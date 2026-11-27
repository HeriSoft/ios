"""i18n đơn giản: resources/i18n/<lang>.json, khóa dạng 'dashboard.title'."""
from __future__ import annotations

import json
from functools import lru_cache

from app_builder.core.config import resources_dir

_lang = "vi"


@lru_cache(maxsize=4)
def _load(lang: str) -> dict[str, str]:
    path = resources_dir() / "i18n" / f"{lang}.json"
    try:
        return json.loads(path.read_text("utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def set_language(lang: str) -> None:
    global _lang
    _lang = lang if lang in ("vi", "en") else "vi"


def language() -> str:
    return _lang


def tr(key: str, **kwargs) -> str:
    text = _load(_lang).get(key) or _load("vi").get(key) or key
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text
