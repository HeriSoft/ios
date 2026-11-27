"""Một event loop asyncio chạy trên thread nền; kết quả/sự kiện trả về GUI thread qua Qt signal (queued)."""
from __future__ import annotations

import asyncio
import threading
from concurrent.futures import Future
from typing import Any, AsyncIterator, Callable, Coroutine

from PySide6.QtCore import QObject, Qt, Signal


class _Loop:
    _instance: "_Loop | None" = None

    def __init__(self) -> None:
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run, name="ai-loop", daemon=True)
        self.thread.start()

    def _run(self) -> None:
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    @classmethod
    def get(cls) -> "_Loop":
        if cls._instance is None:
            cls._instance = _Loop()
        return cls._instance


def submit(coro: Coroutine) -> Future:
    return asyncio.run_coroutine_threadsafe(coro, _Loop.get().loop)


class _Bridge(QObject):
    item = Signal(object)
    done = Signal(object)    # kết quả hoặc None
    failed = Signal(str)


class AsyncCall(QObject):
    """Chạy 1 coroutine; gọi on_done/on_error trên GUI thread."""

    def __init__(self, coro: Coroutine, on_done: Callable[[Any], None] | None = None,
                 on_error: Callable[[str], None] | None = None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.bridge = _Bridge()
        if on_done:
            self.bridge.done.connect(on_done, Qt.ConnectionType.QueuedConnection)
        if on_error:
            self.bridge.failed.connect(on_error, Qt.ConnectionType.QueuedConnection)

        async def wrapper():
            try:
                res = await coro
            except asyncio.CancelledError:
                self.bridge.failed.emit("cancelled")
                return
            except Exception as exc:  # noqa: BLE001
                from app_builder.providers.base import classify_exception
                self.bridge.failed.emit(classify_exception(exc).user_message)
                return
            self.bridge.done.emit(res)

        self.future = submit(wrapper())

    def cancel(self) -> None:
        self.future.cancel()


class AsyncStream(QObject):
    """Tiêu thụ async iterator trên loop nền; mỗi phần tử phát qua on_item; hủy được bằng cancel()."""

    def __init__(self, agen_factory: Callable[[], AsyncIterator], on_item: Callable[[Any], None],
                 on_done: Callable[[Any], None], on_error: Callable[[str], None] | None = None,
                 parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.bridge = _Bridge()
        self.bridge.item.connect(on_item, Qt.ConnectionType.QueuedConnection)
        self.bridge.done.connect(on_done, Qt.ConnectionType.QueuedConnection)
        if on_error:
            self.bridge.failed.connect(on_error, Qt.ConnectionType.QueuedConnection)
        self._task: asyncio.Task | None = None
        loop = _Loop.get().loop

        async def runner():
            try:
                async for x in agen_factory():
                    self.bridge.item.emit(x)
            except asyncio.CancelledError:
                self.bridge.done.emit("cancelled")
                return
            except Exception as exc:  # noqa: BLE001
                self.bridge.failed.emit(str(exc))
                self.bridge.done.emit("error")
                return
            self.bridge.done.emit("finished")

        def start():
            self._task = loop.create_task(runner())

        loop.call_soon_threadsafe(start)

    def cancel(self) -> None:
        loop = _Loop.get().loop

        def _c():
            if self._task and not self._task.done():
                self._task.cancel()

        loop.call_soon_threadsafe(_c)
