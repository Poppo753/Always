from __future__ import annotations

import logging

from yearbook.contracts.messages import MessageRecord
from yearbook.pipeline.state import PipelineState
from yearbook.parsing.whatsapp_parser import WhatsAppParser
from yearbook.parsing.attachment_matcher import AttachmentMatcher
from yearbook.storage.jsonl_store import JsonlStore

logger = logging.getLogger(__name__)


def run_parse(state: PipelineState) -> None:
    """Pipeline B — parse _chat.txt into message records."""
    paths = state.paths
    config = state.config

    parser = WhatsAppParser(
        date_fmt=config.get("parsing", {}).get("date_format", "%d/%m/%y, %H:%M")
    )
    messages = parser.parse_file(paths.chat_file)

    # Enrich with attachment presence on disk
    matcher = AttachmentMatcher(paths.media_dir)
    messages = matcher.enrich_messages(messages)

    # Persist raw messages
    store = JsonlStore(paths.messages_raw)
    store.write_all(messages)
    logger.info("Saved %d message records to %s", len(messages), paths.messages_raw)
