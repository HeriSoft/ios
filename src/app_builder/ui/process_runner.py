"""Chạy tiến trình dài bằng QProcess (không block GUI), stream output, dừng cả cây tiến trình."""
from __future__ import annotations

import codecs
import uuid
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, Signal

from app_builder.core import process_manager as pm
from app_builder.core.database import Database
from app_builder.core.redaction import redact
from app_builder.core.schemas import utcnow_iso


class ProcessRunner(QObject):
    output = Signal(str)
    started = Signal(str)        # job id
    finished = Signal(str, int)  # job id, exit code (-1 = bị dừng/lỗi)

    def __init__(self, db: Database | None = None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.db = db
        self.proc: QProcess | None = None
        self.job_id: str | None = None
        self._stopped = False

    @property
    def running(self) -> bool:
        return self.proc is not None and self.proc.state() != QProcess.ProcessState.NotRunning

    def start(self, argv: list[str], cwd: Path | str, kind: str, project_id: int | None = None,
              node_path: str | None = None, extra_env: dict[str, str] | None = None) -> str | None:
        if self.running:
            self.output.emit("⚠ Đang có tiến trình chạy. Dừng nó trước.\n")
            return None
        try:
            real = pm.build_argv(argv, node_path)
        except pm.UnsafeCommandError as exc:
            self.output.emit(f"✖ {exc}\n")
            return None
        self.job_id = uuid.uuid4().hex[:12]
        self._stopped = False
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")
        proc = QProcess(self)
        env = QProcessEnvironment()
        for k, v in pm.minimal_env(extra_env).items():
            env.insert(k, v)
        proc.setProcessEnvironment(env)
        proc.setWorkingDirectory(str(cwd))
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.readyReadStandardOutput.connect(self._read)
        proc.finished.connect(self._done)
        proc.errorOccurred.connect(self._error)
        self.proc = proc
        shown = " ".join(argv)
        self.output.emit(f"\n$ {shown}\n  (cwd: {cwd})\n")
        if self.db:
            self.db.execute(
                "INSERT INTO jobs(id, project_id, kind, status, detail, created_at, started_at) VALUES (?,?,?,?,?,?,?)",
                (self.job_id, project_id, kind, "running", shown, utcnow_iso(), utcnow_iso()),
            )
        proc.start(real[0], real[1:])
        self.started.emit(self.job_id)
        return self.job_id

    def stop(self) -> None:
        if self.running and self.proc:
            self._stopped = True
            pid = self.proc.processId()
            self.output.emit("\n■ Đang dừng tiến trình (cả cây con)…\n")
            pm.kill_tree(pid)
            self.proc.kill()

    def _read(self) -> None:
        if self.proc:
            data = bytes(self.proc.readAllStandardOutput())
            self.output.emit(redact(self._decoder.decode(data)))

    def _finalize(self, status: str, code: int) -> None:
        if self.db and self.job_id:
            self.db.execute("UPDATE jobs SET status=?, finished_at=? WHERE id=?", (status, utcnow_iso(), self.job_id))
        jid = self.job_id or ""
        self.proc = None
        self.finished.emit(jid, code)

    def _done(self, code: int, exit_status) -> None:
        if self.proc is None:
            return
        if self._stopped:
            self.output.emit("■ Đã dừng.\n")
            self._finalize("cancelled", -1)
        else:
            ok = code == 0 and exit_status == QProcess.ExitStatus.NormalExit
            self.output.emit(("✔ Hoàn tất" if ok else f"✖ Thất bại (exit {code})") + "\n")
            self._finalize("succeeded" if ok else "failed", code)

    def _error(self, err) -> None:
        if err == QProcess.ProcessError.FailedToStart and self.proc is not None:
            self.output.emit(f"✖ Không khởi chạy được: {self.proc.errorString()}\n")
            self._finalize("failed", -1)
