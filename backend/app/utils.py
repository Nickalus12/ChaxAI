from __future__ import annotations

import re
from pathlib import Path

__all__ = ["secure_filename"]

_invalid_re = re.compile(r"[^A-Za-z0-9_.-]")


def secure_filename(filename: str) -> str:
    """Return a secure version of the given filename."""
    name = Path(filename).name
    name = _invalid_re.sub("_", name)
    if not name:
        raise ValueError("Invalid filename")
    return name
