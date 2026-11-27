"""Chạy tiến trình con an toàn: argv (shell=False), cwd rõ ràng, timeout, env tối giản, kill cả cây.

- `.cmd/.bat` trên Windows: npm/npx được chạy qua `node <npm-cli.js>` để tránh cmd.exe.
  Với .cmd khác, chạy qua cmd.exe /d /c chỉ khi mọi tham số qua được kiểm tra ký tự đặc biệt.
- Windows: mỗi tiến trình được gán vào một Job Object (KILL_ON_JOB_CLOSE) để dừng cả cây;
  fallback `taskkill /T /F`.
"""
from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from app_builder.core.redaction import redact

log = logging.getLogger(__name__)

# Biến môi trường được phép truyền cho tiến trình con (còn lại bị bỏ)
ENV_ALLOWLIST = {
    "PATH", "PATHEXT", "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC", "TEMP", "TMP",
    "USERPROFILE", "HOMEDRIVE", "HOMEPATH", "APPDATA", "LOCALAPPDATA", "PROGRAMDATA",
    "PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMW6432", "COMMONPROGRAMFILES",
    "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE", "OS", "USERNAME", "COMPUTERNAME",
    "LANG", "LC_ALL", "TERM", "HOME",
    "JAVA_HOME", "ANDROID_HOME", "ANDROID_SDK_ROOT", "GRADLE_USER_HOME", "NODE_OPTIONS",
    "NPM_CONFIG_CACHE", "NVM_HOME", "NVM_SYMLINK",
}
_SECRET_NAME = re.compile(r"(?i)(KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL|AUTH)")
_CMD_UNSAFE = re.compile(r'[&|<>^%!"\r\n`]')


class UnsafeCommandError(ValueError):
    pass


def minimal_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k.upper() in ENV_ALLOWLIST and not _SECRET_NAME.search(k)}
    for k, v in (extra or {}).items():
        env[k] = v
    return env


def which(name: str, override: str | None = None) -> str | None:
    if override:
        p = Path(override)
        if p.is_file():
            return str(p)
        if p.is_dir():
            for ext in ("", ".exe", ".cmd", ".bat"):
                cand = p / f"{name}{ext}"
                if cand.is_file():
                    return str(cand)
        return None
    return shutil.which(name)


def node_cli_script(tool: str, node_path: str | None = None) -> str | None:
    """Tìm npm-cli.js / npx-cli.js cạnh node.exe để chạy không cần cmd.exe."""
    node = node_path or which("node")
    if not node:
        return None
    base = Path(node).resolve().parent / "node_modules" / "npm" / "bin"
    script = base / f"{tool}-cli.js"
    return str(script) if script.is_file() else None


def build_argv(argv: list[str], node_path: str | None = None) -> list[str]:
    """Chuyển argv logic thành argv thực thi an toàn trên Windows."""
    if not argv:
        raise UnsafeCommandError("Lệnh rỗng")
    prog, args = argv[0], argv[1:]
    for a in argv:
        if "\x00" in a:
            raise UnsafeCommandError("Tham số chứa NUL")
    if prog in ("npm", "npx"):
        node = node_path or which("node")
        script = node_cli_script(prog, node)
        if node and script:
            return [node, script, *args]
    resolved = prog if os.path.isabs(prog) else (which(prog) or prog)
    if sys.platform == "win32" and resolved.lower().endswith((".cmd", ".bat")):
        for a in [resolved, *args]:
            if _CMD_UNSAFE.search(a):
                raise UnsafeCommandError(f"Tham số không an toàn cho .cmd: {a!r}")
        comspec = os.environ.get("COMSPEC", r"C:\Windows\System32\cmd.exe")
        return [comspec, "/d", "/s", "/c", subprocess.list2cmdline([resolved, *args])]
    return [resolved, *args]


@dataclass
class RunResult:
    argv: list[str]
    returncode: int | None
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    error: str | None = None
    extra: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.timed_out and self.error is None


def run(
    argv: list[str],
    cwd: Path | str | None = None,
    timeout: float = 60,
    env: dict[str, str] | None = None,
    node_path: str | None = None,
) -> RunResult:
    """Chạy đồng bộ (dùng trong worker thread, không gọi trên GUI thread)."""
    try:
        real = build_argv(argv, node_path)
    except UnsafeCommandError as exc:
        return RunResult(argv, None, error=str(exc))
    if cwd is not None and not Path(cwd).is_dir():
        return RunResult(argv, None, error=f"Thư mục làm việc không tồn tại: {cwd}")
    flags = 0
    if sys.platform == "win32":
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
    try:
        proc = subprocess.Popen(
            real, cwd=str(cwd) if cwd else None, env=env if env is not None else minimal_env(),
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=False, creationflags=flags,
            # Ngoài Windows: tiến trình con có process group riêng để kill_tree (os.killpg)
            # chỉ diệt cây con, không diệt chính App Builder.
            start_new_session=sys.platform != "win32",
        )
    except FileNotFoundError:
        return RunResult(argv, None, error=f"Không tìm thấy chương trình: {argv[0]}")
    except OSError as exc:
        return RunResult(argv, None, error=f"Không chạy được {argv[0]}: {exc}")
    job = _assign_job(proc.pid)
    try:
        out, err = proc.communicate(timeout=timeout)
        return RunResult(argv, proc.returncode, _decode(out), _decode(err))
    except subprocess.TimeoutExpired:
        kill_tree(proc.pid, job)
        try:
            out, err = proc.communicate(timeout=5)
        except Exception:
            out, err = b"", b""
        return RunResult(argv, None, _decode(out), _decode(err), timed_out=True)
    finally:
        _close_job(job)


def _decode(data: bytes | None) -> str:
    if not data:
        return ""
    for enc in ("utf-8", "mbcs" if sys.platform == "win32" else "latin-1"):
        try:
            return redact(data.decode(enc))
        except (UnicodeDecodeError, LookupError):
            continue
    return redact(data.decode("utf-8", "replace"))


# ---- Windows Job Object ---------------------------------------------------------

def _assign_job(pid: int):
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        k32 = ctypes.WinDLL("kernel32", use_last_error=True)

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [(n, ctypes.c_ulonglong) for n in (
                "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

        class BASIC(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong), ("PerJobUserTimeLimit", ctypes.c_longlong),
                        ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                        ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                        ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                        ("SchedulingClass", wintypes.DWORD)]

        class EXTENDED(ctypes.Structure):
            _fields_ = [("BasicLimitInformation", BASIC), ("IoInfo", IO_COUNTERS),
                        ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                        ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

        k32.CreateJobObjectW.restype = wintypes.HANDLE
        k32.OpenProcess.restype = wintypes.HANDLE
        job = k32.CreateJobObjectW(None, None)
        if not job:
            return None
        info = EXTENDED()
        info.BasicLimitInformation.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        k32.SetInformationJobObject(wintypes.HANDLE(job), 9, ctypes.byref(info), ctypes.sizeof(info))
        hproc = k32.OpenProcess(0x0001 | 0x0100, False, pid)  # TERMINATE | SET_QUOTA
        if hproc:
            k32.AssignProcessToJobObject(wintypes.HANDLE(job), wintypes.HANDLE(hproc))
            k32.CloseHandle(wintypes.HANDLE(hproc))
        return job
    except Exception:  # pragma: no cover
        return None


def _close_job(job) -> None:
    if job and sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes
            ctypes.WinDLL("kernel32").CloseHandle(wintypes.HANDLE(job))
        except Exception:
            pass


def kill_tree(pid: int, job=None) -> None:
    if sys.platform == "win32":
        if job:
            try:
                import ctypes
                from ctypes import wintypes
                ctypes.WinDLL("kernel32").TerminateJobObject(wintypes.HANDLE(job), 1)
                return
            except Exception:
                pass
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True,
                       creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        try:
            pgid = os.getpgid(pid)
            if pgid == os.getpgrp():
                # Tiến trình chung process group với App Builder: chỉ diệt chính nó,
                # không bao giờ killpg nhóm của mình.
                os.kill(pid, 9)
            else:
                os.killpg(pgid, 9)
        except Exception:
            pass
