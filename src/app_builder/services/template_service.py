"""Sinh project Expo từ template: _base + overlay template + file sinh tự động (package.json, app.json, brand.ts, i18n.ts)."""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from app_builder.core.config import resources_dir
from app_builder.core.schemas import ProjectSpec, ScreenSpec
from app_builder.core.workspace import atomic_write_text

TEMPLATES_DIR_NAME = "templates"

# Lĩnh vực trong wizard (mục 3.1). template = mẫu khởi đầu đang có; None -> dùng blank + mô tả
CATEGORIES: list[dict] = [
    {"id": "education", "vi": "Giáo dục / mầm non", "en": "Education / preschool", "hint_vi": "bài học, thư viện hình ảnh, lịch học, hoạt động", "template": "education"},
    {"id": "productivity", "vi": "Năng suất", "en": "Productivity", "hint_vi": "todo, ghi chú, lịch, quản lý dự án", "template": "todo"},
    {"id": "finance", "vi": "Tài chính cá nhân", "en": "Personal finance", "hint_vi": "thu chi, ngân sách, biểu đồ, lưu local", "template": None},
    {"id": "commerce", "vi": "Bán hàng", "en": "Commerce", "hint_vi": "catalog, giỏ hàng, đơn hàng mẫu", "template": None},
    {"id": "health", "vi": "Sức khỏe / fitness", "en": "Health / fitness", "hint_vi": "nhật ký thói quen, vận động (không chẩn đoán)", "template": None},
    {"id": "art_ai", "vi": "Nghệ thuật / AI", "en": "Art / AI", "hint_vi": "gallery, editor, tạo ảnh qua backend an toàn", "template": None},
    {"id": "media", "vi": "Giải trí / media", "en": "Entertainment / media", "hint_vi": "thư viện nội dung, playlist", "template": None},
    {"id": "travel", "vi": "Du lịch / bản đồ", "en": "Travel / maps", "hint_vi": "itinerary, danh sách địa điểm", "template": None},
    {"id": "social", "vi": "Mạng xã hội", "en": "Social", "hint_vi": "profile, feed, chat demo", "template": None},
    {"id": "booking", "vi": "Nhà hàng / đặt lịch", "en": "Restaurant / booking", "hint_vi": "menu, booking demo, lịch hẹn", "template": None},
    {"id": "utility", "vi": "Tiện ích / game casual", "en": "Utility / casual game", "hint_vi": "calculator, quiz, mini-game", "template": None},
    {"id": "custom", "vi": "Custom", "en": "Custom", "hint_vi": "tự mô tả toàn bộ yêu cầu", "template": "blank"},
]

UI_STYLES: dict[str, dict] = {
    "modern": {"vi": "Hiện đại", "en": "Modern", "primary": "#4F46E5", "accent": "#06B6D4", "bg_light": "#F8FAFC", "bg_dark": "#0B1120", "radius": 14},
    "pastel": {"vi": "Pastel dịu nhẹ", "en": "Soft pastel", "primary": "#E879A6", "accent": "#7DD3FC", "bg_light": "#FFF7FB", "bg_dark": "#1A1220", "radius": 20},
    "minimal": {"vi": "Tối giản", "en": "Minimal", "primary": "#111827", "accent": "#6B7280", "bg_light": "#FFFFFF", "bg_dark": "#0A0A0A", "radius": 8},
    "vivid": {"vi": "Rực rỡ", "en": "Vivid", "primary": "#F97316", "accent": "#8B5CF6", "bg_light": "#FFFBF5", "bg_dark": "#140C05", "radius": 16},
    "nature": {"vi": "Thiên nhiên", "en": "Nature", "primary": "#16A34A", "accent": "#CA8A04", "bg_light": "#F6FBF4", "bg_dark": "#07130B", "radius": 14},
}

TEXT_SUFFIXES = {".ts", ".tsx", ".js", ".json", ".md", ".txt", ".css"}


@dataclass
class TemplateInfo:
    id: str
    name: dict
    description: dict
    categories: list[str]
    navigation: str
    screens: list[dict]
    data_model: list[dict]
    acceptance_tests: list[str]
    extra_dependencies: list[str]
    path: Path

    def label(self, lang: str = "vi") -> str:
        return self.name.get(lang) or self.name.get("vi", self.id)

    def desc(self, lang: str = "vi") -> str:
        return self.description.get(lang) or self.description.get("vi", "")


class TemplateError(RuntimeError):
    pass


class TemplateService:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or (resources_dir() / TEMPLATES_DIR_NAME)

    def sdk(self) -> dict:
        return json.loads((self.root / "_sdk.json").read_text("utf-8"))

    def list_templates(self) -> list[TemplateInfo]:
        out = []
        for d in sorted(self.root.iterdir()):
            manifest = d / "template.json"
            if d.is_dir() and not d.name.startswith("_") and manifest.is_file():
                m = json.loads(manifest.read_text("utf-8"))
                out.append(TemplateInfo(
                    id=m["id"], name=m["name"], description=m["description"], categories=m.get("categories", []),
                    navigation=m.get("navigation", "stack"), screens=m.get("screens", []),
                    data_model=m.get("data_model", []), acceptance_tests=m.get("acceptance_tests", []),
                    extra_dependencies=m.get("extra_dependencies", []), path=d,
                ))
        order = {"todo": 0, "education": 1, "blank": 99}
        return sorted(out, key=lambda t: order.get(t.id, 50))

    def get(self, template_id: str) -> TemplateInfo:
        for t in self.list_templates():
            if t.id == template_id:
                return t
        raise TemplateError(f"Không có template '{template_id}'")

    @staticmethod
    def suggest_template(category_ids: list[str]) -> str:
        for c in CATEGORIES:
            if c["id"] in category_ids and c["template"] and c["template"] != "blank":
                return c["template"]
        return "blank"

    # ------------------------------------------------------------------
    def apply_template_to_spec(self, spec: ProjectSpec) -> ProjectSpec:
        info = self.get(spec.template)
        style = UI_STYLES.get(spec.theme.style, UI_STYLES["modern"])
        spec.theme.primary = style["primary"]
        spec.theme.accent = style["accent"]
        spec.theme.background_light = style["bg_light"]
        spec.theme.background_dark = style["bg_dark"]
        spec.theme.radius = style["radius"]
        spec.navigation = info.navigation
        spec.screens = [ScreenSpec(**s) for s in info.screens]
        spec.data_model = info.data_model
        spec.acceptance_tests = list(info.acceptance_tests)
        spec.expo_sdk = self.sdk().get("expo_sdk", "")
        return spec

    def render(self, spec: ProjectSpec, dest: Path) -> list[str]:
        """Tạo project vào dest (phải chưa tồn tại hoặc rỗng). Trả về danh sách file đã tạo (tương đối)."""
        dest = Path(dest)
        if dest.exists() and any(dest.iterdir()):
            raise TemplateError(f"Thư mục đích đã có dữ liệu: {dest}")
        info = self.get(spec.template)
        base = self.root / "_base"
        staging = dest.with_name(dest.name + ".creating")
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir(parents=True)
        created: list[str] = []
        try:
            for src_root in (base, info.path):
                for f in sorted(src_root.rglob("*")):
                    if not f.is_file() or f.name in ("template.json", "strings.json"):
                        continue
                    rel = f.relative_to(src_root).as_posix()
                    if rel == "gitignore.txt":
                        rel = ".gitignore"
                    target = staging / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(f, target)
                    if rel not in created:
                        created.append(rel)
            generated = {
                "package.json": self._package_json(spec, info),
                "app.json": self._app_json(spec),
                "src/brand.ts": self._brand_ts(spec),
                "src/i18n.ts": self._i18n_ts(base, info),
                "README.md": self._readme(spec, info),
                ".env.example": "# Chỉ placeholder. KHÔNG đặt secret của provider AI/GitHub vào app mobile.\n# EXPO_PUBLIC_API_URL=https://your-backend.example.com\n",
                ".appbuilder/project.json": spec.model_dump_json(indent=2),
            }
            for rel, text in generated.items():
                atomic_write_text(staging / rel, text)
                if rel not in created:
                    created.append(rel)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                dest.rmdir()
            staging.replace(dest)
        except BaseException:
            shutil.rmtree(staging, ignore_errors=True)
            raise
        return sorted(created)

    # ------------------------------------------------------------------
    def _package_json(self, spec: ProjectSpec, info: TemplateInfo) -> str:
        sdk = self.sdk()
        versions = sdk["versions"]
        deps = {name: versions[name] for name in sdk["base_dependencies"] + info.extra_dependencies}
        dev = {name: versions[name] for name in sdk["dev_dependencies"]}
        pkg = {
            "name": spec.slug,
            "version": "1.0.0",
            "private": True,
            "main": "expo-router/entry",
            "scripts": {
                "start": "expo start",
                "web": "expo start --web",
                "android": "expo run:android",
                "ios": "expo run:ios",
                "typecheck": "tsc --noEmit",
            },
            "dependencies": dict(sorted(deps.items())),
            "devDependencies": dict(sorted(dev.items())),
        }
        return json.dumps(pkg, indent=2, ensure_ascii=False) + "\n"

    def _app_json(self, spec: ProjectSpec) -> str:
        cfg = {
            "expo": {
                "name": spec.name,
                "slug": spec.slug,
                "version": "1.0.0",
                "scheme": spec.slug.replace("-", ""),
                "orientation": "default",
                "userInterfaceStyle": "automatic",
                "android": {"package": spec.android_package, "versionCode": 1, "permissions": []},
                "ios": {"bundleIdentifier": spec.ios_bundle_id, "buildNumber": "1", "supportsTablet": True},
                "web": {"output": "single", "bundler": "metro"},
                "plugins": ["expo-router"],
            }
        }
        return json.dumps(cfg, indent=2, ensure_ascii=False) + "\n"

    def _brand_ts(self, spec: ProjectSpec) -> str:
        th = spec.theme
        data = {
            "appName": spec.name, "description": spec.description, "language": spec.language,
            "primary": th.primary, "accent": th.accent, "backgroundLight": th.background_light,
            "backgroundDark": th.background_dark, "radius": th.radius, "spacing": th.spacing,
        }
        body = ",\n".join(f"  {k}: {json.dumps(v, ensure_ascii=False)}" for k, v in data.items())
        return (
            "// Sinh bởi App Builder AI — chỉnh màu/bo góc tại đây hoặc qua Theme editor.\n"
            f"export const brand = {{\n{body},\n}} as {{\n"
            "  appName: string; description: string; language: \"vi\" | \"en\";\n"
            "  primary: string; accent: string; backgroundLight: string; backgroundDark: string;\n"
            "  radius: number; spacing: number;\n};\n"
        )

    def _i18n_ts(self, base: Path, info: TemplateInfo) -> str:
        strings: dict[str, dict[str, str]] = {"vi": {}, "en": {}}
        for p in (base / "strings.json", info.path / "strings.json"):
            if p.is_file():
                d = json.loads(p.read_text("utf-8"))
                for lang in strings:
                    strings[lang].update(d.get(lang, {}))
        missing = set(strings["vi"]) ^ set(strings["en"])
        if missing:
            raise TemplateError(f"Thiếu bản dịch cho khóa: {sorted(missing)}")
        return (
            "// Sinh bởi App Builder AI\nimport { brand } from \"./brand\";\n\n"
            f"const strings = {json.dumps(strings, ensure_ascii=False, indent=2)} as const;\n\n"
            "export type StringKey = keyof (typeof strings)[\"vi\"];\n\n"
            "export function t(key: StringKey, vars?: Record<string, string | number>): string {\n"
            "  const table = strings[brand.language] ?? strings.vi;\n"
            "  let s: string = table[key] ?? strings.vi[key] ?? key;\n"
            "  if (vars) for (const [k, v] of Object.entries(vars)) s = s.split(`{${k}}`).join(String(v));\n"
            "  return s;\n}\n"
        )

    def _readme(self, spec: ProjectSpec, info: TemplateInfo) -> str:
        screens = "\n".join(f"- `{s['route']}` — {s['title']}" for s in info.screens)
        return (
            f"# {spec.name}\n\n{spec.description}\n\n"
            f"Tạo bởi App Builder AI từ mẫu **{info.label('vi')}** (Expo SDK {self.sdk().get('expo_sdk')}, Expo Router, TypeScript).\n\n"
            f"## Màn hình\n{screens}\n\n"
            "## Chạy thử\n```powershell\nnpm install\nnpx expo start --web\n```\n\n"
            "## Kiểm tra kiểu\n```powershell\nnpm run typecheck\n```\n\n"
            "Dữ liệu lưu local bằng AsyncStorage. App không chứa API key/secret.\n"
        )
