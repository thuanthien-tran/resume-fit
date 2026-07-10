"""Sanitization helpers for values persisted to PostgreSQL/JSONB.

PostgreSQL text and jsonb cannot store the NUL character (U+0000). Some PDF/DOCX
extractors can emit embedded NUL/control characters, which later become JSON
escapes ("\\u0000") and make psycopg2 raise ``unsupported Unicode escape
sequence``. Keep useful whitespace, remove unsafe controls recursively.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from uuid import UUID

_SAFE_CONTROL_CHARS = {"\n", "\r", "\t"}


def sanitize_text(value: str) -> str:
    """Return text safe for PostgreSQL TEXT/JSONB storage.

    Removes NUL and non-whitespace C0/C1 control characters. Preserves normal
    Unicode, Vietnamese accents, newlines, carriage returns and tabs.
    """
    if not value:
        return value
    return "".join(
        ch
        for ch in value
        if ch in _SAFE_CONTROL_CHARS or (ch != "\x00" and not (ord(ch) < 32 or 127 <= ord(ch) <= 159))
    )


def sanitize_for_jsonb(value):
    """Recursively sanitize a structure before assigning it to JSONB columns."""
    if isinstance(value, str):
        return sanitize_text(value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Mapping):
        return {sanitize_text(str(k)): sanitize_for_jsonb(v) for k, v in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return [sanitize_for_jsonb(item) for item in value]
    return sanitize_text(str(value))
