from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from yearbook.constants import SCHEMA_VERSION


class EventRecord(BaseModel):
    schema_version: str = SCHEMA_VERSION
    event_id: str
    date: str  # YYYY-MM-DD
    time_start: Optional[datetime] = None
    time_end: Optional[datetime] = None
    event_type: str = "conversation"
    confidence: float = 0.5
    description: str = ""
    message_ids: list[str] = Field(default_factory=list)
    media_ids: list[str] = Field(default_factory=list)
    trigger_signals: list[str] = Field(default_factory=list)
    score: float = 0.5
