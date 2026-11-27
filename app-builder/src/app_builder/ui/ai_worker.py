"""Chạy streaming của provider trên QThread riêng; phát tín hiệu về luồng UI. Hủy bằng CancelToken."""
from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal, Slot

from app_builder.providers._errors import to_provider_error
from app_builder.providers.base import AIProvider, AIRequest, CancelToken, Done, ProviderError, TextDelta


class _StreamWorker(QObject):
    text = Signal(str)
    done = Signal(object)    # Done
    failed = Signal(object)  # ProviderError
    ended = Signal()

    def __init__(self, provider: AIProvider, request: AIRequest, cancel: CancelToken) -> None:
        super().__init__()
        self.provider, self.request, self.cancel = provider, request, cancel

    @Slot()
    def run(self) -> None:
        try:
            for ev in self.provider.stream(self.request, self.cancel):
                if isinstance(ev, TextDelta):
                    self.text.emit(ev.text)
                elif isinstance(ev, Done):
                    self.done.emit(ev)
        except ProviderError as exc:
            self.failed.emit(exc)
        except Exception as exc:  # pragma: no cover - lỗi ngoài dự kiến
            self.failed.emit(to_provider_error(exc))
        finally:
            self.ended.emit()


class ChatStream(QObject):
    """Một lần gọi streaming. Dùng: s = ChatStream(provider, req); s.text.connect(...); s.start()."""
    text = Signal(str)
    done = Signal(object)
    failed = Signal(object)
    ended = Signal()

    def __init__(self, provider: AIProvider, request: AIRequest, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.request = request
        self.cancel_token = CancelToken()
        self._thread = QThread()
        self._worker = _StreamWorker(provider, request, self.cancel_token)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.text.connect(self.text)
        self._worker.done.connect(self.done)
        self._worker.failed.connect(self.failed)
        self._worker.ended.connect(self._thread.quit)
        self._thread.finished.connect(self._finished)

    def start(self) -> None:
        self._thread.start()

    def cancel(self) -> None:
        self.cancel_token.cancel()

    @property
    def running(self) -> bool:
        return self._thread.isRunning()

    def wait(self, ms: int = 5000) -> bool:
        return self._thread.wait(ms)

    def _finished(self) -> None:
        self._worker.deleteLater()
        self.ended.emit()
