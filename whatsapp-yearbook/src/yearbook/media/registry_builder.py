from __future__ import annotations

import json
import logging
from pathlib import Path

from yearbook.constants import MEDIA_EXTENSIONS, MEDIA_IMAGE, MEDIA_VOICE
from yearbook.contracts.media import MediaRegistryRecord
from yearbook.contracts.messages import MessageRecord
from yearbook.pipeline.state import PipelineState
from yearbook.storage.jsonl_store import JsonlStore
from yearbook.utils.file_utils import infer_media_kind, infer_mime_type
from yearbook.utils.hashing import sha256_file

logger = logging.getLogger(__name__)


class MediaRegistryBuilder:
    def __init__(self, state: PipelineState) -> None:
        self.paths = state.paths

    def build_registry(self, messages: list[MessageRecord]) -> list[MediaRegistryRecord]:
        # Build filename → message mapping
        attachment_map: dict[str, MessageRecord] = {}
        for msg in messages:
            if msg.attachment:
                attachment_map[msg.attachment.lower()] = msg

        records: list[MediaRegistryRecord] = []
        hash_groups: dict[str, list[str]] = {}  # sha256 → [media_ids]
        counter = 0

        if not self.paths.media_dir.exists():
            logger.warning("Media directory does not exist, registry will be empty.")
            return records

        for f in sorted(self.paths.media_dir.iterdir()):
            if not f.is_file():
                continue

            counter += 1
            media_id = f"media_{counter:06d}"
            kind = infer_media_kind(f)
            mime = infer_mime_type(f)
            try:
                file_hash = sha256_file(f)
                size = f.stat().st_size
            except OSError as e:
                logger.warning("Could not read %s: %s", f.name, e)
                continue

            # Track duplicates
            hash_groups.setdefault(file_hash, []).append(media_id)

            # Link to message
            linked_msg = attachment_map.get(f.name.lower())

            rec = MediaRegistryRecord(
                media_id=media_id,
                filename=f.name,
                relative_path=str(f.relative_to(self.paths.root)),
                media_kind=kind,
                mime_type=mime,
                extension=f.suffix.lower(),
                sha256=file_hash,
                size_bytes=size,
                message_id=linked_msg.message_id if linked_msg else None,
                timestamp=linked_msg.timestamp if linked_msg else None,
                sender=linked_msg.sender if linked_msg else None,
                date=linked_msg.date if linked_msg else None,
                exists_on_disk=True,
            )
            records.append(rec)

        # Mark duplicate groups
        for file_hash, ids in hash_groups.items():
            if len(ids) > 1:
                group_id = f"dedup_{file_hash[:8]}"
                for rec in records:
                    if rec.media_id in ids:
                        rec.dedupe_group_id = group_id

        logger.info("Media registry: %d files indexed", len(records))
        return records


def run_media_registry(state: PipelineState) -> None:
    """Pipeline C (media part 1) — build media registry."""
    paths = state.paths

    # Load messages
    msg_store = JsonlStore(paths.messages_raw)
    messages = msg_store.read_all(MessageRecord)

    builder = MediaRegistryBuilder(state)
    records = builder.build_registry(messages)

    # Save as a JSON dict (media_id → record) for fast lookup
    registry_dict = {r.media_id: r.model_dump() for r in records}
    paths.media_registry.write_text(
        json.dumps(registry_dict, indent=2, default=str), encoding="utf-8"
    )
    logger.info("Media registry saved: %s", paths.media_registry)
