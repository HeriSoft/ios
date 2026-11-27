"""Event bus đơn giản (thread-safe, không phụ thuộc Qt) để core/services báo cho UI."""
from __future__ import annotations

import logging
import threading
from collections import defaultdict
from typing import Any, Callable

log = logging.getLogger(__name__)
Handler = Callable[..., None]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)
        self._lock = threading.Lock()

    def subscribe(self, topic: str, handler: Handler) -> Callable[[], None]:
        with self._lock:
            self._handlers[topic].append(handler)

        def unsubscribe() -> None:
            with self._lock:
                if handler in self._handlers[topic]:
                    self._handlers[topic].remove(handler)

        return unsubscribe

    def publish(self, topic: str, **payload: Any) -> None:
        with self._lock:
            handlers = list(self._handlers.get(topic, ())) + list(self._handlers.get("*", ()))
        for h in handlers:
            try:
                h(topic=topic, **payload)
            except Exception:
                log.exception("Lỗi trong handler sự kiện %s", topic)


bus = EventBus()
