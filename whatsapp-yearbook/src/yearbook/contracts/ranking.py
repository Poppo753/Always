from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from yearbook.constants import SCHEMA_VERSION


class SelectionMetadata(BaseModel):
    message_limit: int = 20
    image_limit: int = 4
    voice_limit: int = 2
    event_limit: int = 6


class RankedDayAssets(BaseModel):
    schema_version: str = SCHEMA_VERSION
    date: str  # YYYY-MM-DD
    top_message_ids: list[str] = Field(default_factory=list)
    top_event_ids: list[str] = Field(default_factory=list)
    top_image_media_ids: list[str] = Field(default_factory=list)
    top_voice_media_ids: list[str] = Field(default_factory=list)
    discarded_message_ids: list[str] = Field(default_factory=list)
    selection_metadata: SelectionMetadata = Field(default_factory=SelectionMetadata)


class ScoredMessage(BaseModel):
    message_id: str
    sender: str
    timestamp: str
    text: str
    score: float = 0.5


class ScoredEvent(BaseModel):
    event_id: str
    event_type: str
    description: str
    score: float = 0.5


class ScoredImage(BaseModel):
    media_id: str
    filename: str
    caption: str
    score: float = 0.5


class ScoredVoice(BaseModel):
    media_id: str
    short_summary: str
    score: float = 0.5


class CandidateQuote(BaseModel):
    message_id: str
    text: str
    sender: str = ""
    score: float = 0.5
