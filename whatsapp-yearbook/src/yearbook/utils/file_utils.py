from __future__ import annotations

import mimetypes
from pathlib import Path

from yearbook.constants import MEDIA_EXTENSIONS


def infer_media_kind(path: Path) -> str:
    ext = path.suffix.lower()
    return MEDIA_EXTENSIONS.get(ext, "document")


def infer_mime_type(path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    return mime or "application/octet-stream"


def safe_read_text(path: Path, encodings: list[str] | None = None) -> str:
    if encodings is None:
        encodings = ["utf-8", "utf-8-sig", "latin-1"]
    for enc in encodings:
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, LookupError):
            continue
    raise ValueError(f"Cannot decode {path} with any known encoding")
