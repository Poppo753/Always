from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from yearbook.constants import SCHEMA_VERSION
from yearbook.contracts.ranking import (
    CandidateQuote,
    ScoredEvent,
    ScoredImage,
    ScoredMessage,
    ScoredVoice,
)


class DayStats(BaseModel):
    message_count: int = 0
    image_count: int = 0
    voice_count: int = 0
    video_count: int = 0
    conversation_clusters: int = 0


class DailyContext(BaseModel):
    schema_version: str = SCHEMA_VERSION
    date: str  # YYYY-MM-DD
    stats: DayStats = Field(default_factory=DayStats)
    top_messages: list[ScoredMessage] = Field(default_factory=list)
    top_events: list[ScoredEvent] = Field(default_factory=list)
    top_images: list[ScoredImage] = Field(default_factory=list)
    top_videos: list[dict] = Field(default_factory=list)
    top_voice_transcripts: list[ScoredVoice] = Field(default_factory=list)
    candidate_quotes: list[CandidateQuote] = Field(default_factory=list)


class DailyReasoning(BaseModel):
    schema_version: str = SCHEMA_VERSION
    date: str
    model_name: str
    prompt_version: str
    main_theme: str = ""
    day_type: str = "quiet_day"
    importance_level: str = "medium"
    mood: str = "neutral"
    reasoning_summary: str = ""
    evidence: dict[str, list[str]] = Field(default_factory=dict)
    selected_quote_message_id: Optional[str] = None
    selected_image_media_ids: list[str] = Field(default_factory=list)


class DailySummary(BaseModel):
    schema_version: str = SCHEMA_VERSION
    date: str
    title: str = ""
    summary: str = ""
    key_moments: list[str] = Field(default_factory=list)
    quote: str = ""
    mood: str = "neutral"
    selected_image_media_ids: list[str] = Field(default_factory=list)
    stats: dict[str, Any] = Field(default_factory=dict)
    source_evidence: dict[str, list[str]] = Field(default_factory=dict)
