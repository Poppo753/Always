from __future__ import annotations

import logging
from datetime import datetime

from yearbook.contracts.run import RunManifest
from yearbook.ingestion.input_validator import InputValidator
from yearbook.ingestion.inventory_builder import InventoryBuilder
from yearbook.pipeline.state import PipelineState
from yearbook.storage.manifest_store import ManifestStore

logger = logging.getLogger(__name__)


def run_bootstrap(state: PipelineState) -> None:
    """Pipeline A — validate input and create run manifest and inventory."""
    config = state.config
    paths = state.paths

    # Validate input
    validator = InputValidator(state)
    validator.validate()

    # Create or update run manifest
    if not state.manifest_store.exists():
        manifest = RunManifest(
            run_id=paths.run_id,
            input_chat_path=str(paths.chat_file.relative_to(paths.root)),
            input_media_dir=str(paths.media_dir.relative_to(paths.root)),
            config_snapshot={
                "model_image": config.get("models", {}).get("image", ""),
                "model_audio": config.get("models", {}).get("audio", ""),
                "model_reasoning": config.get("models", {}).get("reasoning", ""),
                "year_target": config.get("year_target", 2025),
            },
        )
        state.manifest_store.write(manifest)
        logger.info("Run manifest created: %s", paths.run_manifest)
    else:
        logger.info("Run manifest already exists, updating.")

    # Build inventory
    builder = InventoryBuilder(state)
    builder.build(warnings=validator.warnings)
