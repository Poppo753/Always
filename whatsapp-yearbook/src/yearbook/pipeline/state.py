from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from yearbook.paths import ProjectPaths
from yearbook.storage.manifest_store import ManifestStore


@dataclass
class PipelineState:
    """Carries live state through the pipeline execution."""

    paths: ProjectPaths
    config: dict[str, Any]
    manifest_store: ManifestStore
    force_rerun: bool = False
    error_log: list[str] = field(default_factory=list)

    def should_skip(self, stage: str) -> bool:
        if self.force_rerun:
            return False
        return self.manifest_store.is_stage_complete(stage)

    def mark_done(self, stage: str) -> None:
        self.manifest_store.mark_stage_complete(stage)
