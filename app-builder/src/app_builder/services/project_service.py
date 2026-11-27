"""Quản lý project: tạo từ template, danh sách gần đây, import folder, duplicate, gỡ khỏi danh sách."""
from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from app_builder.core.database import Database
from app_builder.core.schemas import ProjectSpec, utcnow_iso
from app_builder.core.workspace import IGNORED_DIRS, atomic_write_text, package_id_from, slugify
from app_builder.services.template_service import TemplateService

log = logging.getLogger(__name__)
SPEC_REL = ".appbuilder/project.json"


@dataclass
class ProjectRecord:
    id: int
    name: str
    slug: str
    path: str
    description: str
    template: str
    categories: list[str]
    platforms: list[str]
    trusted: bool
    created_at: str
    updated_at: str
    last_opened_at: str | None
    last_build_status: str | None
    last_build_at: str | None

    @property
    def exists(self) -> bool:
        return Path(self.path).is_dir()


class ProjectError(RuntimeError):
    pass


class ProjectService:
    def __init__(self, db: Database, templates: TemplateService | None = None) -> None:
        self.db = db
        self.templates = templates or TemplateService()

    # ---- queries -----------------------------------------------------------
    def _row(self, r) -> ProjectRecord:
        return ProjectRecord(
            id=r["id"], name=r["name"], slug=r["slug"], path=r["path"], description=r["description"],
            template=r["template"], categories=json.loads(r["categories"]), platforms=json.loads(r["platforms"]),
            trusted=bool(r["trusted"]), created_at=r["created_at"], updated_at=r["updated_at"],
            last_opened_at=r["last_opened_at"], last_build_status=r["last_build_status"], last_build_at=r["last_build_at"],
        )

    def list_projects(self, search: str = "") -> list[ProjectRecord]:
        rows = self.db.query(
            "SELECT * FROM projects ORDER BY COALESCE(last_opened_at, created_at) DESC"
        )
        items = [self._row(r) for r in rows]
        if search:
            s = search.casefold()
            items = [p for p in items if s in p.name.casefold() or s in p.description.casefold() or s in p.path.casefold()]
        return items

    def get(self, project_id: int) -> ProjectRecord:
        r = self.db.query_one("SELECT * FROM projects WHERE id=?", (project_id,))
        if not r:
            raise ProjectError("Project không tồn tại")
        return self._row(r)

    def find_by_path(self, path: Path | str) -> ProjectRecord | None:
        r = self.db.query_one("SELECT * FROM projects WHERE path=?", (str(Path(path).resolve()),))
        return self._row(r) if r else None

    # ---- spec --------------------------------------------------------------
    @staticmethod
    def load_spec(project_path: Path | str) -> ProjectSpec | None:
        p = Path(project_path) / SPEC_REL
        if not p.is_file():
            return None
        try:
            return ProjectSpec.model_validate_json(p.read_text("utf-8"))
        except Exception as exc:
            log.warning("Spec lỗi tại %s: %s", p, exc)
            return None

    @staticmethod
    def save_spec(project_path: Path | str, spec: ProjectSpec) -> None:
        atomic_write_text(Path(project_path) / SPEC_REL, spec.model_dump_json(indent=2))

    # ---- mutations ---------------------------------------------------------
    def _insert(self, spec: ProjectSpec, path: Path, trusted: bool) -> ProjectRecord:
        now = utcnow_iso()
        pid = self.db.execute(
            "INSERT INTO projects(name, slug, path, description, template, categories, platforms, trusted,"
            " created_at, updated_at, last_opened_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (spec.name, spec.slug, str(path.resolve()), spec.description, spec.template,
             json.dumps(spec.categories), json.dumps(spec.platforms), int(trusted), now, now, now),
        )
        return self.get(pid)

    def create_project(self, spec: ProjectSpec, parent_dir: Path | str, references: list[Path] | None = None) -> ProjectRecord:
        parent = Path(parent_dir)
        dest = parent / spec.slug
        if self.find_by_path(dest):
            raise ProjectError(f"Project đã có trong danh sách: {dest}")
        if dest.exists() and any(dest.iterdir()):
            raise ProjectError(f"Thư mục đã tồn tại và không rỗng: {dest}")
        self.templates.apply_template_to_spec(spec)
        # Sao chép tài liệu/ảnh tham chiếu vào project (không gửi đi đâu)
        copied: list[str] = []
        self.templates.render(spec, dest)
        if references:
            ref_dir = dest / ".appbuilder" / "references"
            ref_dir.mkdir(parents=True, exist_ok=True)
            for ref in references:
                ref = Path(ref)
                if ref.is_file():
                    target = ref_dir / ref.name
                    shutil.copyfile(ref, target)
                    copied.append(f".appbuilder/references/{ref.name}")
            spec.references = copied
            self.save_spec(dest, spec)
        # Kể cả project tạo từ template, npm install vẫn chạy script của dependency -> yêu cầu trust ở lần đầu
        rec = self._insert(spec, dest, trusted=False)
        self.db.audit("project.created", rec.id, template=spec.template, path=str(dest))
        return rec

    def import_folder(self, folder: Path | str) -> ProjectRecord:
        folder = Path(folder).resolve()
        if not folder.is_dir():
            raise ProjectError("Thư mục không tồn tại")
        existing = self.find_by_path(folder)
        if existing:
            return existing
        spec = self.load_spec(folder)
        if spec is None:
            name = folder.name
            pkg_json = folder / "package.json"
            app_json = folder / "app.json"
            desc = ""
            try:
                if app_json.is_file():
                    expo = json.loads(app_json.read_text("utf-8")).get("expo", {})
                    name = expo.get("name") or name
                elif pkg_json.is_file():
                    name = json.loads(pkg_json.read_text("utf-8")).get("name") or name
            except (OSError, json.JSONDecodeError):
                pass
            pkg = package_id_from(name)
            spec = ProjectSpec(name=name[:60], slug=slugify(name), description=desc, android_package=pkg,
                               ios_bundle_id=pkg, template="imported")
        # Project import: CHƯA trusted — phải xác nhận trước lần Run/Install đầu
        rec = self._insert(spec, folder, trusted=False)
        self.db.audit("project.imported", rec.id, path=str(folder))
        return rec

    def duplicate(self, project_id: int, new_name: str) -> ProjectRecord:
        src = self.get(project_id)
        src_path = Path(src.path)
        if not src_path.is_dir():
            raise ProjectError("Thư mục nguồn không còn tồn tại")
        slug = slugify(new_name)
        dest = src_path.parent / slug
        n = 2
        while dest.exists():
            dest = src_path.parent / f"{slug}-{n}"
            n += 1
        shutil.copytree(src_path, dest, ignore=shutil.ignore_patterns(*IGNORED_DIRS))
        spec = self.load_spec(dest)
        if spec:
            spec.name = new_name
            spec.slug = dest.name
            spec.created_at = utcnow_iso()
            self.save_spec(dest, spec)
            self._rename_in_app_json(dest, new_name, dest.name)
        else:
            pkg = package_id_from(new_name)
            spec = ProjectSpec(name=new_name, slug=dest.name, android_package=pkg, ios_bundle_id=pkg, template=src.template)
        rec = self._insert(spec, dest, trusted=src.trusted)
        self.db.audit("project.duplicated", rec.id, source=src.id)
        return rec

    @staticmethod
    def _rename_in_app_json(folder: Path, name: str, slug: str) -> None:
        app_json = folder / "app.json"
        try:
            cfg = json.loads(app_json.read_text("utf-8"))
            cfg.setdefault("expo", {})["name"] = name
            cfg["expo"]["slug"] = slug
            atomic_write_text(app_json, json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")
        except (OSError, json.JSONDecodeError):
            pass

    def remove_from_list(self, project_id: int) -> None:
        """Chỉ gỡ khỏi danh sách — KHÔNG xóa file trên đĩa."""
        rec = self.get(project_id)
        self.db.execute("DELETE FROM projects WHERE id=?", (project_id,))
        self.db.audit("project.removed_from_list", None, path=rec.path)

    def mark_opened(self, project_id: int) -> None:
        self.db.execute("UPDATE projects SET last_opened_at=? WHERE id=?", (utcnow_iso(), project_id))

    def set_trusted(self, project_id: int, trusted: bool) -> None:
        self.db.execute("UPDATE projects SET trusted=?, updated_at=? WHERE id=?", (int(trusted), utcnow_iso(), project_id))
        self.db.audit("project.trust_changed", project_id, trusted=trusted)
