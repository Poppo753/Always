from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from yearbook.contracts.run import RunManifest


class ManifestStore:
    """Reads and writes the run_manifest.json for a pipeline run."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def write(self, manifest: RunManifest) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

    def read(self) -> RunManifest:
        return RunManifest.model_validate_json(self.path.read_text(encoding="utf-8"))

    def exists(self) -> bool:
        return self.path.exists()

    def mark_stage_complete(self, stage: str) -> None:
        manifest = self.read()
        if stage not in manifest.completed_stages:
            manifest.completed_stages.append(stage)
        self.write(manifest)

    def is_stage_complete(self, stage: str) -> bool:
        if not self.exists():
            return False
        manifest = self.read()
        return stage in manifest.completed_stages
