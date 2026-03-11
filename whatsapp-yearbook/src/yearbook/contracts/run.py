from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from yearbook.constants import SCHEMA_VERSION


class RunManifest(BaseModel):
    schema_version: str = SCHEMA_VERSION
    run_id: str
    project_name: str = "whatsapp_yearbook"
    created_at: datetime = Field(default_factory=datetime.now)
    input_chat_path: str
    input_media_dir: str
    config_snapshot: dict[str, Any] = Field(default_factory=dict)
    completed_stages: list[str] = Field(default_factory=list)


class InputInventory(BaseModel):
    schema_version: str = SCHEMA_VERSION
    run_id: str
    chat_file_hash: str
    chat_file_size_bytes: int
    media_files_count: int
    media_files: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
