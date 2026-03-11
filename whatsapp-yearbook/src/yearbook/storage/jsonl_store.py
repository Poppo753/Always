from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class JsonlStore:
    """Read/write newline-delimited JSON files."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def append(self, record: BaseModel) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(record.model_dump_json() + "\n")

    def write_all(self, records: list[BaseModel]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            for r in records:
                f.write(r.model_dump_json() + "\n")

    def read_all(self, model_class: Type[T]) -> list[T]:
        if not self.path.exists():
            return []
        results = []
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    results.append(model_class.model_validate_json(line))
        return results

    def iter_raw(self) -> Iterator[dict[str, Any]]:
        if not self.path.exists():
            return
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)

    def exists(self) -> bool:
        return self.path.exists() and self.path.stat().st_size > 0
