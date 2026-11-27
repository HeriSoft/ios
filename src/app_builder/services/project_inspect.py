"""Đọc thông tin project thật từ đĩa: routes Expo Router, dependencies, assets, tìm kiếm file."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

from app_builder.core.workspace import IGNORED_DIRS

ROUTE_EXTS = (".tsx", ".ts", ".jsx", ".js")
TEXT_EXTS = {".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".css", ".txt", ".py", ".gradle", ".xml", ".yml", ".yaml"}


@dataclass
class RouteInfo:
    route: str
    file: str  # tương đối
    kind: str  # screen | layout | special


def routes_from_app_dir(project: Path | str) -> list[RouteInfo]:
    app = Path(project) / "app"
    if not app.is_dir():
        return []
    out: list[RouteInfo] = []
    for f in sorted(app.rglob("*")):
        if not f.is_file() or f.suffix not in ROUTE_EXTS:
            continue
        rel = f.relative_to(app).with_suffix("")
        parts = list(rel.parts)
        name = parts[-1]
        file_rel = f.relative_to(project).as_posix()
        if name == "_layout":
            kind = "layout"
        elif name.startswith("+"):
            kind = "special"
        else:
            kind = "screen"
        segs = [p for p in parts if not (p.startswith("(") and p.endswith(")"))]
        if segs and segs[-1] in ("index", "_layout"):
            segs = segs[:-1]
        route = "/" + "/".join(segs)
        out.append(RouteInfo(route=route, file=file_rel, kind=kind))
    order = {"screen": 0, "layout": 1, "special": 2}
    return sorted(out, key=lambda r: (order[r.kind], r.route))


def read_dependencies(project: Path | str) -> dict:
    project = Path(project)
    pkg = project / "package.json"
    result = {"dependencies": {}, "devDependencies": {}, "installed": (project / "node_modules").is_dir(),
              "lockfile": (project / "package-lock.json").is_file(), "error": None}
    if not pkg.is_file():
        result["error"] = "Không có package.json"
        return result
    try:
        data = json.loads(pkg.read_text("utf-8"))
        result["dependencies"] = data.get("dependencies", {})
        result["devDependencies"] = data.get("devDependencies", {})
    except (OSError, json.JSONDecodeError) as exc:
        result["error"] = f"package.json lỗi: {exc}"
    return result


def installed_version(project: Path | str, name: str) -> str | None:
    p = Path(project) / "node_modules" / Path(*name.split("/")) / "package.json"
    try:
        return json.loads(p.read_text("utf-8")).get("version")
    except (OSError, json.JSONDecodeError):
        return None


def iter_project_files(project: Path | str, max_files: int = 20000):
    root = Path(project)
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".tmp-")]
        for fn in filenames:
            yield Path(dirpath) / fn
            count += 1
            if count >= max_files:
                return


def search_project(project: Path | str, query: str, max_results: int = 200) -> list[tuple[str, int, str]]:
    """Tìm theo tên file và nội dung (không phân biệt hoa thường). Trả (rel_path, line, preview)."""
    q = query.strip()
    if not q:
        return []
    root = Path(project)
    rx = re.compile(re.escape(q), re.IGNORECASE)
    results: list[tuple[str, int, str]] = []
    for f in iter_project_files(root):
        rel = f.relative_to(root).as_posix()
        if rx.search(f.name):
            results.append((rel, 0, ""))
        if f.suffix.lower() in TEXT_EXTS:
            try:
                if f.stat().st_size > 1_000_000:
                    continue
                for i, line in enumerate(f.read_text("utf-8", errors="ignore").splitlines(), 1):
                    if rx.search(line):
                        results.append((rel, i, line.strip()[:160]))
                        if len(results) >= max_results:
                            return results
            except OSError:
                continue
        if len(results) >= max_results:
            break
    return results
