from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from yearbook.contracts.messages import MessageRecord
from yearbook.constants import MSG_TEXT

logger = logging.getLogger(__name__)


class AttachmentMatcher:
    """Links attachment filenames in messages to actual files on disk."""

    def __init__(self, media_dir: Path) -> None:
        self.media_dir = media_dir
        self._index: dict[str, Path] = {}
        if media_dir.exists():
            for f in media_dir.iterdir():
                if f.is_file():
                    self._index[f.name.lower()] = f

    def resolve(self, filename: str) -> Optional[Path]:
        return self._index.get(filename.lower())

    def enrich_messages(self, messages: list[MessageRecord]) -> list[MessageRecord]:
        missing = 0
        for msg in messages:
            if msg.attachment:
                resolved = self.resolve(msg.attachment)
                if not resolved:
                    missing += 1
                    msg.parse_warnings.append(f"attachment_not_found: {msg.attachment}")
        if missing:
            logger.warning("%d attachments referenced but not found on disk", missing)
        return messages
