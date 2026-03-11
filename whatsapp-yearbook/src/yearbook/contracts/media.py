from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from yearbook.constants import SCHEMA_VERSION


class MediaRegistryRecord(BaseModel):
    schema_version: str = SCHEMA_VERSION
    media_id: str
    filename: str
    relative_path: str
    media_kind: str
    mime_type: str
    extension: str
    sha256: str
    size_bytes: int
    message_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    sender: Optional[str] = None
    date: Optional[str] = None  # YYYY-MM-DD
    dedupe_group_id: Optional[str] = None
    exists_on_disk: bool = True


class ImageAnalysisRecord(BaseModel):
    schema_version: str = SCHEMA_VERSION
    analysis_id: str
    media_id: str
    filename: str
    model_name: str
    prompt_version: str
    caption: str = ""
    short_caption: str = ""
    category: str = "other"
    subcategory: str = ""
    ocr_text: str = ""
    people_count_estimate: int = 0
    contains_screenshot: bool = False
    contains_document_like_layout: bool = False
    contains_meme: bool = False
    tags: list[str] = Field(default_factory=list)
    aesthetic_score: float = 0.5
    narrative_relevance_score: float = 0.5
    technical_quality_score: float = 0.5
    confidence: float = 0.5
    warnings: list[str] = Field(default_factory=list)


class VideoFrameAnalysis(BaseModel):
    """Analysis of a single extracted video frame."""
    timestamp_sec: float
    caption: str = ""
    short_caption: str = ""
    category: str = "other"
    people_count_estimate: int = 0
    contains_meme: bool = False
    tags: list[str] = Field(default_factory=list)
    aesthetic_score: float = 0.5
    confidence: float = 0.5


class VideoAnalysisRecord(BaseModel):
    schema_version: str = SCHEMA_VERSION
    analysis_id: str
    media_id: str
    filename: str
    model_name: str
    duration_seconds: float = 0.0
    frame_count: int = 0
    frames: list[VideoFrameAnalysis] = Field(default_factory=list)
    # Aggregated description from all frames
    caption: str = ""
    short_caption: str = ""
    # Audio track
    audio_transcript: str = ""
    audio_language: str = ""
    # Combined narrative: frames + audio
    narrative: str = ""
    tags: list[str] = Field(default_factory=list)
    people_count_estimate: int = 0
    narrative_relevance_score: float = 0.5
    confidence: float = 0.5
    warnings: list[str] = Field(default_factory=list)


class VoiceTranscriptRecord(BaseModel):
    schema_version: str = SCHEMA_VERSION
    transcript_id: str
    media_id: str
    filename: str
    model_name: str
    duration_seconds: float = 0.0
    language: Optional[str] = None
    transcript: str = ""
    short_summary: str = ""
    confidence: float = 0.5
    warnings: list[str] = Field(default_factory=list)
