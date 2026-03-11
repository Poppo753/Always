from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(path: Path, chunk_size: int = 65536) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def cache_key(base_hash: str, *extras: str) -> str:
    """Combine a file hash with additional keys (e.g. prompt version, model name)."""
    combined = base_hash + "".join(extras)
    return hashlib.sha256(combined.encode()).hexdigest()
