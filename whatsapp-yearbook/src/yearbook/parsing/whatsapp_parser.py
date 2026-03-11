from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from yearbook.constants import (
    MSG_IMAGE, MSG_VIDEO, MSG_VOICE, MSG_DOCUMENT, MSG_STICKER, MSG_SYSTEM, MSG_TEXT, MSG_UNKNOWN,
    MEDIA_EXTENSIONS,
)
from yearbook.contracts.messages import MessageRecord
from yearbook.utils.file_utils import safe_read_text

logger = logging.getLogger(__name__)

# Pattern for DD/MM/YY, HH:MM - Sender: text
# Also handles DD/MM/YYYY, H:MM
_MSG_PATTERN = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4}),\s(\d{1,2}:\d{2})\s-\s(.+?):\s(.*)",
    re.DOTALL,
)
# System messages (no sender)
_SYS_PATTERN = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4}),\s(\d{1,2}:\d{2})\s-\s(.+)$"
)

# Attachment placeholder: <Media omitted> or <allegato: filename.ext>
_ATTACHMENT_PATTERN = re.compile(
    r"<allegato:\s*(.+?)>|<Media omitted>|\u200e?(.+\.(jpg|jpeg|png|gif|mp4|mov|opus|ogg|m4a|aac|pdf|webp|heic))\s*\(file allegato\)",
    re.IGNORECASE,
)

_DATE_FORMATS = ["%d/%m/%y, %H:%M", "%d/%m/%Y, %H:%M", "%d/%m/%y, %H:%M:%S"]


def _parse_timestamp(date_str: str, time_str: str) -> Optional[datetime]:
    raw = f"{date_str}, {time_str}"
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def _detect_attachment(text: str) -> tuple[Optional[str], Optional[str]]:
    """Return (filename, kind) if text contains an attachment reference."""
    m = _ATTACHMENT_PATTERN.search(text)
    if not m:
        return None, None

    # <allegato: filename>
    if m.group(1):
        filename = m.group(1).strip()
    elif m.group(2):
        filename = m.group(2).strip()
    else:
        return None, None

    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    kind = MEDIA_EXTENSIONS.get(ext, MSG_DOCUMENT)
    return filename, kind


def _msg_type_from_attachment_kind(kind: Optional[str]) -> str:
    if kind is None:
        return MSG_TEXT
    return kind if kind in (MSG_IMAGE, MSG_VIDEO, MSG_VOICE, MSG_DOCUMENT, MSG_STICKER) else MSG_UNKNOWN


class WhatsAppParser:
    """Parses a WhatsApp _chat.txt into MessageRecord objects."""

    def __init__(self, date_fmt: str = "%d/%m/%y, %H:%M") -> None:
        self.date_fmt = date_fmt

    def parse_file(self, path: Path) -> list[MessageRecord]:
        text = safe_read_text(path, ["utf-8", "utf-8-sig", "latin-1"])
        lines = text.splitlines()
        return self._parse_lines(lines)

    def _parse_lines(self, lines: list[str]) -> list[MessageRecord]:
        records: list[MessageRecord] = []
        msg_id_counter = 0

        # Group lines into raw message blocks
        blocks: list[tuple[int, str]] = []  # (line_start, full_text)
        current_start = 0
        current_lines: list[str] = []

        for i, line in enumerate(lines):
            if _MSG_PATTERN.match(line) or _SYS_PATTERN.match(line):
                if current_lines:
                    blocks.append((current_start, "\n".join(current_lines)))
                current_start = i + 1  # 1-based
                current_lines = [line]
            else:
                current_lines.append(line)

        if current_lines:
            blocks.append((current_start, "\n".join(current_lines)))

        for line_start, block in blocks:
            msg_id_counter += 1
            record = self._parse_block(block, line_start, line_start + block.count("\n"), msg_id_counter)
            if record:
                records.append(record)

        logger.info("Parsed %d messages from %d lines", len(records), len(lines))
        return records

    def _parse_block(self, block: str, line_start: int, line_end: int, counter: int) -> Optional[MessageRecord]:
        first_line, *rest_lines = block.split("\n", 1)
        rest = rest_lines[0] if rest_lines else ""
        msg_id = f"msg_{counter:06d}"

        # Try regular message
        m = _MSG_PATTERN.match(first_line)
        if m:
            date_str, time_str, sender, body = m.group(1), m.group(2), m.group(3), m.group(4)
            full_text = (body + ("\n" + rest if rest else "")).strip()

            ts = _parse_timestamp(date_str, time_str)
            if ts is None:
                logger.warning("Could not parse timestamp in: %s", first_line[:60])
                return None

            attachment, att_kind = _detect_attachment(full_text)
            msg_type = _msg_type_from_attachment_kind(att_kind) if attachment else MSG_TEXT

            # Clean text if it IS an attachment placeholder
            display_text = full_text if not attachment else ""

            return MessageRecord(
                message_id=msg_id,
                source_line_start=line_start,
                source_line_end=line_end,
                timestamp=ts,
                date=ts.strftime("%Y-%m-%d"),
                sender=sender.strip(),
                message_type=msg_type,
                text=display_text,
                attachment=attachment,
                attachment_kind=att_kind,
                is_system=False,
            )

        # Try system message
        s = _SYS_PATTERN.match(first_line)
        if s:
            date_str, time_str, body = s.group(1), s.group(2), s.group(3)
            ts = _parse_timestamp(date_str, time_str)
            if ts is None:
                return None
            return MessageRecord(
                message_id=msg_id,
                source_line_start=line_start,
                source_line_end=line_end,
                timestamp=ts,
                date=ts.strftime("%Y-%m-%d"),
                sender="__system__",
                message_type=MSG_SYSTEM,
                text=body.strip(),
                is_system=True,
            )

        return None
