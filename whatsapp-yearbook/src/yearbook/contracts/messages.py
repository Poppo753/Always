from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from yearbook.constants import SCHEMA_VERSION, MSG_TEXT


class MessageRecord(BaseModel):
    schema_version: str = SCHEMA_VERSION
    message_id: str
    source_line_start: int
    source_line_end: int
    timestamp: datetime
    date: str  # YYYY-MM-DD
    sender: str
    message_type: str = MSG_TEXT
    text: str = ""
    attachment: Optional[str] = None
    attachment_kind: Optional[str] = None
    is_system: bool = False
    reply_to_message_id: Optional[str] = None
    language: Optional[str] = None
    parse_warnings: list[str] = Field(default_factory=list)
