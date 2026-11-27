import os
import subprocess
import sys

import pytest

from app_builder.core.workspace import (
    UnsafePathError, atomic_write_text, is_valid_android_package, is_valid_ios_bundle_id, package_id_from,
    resolve_inside, sha256_file, slugify, validate_relative_path,
)


@pytest.mark.parametrize("bad", [
    "../x", "a/../../x", "..\\x", "a\\..\\..\\x", "/etc/passwd", "\\x", "C:\\Windows\\x", "C:x", "D:/x",
    "\\\\server\\share\\x", "//server/share/x", "file.txt:stream", "CON", "nul.txt", "a/COM1.js", "a/LPT9",
    "bad?.ts", "a/b*.ts", "trail. ", "x\x00y", "", "   ", ".", "./",
])
def test_rejects_unsafe_paths(tmp_path, bad):
    with pytest.raises(UnsafePathError):
        resolve_inside(tmp_path, bad)


@pytest.mark.parametrize("good", ["app/index.tsx", "src\\components\\ui.tsx", "./a/b.json", "a//b.ts", "Thư mục/tệp có dấu.ts"])
def test_accepts_safe_paths(tmp_path, good):
    p = resolve_inside(tmp_path, good)
    assert str(p).startswith(os.path.realpath(tmp_path))


def test_symlink_escape_blocked(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "root"
    root.mkdir()
    link = root / "link"
    try:
        os.symlink(outside, link, target_is_directory=True)
    except OSError:
        pytest.skip("Không có quyền tạo symlink")
    with pytest.raises(UnsafePathError):
        resolve_inside(root, "link/evil.txt")


@pytest.mark.skipif(sys.platform != "win32", reason="Junction chỉ có trên Windows")
def test_junction_escape_blocked(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "root"
    root.mkdir()
    r = subprocess.run(["cmd", "/c", "mklink", "/J", str(root / "j"), str(outside)], capture_output=True)
    if r.returncode != 0:
        pytest.skip("Không tạo được junction")
    with pytest.raises(UnsafePathError):
        resolve_inside(root, "j/evil.txt")


def test_validate_normalizes():
    assert str(validate_relative_path("a\\b/./c.ts")) == "a/b/c.ts"


def test_atomic_write_and_hash(vn_tmp):
    f = vn_tmp / "sub" / "tệp.txt"
    atomic_write_text(f, "xin chào")
    assert f.read_text("utf-8") == "xin chào"
    h1 = sha256_file(f)
    atomic_write_text(f, "khác")
    assert sha256_file(f) != h1
    assert not [p for p in f.parent.iterdir() if p.name.startswith(".tmp-")]
    assert sha256_file(vn_tmp / "missing") is None


def test_slugify_vietnamese():
    assert slugify("Bé Học Vui") == "be-hoc-vui"
    assert slugify("Đường Đi") == "duong-di"
    assert slugify("!!!") == "my-app"


def test_package_ids():
    pkg = package_id_from("Bé Học Vui")
    assert pkg == "com.example.behocvui"
    assert is_valid_android_package(pkg)
    assert package_id_from("123 app").startswith("com.example.app")
    assert not is_valid_android_package("com.1bad.x")
    assert not is_valid_android_package("nodot")
    assert is_valid_ios_bundle_id("com.my-company.app")
    assert not is_valid_ios_bundle_id("com..app")
