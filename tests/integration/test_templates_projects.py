"""Integration offline: sinh template, quản lý project, đọc routes. Không cần mạng/API key."""
import json
import os
import shutil
import subprocess

import pytest

from app_builder.core.schemas import ProjectSpec
from app_builder.services import project_inspect as pi
from app_builder.services.project_service import ProjectError, ProjectService
from app_builder.services.template_service import CATEGORIES, TemplateError, TemplateService

TS = TemplateService()


def make_spec(template: str, name: str = "Bé Học Vui", **kw) -> ProjectSpec:
    from app_builder.core.workspace import package_id_from, slugify
    return ProjectSpec(name=name, slug=slugify(name), android_package=package_id_from(name),
                       ios_bundle_id=package_id_from(name), template=template, **kw)


def test_templates_listed():
    ids = [t.id for t in TS.list_templates()]
    assert {"todo", "education", "blank"} <= set(ids)
    for c in CATEGORIES:
        assert c["template"] in (None, *ids)


@pytest.mark.parametrize("tid", ["todo", "education", "blank"])
def test_render_template(vn_tmp, tid):
    spec = TS.apply_template_to_spec(make_spec(tid, theme={"style": "pastel"}))
    dest = vn_tmp / tid
    files = TS.render(spec, dest)
    for required in ("package.json", "app.json", "tsconfig.json", ".gitignore", "src/brand.ts", "src/i18n.ts",
                     "src/theme.tsx", "src/components/ui.tsx", "app/_layout.tsx", ".appbuilder/project.json",
                     ".env.example", "README.md"):
        assert required in files, required
        assert (dest / required).is_file()
    pkg = json.loads((dest / "package.json").read_text("utf-8"))
    sdk = TS.sdk()
    assert pkg["main"] == "expo-router/entry"
    for name, ver in {**pkg["dependencies"], **pkg["devDependencies"]}.items():
        assert sdk["versions"][name] == ver
    app = json.loads((dest / "app.json").read_text("utf-8"))["expo"]
    assert app["name"] == "Bé Học Vui"
    assert app["android"]["package"] == spec.android_package
    assert app["android"]["permissions"] == []  # không bật quyền nhạy cảm mặc định
    assert "#E879A6" in (dest / "src/brand.ts").read_text("utf-8")  # màu pastel
    gi = (dest / ".gitignore").read_text("utf-8")
    for pattern in (".env", "*.keystore", "node_modules/", "*.jks"):
        assert pattern in gi
    assert not list(vn_tmp.glob("*.creating"))
    # Mọi khóa t("...") dùng trong code phải có trong i18n.ts
    i18n = (dest / "src/i18n.ts").read_text("utf-8")
    import re
    for f in dest.rglob("*.tsx"):
        for key in re.findall(r"\bt\(\"([A-Za-z]+)\"", f.read_text("utf-8")):
            assert f'"{key}"' in i18n, f"{f.name}: thiếu khóa {key}"


def test_render_refuses_non_empty(vn_tmp):
    dest = vn_tmp / "x"
    dest.mkdir()
    (dest / "keep.txt").write_text("user data")
    with pytest.raises(TemplateError):
        TS.render(TS.apply_template_to_spec(make_spec("todo")), dest)
    assert (dest / "keep.txt").read_text() == "user data"


def test_name_with_quotes_is_escaped(vn_tmp):
    spec = TS.apply_template_to_spec(make_spec("blank", name='App "Trích" \\ dẫn'))
    TS.render(spec, vn_tmp / "q")
    json.loads((vn_tmp / "q" / "app.json").read_text("utf-8"))
    assert '\\"Trích\\"' in (vn_tmp / "q" / "src/brand.ts").read_text("utf-8")


def test_project_lifecycle(db, vn_tmp, tmp_path):
    ps = ProjectService(db)
    ref = tmp_path / "ghi chú.md"
    ref.write_text("tham chiếu", "utf-8")
    rec = ps.create_project(make_spec("todo", name="Việc Nhà"), vn_tmp, [ref])
    assert rec.exists and not rec.trusted and rec.template == "todo"
    spec = ps.load_spec(rec.path)
    assert spec.references == [".appbuilder/references/ghi chú.md"]
    assert len(spec.screens) == 3 and spec.acceptance_tests
    assert [p.id for p in ps.list_projects("việc")] == [rec.id]
    assert ps.list_projects("không-có") == []
    with pytest.raises(ProjectError):
        ps.create_project(make_spec("todo", name="Việc Nhà"), vn_tmp)

    # duplicate bỏ qua node_modules
    (vn_tmp / rec.slug / "node_modules" / "x").mkdir(parents=True)
    dup = ps.duplicate(rec.id, "Việc Nhà 2")
    assert dup.id != rec.id and not (vn_tmp / dup.slug / "node_modules").exists()
    assert json.loads((vn_tmp / dup.slug / "app.json").read_text("utf-8"))["expo"]["name"] == "Việc Nhà 2"

    # gỡ khỏi danh sách KHÔNG xóa file
    ps.remove_from_list(rec.id)
    assert (vn_tmp / rec.slug / "package.json").exists()
    assert rec.id not in [p.id for p in ps.list_projects()]

    # import lại -> chưa tin cậy, giữ spec
    imp = ps.import_folder(vn_tmp / rec.slug)
    assert not imp.trusted and imp.name == "Việc Nhà"
    assert ps.import_folder(vn_tmp / rec.slug).id == imp.id
    ps.set_trusted(imp.id, True)
    assert ps.get(imp.id).trusted
    kinds = [r["kind"] for r in db.query("SELECT kind FROM audit_events")]
    assert "project.created" in kinds and "project.removed_from_list" in kinds


def test_import_plain_folder(db, vn_tmp):
    (vn_tmp / "plain").mkdir()
    (vn_tmp / "plain" / "package.json").write_text('{"name": "my-rn-app"}')
    rec = ProjectService(db).import_folder(vn_tmp / "plain")
    assert rec.name == "my-rn-app" and rec.template == "imported"


def test_routes_and_deps(vn_tmp):
    spec = TS.apply_template_to_spec(make_spec("education"))
    TS.render(spec, vn_tmp / "edu")
    routes = {r.route: r.kind for r in pi.routes_from_app_dir(vn_tmp / "edu") if r.kind == "screen"}
    assert set(routes) == {"/", "/gallery", "/schedule", "/activities", "/lesson/[id]", "/settings"}
    d = pi.read_dependencies(vn_tmp / "edu")
    assert "expo" in d["dependencies"] and not d["installed"]
    res = pi.search_project(vn_tmp / "edu", "ProgressProvider")
    assert any(r[0] == "app/_layout.tsx" for r in res)


@pytest.mark.slow
@pytest.mark.skipif(os.environ.get("APPBUILDER_RUN_SLOW") != "1", reason="opt-in: APPBUILDER_RUN_SLOW=1 (cần mạng, ~2 phút)")
def test_npm_install_and_typecheck_all_templates(tmp_path):
    """Integration thật: npm install + tsc --noEmit cho cả 3 template (dùng chung node_modules qua junction)."""
    from app_builder.core import process_manager as pm
    base = tmp_path / "Dự án có dấu"
    for tid in ("todo", "education", "blank"):
        TS.render(TS.apply_template_to_spec(make_spec(tid, name=f"Thử {tid}")), base / tid)
    r = pm.run(["npm", "install", "--no-audit", "--no-fund"], cwd=base / "todo", timeout=900)
    assert r.ok, r.stderr[-2000:]
    tsc = base / "todo" / "node_modules" / "typescript" / "bin" / "tsc"
    for tid in ("todo", "education", "blank"):
        if tid != "todo":
            subprocess.run(["cmd", "/c", "mklink", "/J", str(base / tid / "node_modules"),
                            str(base / "todo" / "node_modules")], check=True, capture_output=True)
        r = pm.run([pm.which("node"), str(tsc), "--noEmit"], cwd=base / tid, timeout=300)
        assert r.ok, f"{tid}: {r.stdout[-3000:]}"
    shutil.rmtree(base, ignore_errors=True)
