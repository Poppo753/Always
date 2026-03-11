from __future__ import annotations

import json
import logging
from pathlib import Path

from yearbook.contracts.run import InputInventory
from yearbook.pipeline.state import PipelineState
from yearbook.utils.hashing import sha256_file

logger = logging.getLogger(__name__)


class InventoryBuilder:
    def __init__(self, state: PipelineState) -> None:
        self.paths = state.paths

    def build(self, warnings: list[str] | None = None) -> InputInventory:
        chat_hash = sha256_file(self.paths.chat_file)
        chat_size = self.paths.chat_file.stat().st_size

        media_files: list[str] = []
        if self.paths.media_dir.exists():
            media_files = sorted(
                str(f.name) for f in self.paths.media_dir.iterdir() if f.is_file()
            )

        inv = InputInventory(
            run_id=self.paths.run_id,
            chat_file_hash=chat_hash,
            chat_file_size_bytes=chat_size,
            media_files_count=len(media_files),
            media_files=media_files,
            warnings=warnings or [],
        )

        out = self.paths.input_inventory
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(inv.model_dump_json(indent=2), encoding="utf-8")
        logger.info("Inventory saved: %d media files", len(media_files))
        return inv
