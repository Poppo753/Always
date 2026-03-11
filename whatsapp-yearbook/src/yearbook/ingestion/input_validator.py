from __future__ import annotations

import logging
from pathlib import Path

from yearbook.exceptions import InputValidationError
from yearbook.pipeline.state import PipelineState

logger = logging.getLogger(__name__)


class InputValidator:
    def __init__(self, state: PipelineState) -> None:
        self.paths = state.paths
        self.warnings: list[str] = []

    def validate(self) -> None:
        if not self.paths.chat_file.exists():
            raise InputValidationError(
                f"Chat file not found: {self.paths.chat_file}\n"
                f"Please copy your WhatsApp export to: {self.paths.input_dir}/_chat.txt"
            )

        if self.paths.chat_file.stat().st_size == 0:
            raise InputValidationError("Chat file is empty.")

        if not self.paths.media_dir.exists():
            self.warnings.append(
                f"Media directory not found: {self.paths.media_dir} — "
                "image and voice analysis will be skipped."
            )
            logger.warning("Media dir not found: %s", self.paths.media_dir)
        else:
            media_count = sum(1 for _ in self.paths.media_dir.iterdir() if _.is_file())
            logger.info("Found %d media files in %s", media_count, self.paths.media_dir)
