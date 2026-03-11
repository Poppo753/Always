from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class CacheStore:
    """A simple file-based cache keyed by a hash string."""

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key_path(self, key: str) -> Path:
        # Use first 2 chars as subdir to avoid huge flat directories
        return self.cache_dir / key[:2] / f"{key}.json"

    def has(self, key: str) -> bool:
        return self._key_path(key).exists()

    def get(self, key: str, model_class: Type[T]) -> Optional[T]:
        p = self._key_path(key)
        if not p.exists():
            return None
        return model_class.model_validate_json(p.read_text(encoding="utf-8"))

    def get_raw(self, key: str) -> Optional[dict[str, Any]]:
        p = self._key_path(key)
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    def set(self, key: str, record: BaseModel) -> None:
        p = self._key_path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(record.model_dump_json(indent=2), encoding="utf-8")

    def set_raw(self, key: str, data: dict[str, Any]) -> None:
        p = self._key_path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
