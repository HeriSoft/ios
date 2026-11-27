"""Widget dùng chung và helper chạy tác vụ nền (không block GUI thread)."""
from __future__ import annotations

import traceback
from typing import Any, Callable

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app_builder.core.i18n import tr


def label(text: str, obj: str | None = None, wrap: bool = False) -> QLabel:
    lb = QLabel(text)
    if obj:
        lb.setObjectName(obj)
    lb.setWordWrap(wrap)
    return lb


def badge(text: str, kind: str = "") -> QLabel:
    lb = QLabel(text)
    lb.setObjectName({"ok": "BadgeOk", "warn": "BadgeWarn", "danger": "BadgeDanger"}.get(kind, "Badge"))
    return lb


def set_badge_kind(lb: QLabel, text: str, kind: str) -> None:
    lb.setText(text)
    lb.setObjectName({"ok": "BadgeOk", "warn": "BadgeWarn", "danger": "BadgeDanger"}.get(kind, "Badge"))
    lb.style().unpolish(lb)
    lb.style().polish(lb)


class MilestoneNotice(QFrame):
    """Đánh dấu rõ chức năng chưa triển khai (không đặt nút giả)."""

    def __init__(self, title: str, milestone: str, detail: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Notice")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        row = QHBoxLayout()
        row.addWidget(label(title, "H3"))
        row.addStretch(1)
        if milestone:
            row.addWidget(badge(tr("common.planned", milestone=milestone), "warn"))
        lay.addLayout(row)
        if detail:
            lay.addWidget(label(detail, "Muted", wrap=True))


def centered(widget: QWidget, max_width: int = 640) -> QWidget:
    host = QWidget()
    lay = QHBoxLayout(host)
    lay.addStretch(1)
    widget.setMaximumWidth(max_width)
    lay.addWidget(widget, 10)
    lay.addStretch(1)
    host_v = QWidget()
    v = QVBoxLayout(host_v)
    v.addStretch(1)
    v.addWidget(host)
    v.addStretch(2)
    return host_v


# ---- Tác vụ nền -------------------------------------------------------------------

class _Signals(QObject):
    done = Signal(object)
    failed = Signal(str)


class _Task(QRunnable):
    def __init__(self, fn: Callable[[], Any]) -> None:
        super().__init__()
        self.fn = fn
        self.signals = _Signals()
        self.setAutoDelete(True)

    def run(self) -> None:  # chạy ở worker thread
        try:
            result = self.fn()
        except Exception as exc:
            self.signals.failed.emit(f"{exc}\n\n{traceback.format_exc(limit=3)}")
        else:
            self.signals.done.emit(result)


_keep: set = set()


def run_in_background(fn: Callable[[], Any], on_done: Callable[[Any], None] | None = None,
                      on_error: Callable[[str], None] | None = None) -> None:
    task = _Task(fn)
    sig = task.signals
    _keep.add(sig)

    def _finish(*_):
        _keep.discard(sig)

    if on_done:
        sig.done.connect(on_done, Qt.ConnectionType.QueuedConnection)
    if on_error:
        sig.failed.connect(on_error, Qt.ConnectionType.QueuedConnection)
    sig.done.connect(_finish)
    sig.failed.connect(_finish)
    QThreadPool.globalInstance().start(task)
