from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from yearbook.constants import PIPELINE_STAGES
from yearbook.pipeline.state import PipelineState

logger = logging.getLogger(__name__)


def build_run_report(state: PipelineState) -> dict[str, Any]:
    """Assemble a summary report of the pipeline run."""
    paths = state.paths
    manifest = state.manifest_store.load()

    summary_files = sorted(paths.daily_summaries_dir.glob("*.json"))
    days_rendered = len(list(paths.daily_summaries_dir.glob("*.json")))

    report = {
        "run_id": paths.run_id,
        "completed_stages": manifest.completed_stages if manifest else [],
        "days_processed": days_rendered,
        "output_pptx": str(paths.pptx_output) if paths.pptx_output.exists() else None,
    }
    return report


def run_report(state: PipelineState) -> None:
    """Build and save the run report (optional post-run step)."""
    report = build_run_report(state)
    out = state.paths.run_report
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    logger.info("Run report saved: %s", out)
