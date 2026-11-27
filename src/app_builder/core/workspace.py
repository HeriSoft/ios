"""An toàn đường dẫn trong workspace + ghi file nguyên tử.

Path check KHÔNG thay thế sandbox của hệ điều hành; nó chỉ chặn AI/patch ghi ra ngoài
workspace đã chọn (path traversal, ổ đĩa khác, UNC, symlink/junction, ADS, tên thiết bị).
"""
from __future__ import annotations

import hashlib
import os
import re
import tempfile
import unicodedata
from pathlib import Path, PurePosixPath, PureWindowsPath

WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

# Thư mục không đưa vào context/explorer/export
IGNORED_DIRS = {
    "node_modules", ".git", ".expo", ".expo-shared", "dist", "web-build", "build",
    ".gradle", ".idea", ".vscode", "__pycache__", ".venv", ".appbuilder-cache",
}


class UnsafePathError(ValueError):
    """Đường dẫn nằm ngoài workspace hoặc không hợp lệ."""


def validate_relative_path(rel: str) -> PurePosixPath:
    """Kiểm tra cú pháp một đường dẫn tương đối (chưa đụng tới filesystem)."""
    if not isinstance(rel, str) or not rel.strip():
        raise UnsafePathError("Đường dẫn rỗng")
    if "\x00" in rel:
        raise UnsafePathError("Đường dẫn chứa ký tự NUL")
    norm = rel.replace("\\", "/")
    if norm.startswith("//") or norm.startswith("/"):
        raise UnsafePathError(f"Không chấp nhận đường dẫn tuyệt đối/UNC: {rel}")
    win = PureWindowsPath(rel)
    if win.drive or win.root or re.match(r"^[A-Za-z]:", rel):
        raise UnsafePathError(f"Không chấp nhận ổ đĩa/đường dẫn tuyệt đối: {rel}")
    parts = [p for p in norm.split("/") if p not in ("", ".")]
    if not parts:
        raise UnsafePathError("Đường dẫn rỗng")
    for part in parts:
        if part == "..":
            raise UnsafePathError(f"Không chấp nhận '..': {rel}")
        if ":" in part:
            raise UnsafePathError(f"Không chấp nhận ':' (ADS/ổ đĩa): {rel}")
        if part.endswith((" ", ".")):
            raise UnsafePathError(f"Tên kết thúc bằng dấu cách/chấm không hợp lệ: {part}")
        stem = part.split(".")[0].upper()
        if stem in WINDOWS_RESERVED:
            raise UnsafePathError(f"Tên thiết bị Windows bị cấm: {part}")
        if any(c in part for c in '<>"|?*') or any(ord(c) < 32 for c in part):
            raise UnsafePathError(f"Ký tự không hợp lệ trong tên: {part}")
    return PurePosixPath(*parts)


def resolve_inside(root: Path | str, rel: str) -> Path:
    """Trả về đường dẫn tuyệt đối nằm chắc chắn trong root (theo realpath, kể cả symlink/junction)."""
    root_real = Path(os.path.realpath(root))
    pure = validate_relative_path(rel)
    candidate = root_real.joinpath(*pure.parts)
    # realpath đi theo symlink/junction của các thành phần đã tồn tại
    real = Path(os.path.realpath(candidate))
    try:
        real.relative_to(root_real)
    except ValueError as exc:
        raise UnsafePathError(f"Đường dẫn thoát khỏi workspace: {rel}") from exc
    # Chặn từng thành phần cha là reparse point trỏ ra ngoài (phòng hờ khi realpath không theo)
    cur = root_real
    for part in pure.parts:
        cur = cur / part
        if cur.exists() and (cur.is_symlink() or _is_junction(cur)):
            target = Path(os.path.realpath(cur))
            try:
                target.relative_to(root_real)
            except ValueError as exc:
                raise UnsafePathError(f"Liên kết trỏ ra ngoài workspace: {rel}") from exc
    return candidate


def _is_junction(p: Path) -> bool:
    try:
        return p.is_junction()  # Python 3.12+
    except AttributeError:
        try:
            import stat
            st = os.lstat(p)
            return bool(getattr(st, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)
        except OSError:
            return False


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str | None:
    try:
        return sha256_bytes(Path(path).read_bytes())
    except FileNotFoundError:
        return None


def atomic_write_bytes(path: Path | str, data: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def atomic_write_text(path: Path | str, text: str) -> None:
    atomic_write_bytes(path, text.encode("utf-8"))


def slugify(name: str, max_len: int = 40) -> str:
    """'Ứng dụng Học Tập' -> 'ung-dung-hoc-tap'."""
    s = name.replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return (s[:max_len].strip("-")) or "my-app"


def package_id_from(name: str, prefix: str = "com.example") -> str:
    seg = slugify(name).replace("-", "")
    if not seg or not seg[0].isalpha():
        seg = "app" + seg
    return f"{prefix}.{seg[:30]}"


PACKAGE_ID_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)+$")
BUNDLE_ID_RE = re.compile(r"^[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+$")


def is_valid_android_package(pkg: str) -> bool:
    return bool(PACKAGE_ID_RE.match(pkg)) and len(pkg) <= 150


def is_valid_ios_bundle_id(bid: str) -> bool:
    return bool(BUNDLE_ID_RE.match(bid)) and len(bid) <= 155
