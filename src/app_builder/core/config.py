"""Đường dẫn dữ liệu và cấu hình ứng dụng (JSON + Pydantic). Không lưu secret ở đây."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from app_builder import APP_ID


def _known_documents_dir() -> Path:
    """Thư mục Documents thật trên Windows (hỗ trợ OneDrive redirect)."""
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes
            import uuid

            class GUID(ctypes.Structure):
                _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD),
                            ("Data3", wintypes.WORD), ("Data4", ctypes.c_ubyte * 8)]

            u = uuid.UUID("{FDD39AD0-238F-46AF-ADB4-6C85480369C7}")  # FOLDERID_Documents
            guid = GUID(u.fields[0], u.fields[1], u.fields[2],
                        (ctypes.c_ubyte * 8).from_buffer_copy(u.bytes[8:]))
            ptr = ctypes.c_wchar_p()
            if ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(guid), 0, None, ctypes.byref(ptr)) == 0:
                path = Path(ptr.value)
                ctypes.windll.ole32.CoTaskMemFree(ptr)
                return path
        except Exception:  # pragma: no cover - fallback
            pass
    return Path.home() / "Documents"


def data_dir() -> Path:
    """%LOCALAPPDATA%/AppBuilderAI (ghi đè bằng APPBUILDER_DATA_DIR cho test)."""
    override = os.environ.get("APPBUILDER_DATA_DIR")
    if override:
        p = Path(override)
    else:
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        p = Path(base) / APP_ID
    p.mkdir(parents=True, exist_ok=True)
    return p


def logs_dir() -> Path:
    p = data_dir() / "logs"
    p.mkdir(parents=True, exist_ok=True)
    return p


def default_workspace_dir() -> Path:
    override = os.environ.get("APPBUILDER_WORKSPACE_DIR")
    if override:
        return Path(override)
    return _known_documents_dir() / APP_ID / "Projects"


def resources_dir() -> Path:
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / "app_builder" / "resources"
    return Path(__file__).resolve().parent.parent / "resources"


class AppSettings(BaseModel):
    language: Literal["vi", "en"] = "vi"
    theme: Literal["dark", "light"] = "dark"
    workspace_dir: str = Field(default_factory=lambda: str(default_workspace_dir()))
    # Đường dẫn công cụ do người dùng chọn (ghi đè PATH): node, git, gh, java_home, android_sdk, claude, eas
    tool_paths: dict[str, str] = Field(default_factory=dict)
    keep_message_history: bool = False
    telemetry: bool = False  # luôn mặc định tắt
    window_geometry: str = ""
    window_state: str = ""


def settings_path() -> Path:
    return data_dir() / "settings.json"


def load_settings() -> AppSettings:
    path = settings_path()
    if path.exists():
        try:
            return AppSettings.model_validate(json.loads(path.read_text("utf-8")))
        except (ValidationError, json.JSONDecodeError, OSError):
            # File hỏng: giữ bản sao rồi dùng mặc định
            try:
                path.replace(path.with_suffix(".corrupt.json"))
            except OSError:
                pass
    return AppSettings()


def save_settings(settings: AppSettings) -> None:
    from app_builder.core.workspace import atomic_write_text

    atomic_write_text(settings_path(), settings.model_dump_json(indent=2))
