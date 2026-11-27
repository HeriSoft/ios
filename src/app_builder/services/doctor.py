"""Doctor: dò công cụ cần thiết trên Windows, phiên bản, đường dẫn và hướng dẫn cài đặt.

Không cài gì tự động. Thiếu công cụ -> trạng thái 'missing' + hướng dẫn, các tính năng phụ thuộc
hiển thị BLOCKED.
"""
from __future__ import annotations

import ctypes
import json
import os
import platform
import re
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path

from app_builder.core import process_manager as pm
from app_builder.core.config import resources_dir

OK, WARN, MISSING, INFO = "ok", "warn", "missing", "info"


@dataclass
class ToolCheck:
    key: str
    name: str
    status: str
    version: str = ""
    path: str = ""
    detail: str = ""
    hint: str = ""
    needed_for: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _first_line(text: str) -> str:
    return (text or "").strip().splitlines()[0].strip() if (text or "").strip() else ""


def _version_tuple(text: str) -> tuple[int, ...]:
    m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", text or "")
    return tuple(int(x) for x in m.groups() if x is not None) if m else ()


def expo_sdk_info() -> dict:
    try:
        return json.loads((resources_dir() / "templates" / "_sdk.json").read_text("utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def node_satisfies(version: tuple[int, ...], engines: str) -> bool:
    """Kiểm tra semver range dạng '^22.13.0 || ^24.3.0 || >=27.0.0' (đủ dùng cho engines của Expo)."""
    if not version:
        return False
    v = (version + (0, 0, 0))[:3]
    for alt in engines.split("||"):
        alt = alt.strip()
        m = re.match(r"(\^|>=|~)?\s*(\d+)\.(\d+)\.(\d+)", alt)
        if not m:
            continue
        op, req = m.group(1) or "=", tuple(int(x) for x in m.group(2, 3, 4))
        if op == "^" and v[0] == req[0] and v >= req:
            return True
        if op == ">=" and v >= req:
            return True
        if op == "~" and v[:2] == req[:2] and v >= req:
            return True
        if op == "=" and v == req:
            return True
    return False


def _check_python() -> ToolCheck:
    ver = platform.python_version()
    ok = sys.version_info >= (3, 11)
    return ToolCheck("python", "Python", OK if ok else MISSING, ver, sys.executable,
                     hint="" if ok else "Cài Python 3.11+ từ python.org", needed_for=["IDE"])


def _check_qt() -> list[ToolCheck]:
    out = []
    try:
        import PySide6
        out.append(ToolCheck("pyside6", "PySide6 (Qt)", OK, PySide6.__version__, needed_for=["IDE"]))
    except ImportError:
        out.append(ToolCheck("pyside6", "PySide6 (Qt)", MISSING, hint="pip install PySide6", needed_for=["IDE"]))
        return out
    try:
        import PySide6.QtWebEngineWidgets  # noqa: F401
        out.append(ToolCheck("webengine", "Qt WebEngine", OK, PySide6.__version__,
                             detail="Preview web nhúng trong IDE", needed_for=["Preview"]))
    except ImportError:
        out.append(ToolCheck("webengine", "Qt WebEngine", WARN,
                             detail="Không có — preview sẽ mở bằng trình duyệt ngoài",
                             hint="pip install PySide6-Addons", needed_for=["Preview"]))
    return out


def _check_node(tool_paths: dict[str, str]) -> list[ToolCheck]:
    node = pm.which("node", tool_paths.get("node"))
    if not node:
        return [ToolCheck("node", "Node.js", MISSING, hint="Cài Node.js LTS từ https://nodejs.org (bản LTS chẵn: 22 hoặc 24)",
                          needed_for=["Preview", "Build", "Typecheck"]),
                ToolCheck("npm", "npm", MISSING, hint="Đi kèm Node.js", needed_for=["Preview", "Build"])]
    r = pm.run([node, "--version"], timeout=15)
    ver = _first_line(r.stdout)
    vt = _version_tuple(ver)
    sdk = expo_sdk_info()
    engines = sdk.get("node_engines", "")
    status, detail = OK, ""
    if vt and vt[0] % 2 == 1:
        status, detail = WARN, "Phiên bản lẻ (Current, không phải LTS)."
    if engines and not node_satisfies(vt, engines):
        status = WARN
        detail = (detail + f" Expo SDK {sdk.get('expo_sdk', '?')} yêu cầu Node {engines}.").strip()
    checks = [ToolCheck("node", "Node.js", status, ver, node, detail,
                        hint="Khuyến nghị cài Node.js LTS (22.x/24.x) để tương thích Expo" if status != OK else "",
                        needed_for=["Preview", "Build", "Typecheck"])]
    npm_script = pm.node_cli_script("npm", node)
    if npm_script:
        r2 = pm.run(["npm", "--version"], timeout=30, node_path=node)
        checks.append(ToolCheck("npm", "npm", OK if r2.ok else WARN, _first_line(r2.stdout), npm_script,
                                detail=r2.error or "", needed_for=["Preview", "Build"]))
    else:
        checks.append(ToolCheck("npm", "npm", MISSING, hint="Cài lại Node.js (kèm npm)", needed_for=["Preview", "Build"]))
    return checks


def _simple(key: str, name: str, argv: list[str], tool_paths: dict[str, str], hint: str,
            needed_for: list[str], missing_status: str = MISSING) -> ToolCheck:
    exe = pm.which(argv[0], tool_paths.get(key))
    if not exe:
        return ToolCheck(key, name, missing_status, hint=hint, needed_for=needed_for)
    r = pm.run([exe, *argv[1:]], timeout=20)
    text = r.stdout or r.stderr
    if not r.ok and not text:
        return ToolCheck(key, name, WARN, path=exe, detail=r.error or "Không đọc được phiên bản", hint=hint,
                         needed_for=needed_for)
    return ToolCheck(key, name, OK, _first_line(text), exe, needed_for=needed_for)


def _check_gh(tool_paths: dict[str, str]) -> ToolCheck:
    c = _simple("gh", "GitHub CLI", ["gh", "--version"], tool_paths,
                "Cài GitHub CLI: https://cli.github.com rồi chạy `gh auth login`", ["GitHub"], WARN)
    if c.status == OK:
        r = pm.run([c.path, "auth", "status", "--hostname", "github.com"], timeout=20,
                   env=pm.minimal_env({"GH_PROMPT_DISABLED": "1"}))
        c.detail = "Đã đăng nhập github.com" if r.returncode == 0 else "Chưa đăng nhập (chạy `gh auth login`)"
        if r.returncode != 0:
            c.status = WARN
    return c


def find_java_home(tool_paths: dict[str, str]) -> str | None:
    cands = [tool_paths.get("java_home"), os.environ.get("JAVA_HOME")]
    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    for vendor in ("Android\\Android Studio\\jbr", "Android\\Android Studio\\jre"):
        cands.append(str(Path(pf) / vendor))
    for root in ("Java", "Eclipse Adoptium", "Microsoft", "Zulu"):
        d = Path(pf) / root
        if d.is_dir():
            cands.extend(str(p) for p in sorted(d.iterdir(), reverse=True) if p.is_dir())
    for c in cands:
        if c and (Path(c) / "bin" / "java.exe").is_file():
            return c
    return None


def _check_java(tool_paths: dict[str, str]) -> ToolCheck:
    home = find_java_home(tool_paths)
    java = str(Path(home) / "bin" / "java.exe") if home else pm.which("java")
    hint = "Cài JDK 17 (vd: Microsoft Build of OpenJDK hoặc JBR đi kèm Android Studio) và đặt JAVA_HOME"
    if not java:
        return ToolCheck("java", "JDK (Java)", MISSING, hint=hint, needed_for=["Android build"])
    r = pm.run([java, "-version"], timeout=20)
    ver = _first_line(r.stderr or r.stdout)
    vt = _version_tuple(ver)
    status = OK if vt and vt[0] >= 17 else WARN
    return ToolCheck("java", "JDK (Java)", status, ver, java,
                     detail="" if status == OK else "Gradle/Android cần JDK 17+", hint="" if status == OK else hint,
                     needed_for=["Android build"])


def find_android_sdk(tool_paths: dict[str, str]) -> str | None:
    cands = [tool_paths.get("android_sdk"), os.environ.get("ANDROID_HOME"), os.environ.get("ANDROID_SDK_ROOT"),
             str(Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk")]
    for c in cands:
        if c and Path(c).is_dir() and ((Path(c) / "platform-tools").is_dir() or (Path(c) / "platforms").is_dir()):
            return c
    return None


def _check_android(tool_paths: dict[str, str]) -> list[ToolCheck]:
    sdk = find_android_sdk(tool_paths)
    hint = ("Cài Android Studio (kèm Android SDK, Platform-Tools, Build-Tools) — "
            "https://developer.android.com/studio; đặt ANDROID_HOME=%LOCALAPPDATA%\\Android\\Sdk")
    if not sdk:
        return [ToolCheck("android_sdk", "Android SDK", MISSING, hint=hint, needed_for=["Android build", "Emulator"]),
                ToolCheck("adb", "adb", MISSING, hint="Đi kèm Android SDK Platform-Tools", needed_for=["Cài APK", "Thiết bị USB"])]
    platforms = sorted(p.name for p in (Path(sdk) / "platforms").glob("android-*")) if (Path(sdk) / "platforms").is_dir() else []
    out = [ToolCheck("android_sdk", "Android SDK", OK, ", ".join(platforms[-2:]) or "?", sdk, needed_for=["Android build"])]
    adb = Path(sdk) / "platform-tools" / "adb.exe"
    adb_path = str(adb) if adb.is_file() else pm.which("adb")
    if adb_path:
        r = pm.run([adb_path, "version"], timeout=20)
        out.append(ToolCheck("adb", "adb", OK if r.ok else WARN, _first_line(r.stdout), adb_path,
                             needed_for=["Cài APK", "Thiết bị USB"]))
    else:
        out.append(ToolCheck("adb", "adb", MISSING, hint="Cài 'Android SDK Platform-Tools' trong SDK Manager",
                             needed_for=["Cài APK"]))
    return out


def _check_system() -> list[ToolCheck]:
    out = [ToolCheck("os", "Windows", INFO, f"{platform.system()} {platform.release()} ({platform.version()})",
                     detail=platform.machine())]
    if sys.platform == "win32":
        class MEM(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        m = MEM()
        m.dwLength = ctypes.sizeof(MEM)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
            gb = m.ullTotalPhys / 1024 ** 3
            out.append(ToolCheck("ram", "RAM", OK if gb >= 15 else WARN, f"{gb:.1f} GB",
                                 detail=f"Còn trống {m.ullAvailPhys / 1024 ** 3:.1f} GB",
                                 hint="" if gb >= 15 else "Khuyến nghị 16 GB; tránh chạy emulator + nhiều dev server"))
    return out


def check_disk(path: str) -> ToolCheck:
    try:
        p = Path(path)
        while not p.exists() and p.parent != p:
            p = p.parent
        free = shutil.disk_usage(p).free / 1024 ** 3
        return ToolCheck("disk", "Dung lượng trống", OK if free >= 10 else WARN, f"{free:.0f} GB", str(p),
                         hint="" if free >= 10 else "Cần ≥10 GB cho node_modules + Gradle cache")
    except OSError as exc:
        return ToolCheck("disk", "Dung lượng trống", WARN, detail=str(exc))


def _check_keyring() -> ToolCheck:
    from app_builder.core.secret_store import SecretStore
    s = SecretStore()
    if s.persistent:
        return ToolCheck("keyring", "Kho secret (Credential Manager)", OK, s.backend_name)
    return ToolCheck("keyring", "Kho secret", WARN, "memory-only",
                     detail="Key chỉ giữ trong bộ nhớ, mất khi thoát", hint="pip install keyring")


def run_doctor(tool_paths: dict[str, str] | None = None, workspace_dir: str | None = None) -> list[ToolCheck]:
    tp = tool_paths or {}
    tasks = {
        "node": lambda: _check_node(tp),
        "git": lambda: [_simple("git", "Git", ["git", "--version"], tp,
                                "Cài Git for Windows: https://git-scm.com/download/win", ["GitHub", "Checkpoint"])],
        "gh": lambda: [_check_gh(tp)],
        "java": lambda: [_check_java(tp)],
        "android": lambda: _check_android(tp),
        "claude": lambda: [_simple("claude", "Claude Code CLI", ["claude", "--version"], tp,
                                   "Tùy chọn: cài Claude Code theo https://code.claude.com/docs rồi đăng nhập bằng flow chính thức",
                                   ["Claude Code"], WARN)],
        "eas": lambda: [_simple("eas", "EAS CLI", ["eas", "--version"], tp,
                                "Tùy chọn: npm install -g eas-cli (cho build cloud Android/iOS)", ["EAS build"], WARN)],
    }
    results: list[ToolCheck] = [_check_python(), *_check_qt()]
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {k: ex.submit(fn) for k, fn in tasks.items()}
        for k in tasks:
            try:
                results.extend(futs[k].result(timeout=90))
            except Exception as exc:  # pragma: no cover
                results.append(ToolCheck(k, k, WARN, detail=f"Lỗi khi kiểm tra: {exc}"))
    results.append(_check_keyring())
    results.extend(_check_system())
    if workspace_dir:
        results.append(check_disk(workspace_dir))
    return results


def blocked_features(checks: list[ToolCheck]) -> dict[str, list[str]]:
    """feature -> danh sách công cụ còn thiếu."""
    out: dict[str, list[str]] = {}
    for c in checks:
        if c.status == MISSING:
            for f in c.needed_for:
                out.setdefault(f, []).append(c.name)
    return out


def format_report(checks: list[ToolCheck]) -> str:
    icon = {OK: "[OK]  ", WARN: "[WARN]", MISSING: "[MISS]", INFO: "[INFO]"}
    lines = []
    for c in checks:
        line = f"{icon.get(c.status, '[?]  ')} {c.name:<32} {c.version}"
        if c.path:
            line += f"\n         {c.path}"
        if c.detail:
            line += f"\n         {c.detail}"
        if c.hint and c.status != OK:
            line += f"\n         → {c.hint}"
        lines.append(line)
    blocked = blocked_features(checks)
    if blocked:
        lines.append("")
        lines.append("BLOCKED:")
        for f, tools in blocked.items():
            lines.append(f"  - {f}: thiếu {', '.join(tools)}")
    return "\n".join(lines)
