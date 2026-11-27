"""Che secret trong log, thông báo lỗi và output tiến trình."""
from __future__ import annotations

import logging
import re

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"sk-ant-[A-Za-z0-9_\-]{10,}"), "sk-ant-***"),
    (re.compile(r"sk-(?:proj-)?[A-Za-z0-9_\-]{16,}"), "sk-***"),
    (re.compile(r"AIza[0-9A-Za-z_\-]{30,}"), "AIza***"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"), "gh*_***"),
    (re.compile(r"github_pat_[A-Za-z0-9_]{20,}"), "github_pat_***"),
    (re.compile(r"xox[abprs]-[A-Za-z0-9\-]{10,}"), "xox*-***"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AKIA***"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"), "[PRIVATE KEY]"),
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-]{12,}"), r"\1***"),
    (re.compile(r"(?i)(https?://)[^/\s:@]+:[^/\s@]+@"), r"\1***:***@"),
    (re.compile(r"(?i)((?:api[_-]?key|token|secret|password|passwd|pwd)\s*[=:]\s*)[\"']?[^\s\"',;]{6,}"), r"\1***"),
]


def redact(text: str, extra_secrets: list[str] | None = None) -> str:
    if not text:
        return text
    for secret in extra_secrets or []:
        if secret and len(secret) >= 6:
            text = text.replace(secret, "***")
    for pat, repl in _PATTERNS:
        text = pat.sub(repl, text)
    return text


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
        except Exception:
            return True
        record.msg = redact(msg)
        record.args = ()
        return True
