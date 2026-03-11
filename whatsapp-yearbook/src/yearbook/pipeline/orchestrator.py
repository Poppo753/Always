from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from yearbook.constants import PIPELINE_STAGES, STAGE_BOOTSTRAP, STAGE_PARSE, STAGE_MEDIA_REGISTRY
from yearbook.constants import STAGE_IMAGE_ANALYSIS, STAGE_VIDEO_ANALYSIS, STAGE_VOICE_TRANSCRIPTION, STAGE_DAY_GROUPING
from yearbook.constants import STAGE_EVENT_DETECTION, STAGE_RANKING, STAGE_CONTEXT_BUILD
from yearbook.constants import STAGE_REASONING, STAGE_SUMMARIZE, STAGE_RENDER
from yearbook.paths import ProjectPaths
from yearbook.pipeline.state import PipelineState
from yearbook.storage.manifest_store import ManifestStore
from yearbook.config.loader import load_config
from yearbook.logging_config import setup_logging

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Runs the full yearbook generation pipeline, stage by stage."""

    def __init__(self, project_root: Path, run_id: str, force_rerun: bool = False) -> None:
        self.project_root = project_root
        self.run_id = run_id
        self.config = load_config(project_root)
        self.paths = ProjectPaths(project_root, run_id)
        self.paths.ensure_run_dirs()

        setup_logging(log_file=self.paths.log_file)

        self.manifest_store = ManifestStore(self.paths.run_manifest)
        self.state = PipelineState(
            paths=self.paths,
            config=self.config,
            manifest_store=self.manifest_store,
            force_rerun=force_rerun,
        )

    def run_all(self) -> None:
        logger.info("Starting pipeline run: %s", self.run_id)
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            TimeElapsedColumn(),
        ) as progress:
            task = progress.add_task("Pipeline", total=len(PIPELINE_STAGES))
            for stage in PIPELINE_STAGES:
                progress.update(task, description=f"[{stage}]")
                self.run_stage(stage)
                progress.advance(task)

        logger.info("Pipeline completed: %s", self.run_id)

    def run_stage(self, stage: str) -> None:
        if self.state.should_skip(stage):
            logger.info("Skipping completed stage: %s", stage)
            return

        logger.info("Running stage: %s", stage)
        try:
            handler = self._get_stage_handler(stage)
            handler(self.state)
            self.state.mark_done(stage)
            logger.info("Stage completed: %s", stage)
        except Exception as e:
            logger.error("Stage %s failed: %s", stage, e)
            if not self.config.get("pipeline", {}).get("resume_on_error", True):
                raise

    def resume_from(self, stage: str) -> None:
        idx = PIPELINE_STAGES.index(stage)
        for s in PIPELINE_STAGES[idx:]:
            self.run_stage(s)

    def _get_stage_handler(self, stage: str):
        from yearbook.ingestion.bootstrap import run_bootstrap
        from yearbook.parsing.message_normalizer import run_parse
        from yearbook.media.registry_builder import run_media_registry
        from yearbook.media.image_analyzer import run_image_analysis
        from yearbook.media.video_analyzer import run_video_analysis
        from yearbook.media.voice_transcriber import run_voice_transcription
        from yearbook.contexts.day_grouper import run_day_grouping
        from yearbook.events.event_detector import run_event_detection
        from yearbook.ranking.day_asset_ranker import run_ranking
        from yearbook.contexts.context_builder import run_context_build
        from yearbook.reasoning.day_reasoner import run_reasoning
        from yearbook.summaries.narrative_generator import run_summarize
        from yearbook.render.pptx_renderer import run_render

        handlers = {
            STAGE_BOOTSTRAP: run_bootstrap,
            STAGE_PARSE: run_parse,
            STAGE_MEDIA_REGISTRY: run_media_registry,
            STAGE_IMAGE_ANALYSIS: run_image_analysis,
            STAGE_VIDEO_ANALYSIS: run_video_analysis,
            STAGE_VOICE_TRANSCRIPTION: run_voice_transcription,
            STAGE_DAY_GROUPING: run_day_grouping,
            STAGE_EVENT_DETECTION: run_event_detection,
            STAGE_RANKING: run_ranking,
            STAGE_CONTEXT_BUILD: run_context_build,
            STAGE_REASONING: run_reasoning,
            STAGE_SUMMARIZE: run_summarize,
            STAGE_RENDER: run_render,
        }
        if stage not in handlers:
            raise ValueError(f"Unknown stage: {stage}")
        return handlers[stage]
