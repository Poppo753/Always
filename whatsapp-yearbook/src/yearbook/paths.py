from __future__ import annotations

from pathlib import Path


class ProjectPaths:
    """Resolves all filesystem paths for a yearbook project run."""

    def __init__(self, project_root: Path, run_id: str) -> None:
        self.root = project_root
        self.run_id = run_id

        # Input
        self.input_dir = project_root / "input"
        self.chat_file = self.input_dir / "_chat.txt"
        self.media_dir = self.input_dir / "media"

        # Run artifacts
        self.run_dir = project_root / "runs" / run_id
        self.run_manifest = self.run_dir / "run_manifest.json"
        self.input_inventory = self.run_dir / "input_inventory.json"
        self.messages_raw = self.run_dir / "messages_raw.jsonl"
        self.messages_normalized = self.run_dir / "messages_normalized.parquet"
        self.media_registry = self.run_dir / "media_registry.json"
        self.image_analysis = self.run_dir / "image_analysis.jsonl"
        self.video_analysis = self.run_dir / "video_analysis.jsonl"
        self.voice_transcripts = self.run_dir / "voice_transcripts.jsonl"
        self.events = self.run_dir / "events.jsonl"
        self.ranked_day_assets = self.run_dir / "ranked_day_assets.jsonl"
        self.run_report = self.run_dir / "run_report.json"

        # Per-day subdirs
        self.daily_contexts_dir = self.run_dir / "daily_contexts"
        self.daily_reasoning_dir = self.run_dir / "daily_reasoning"
        self.daily_summaries_dir = self.run_dir / "daily_summaries"

        # Cache
        self.cache_dir = project_root / "cache"
        self.cache_images = self.cache_dir / "images"
        self.cache_video = self.cache_dir / "video"
        self.cache_video_frames = self.cache_dir / "video_frames"
        self.cache_audio = self.cache_dir / "audio"
        self.cache_reasoning = self.cache_dir / "reasoning"
        self.cache_summaries = self.cache_dir / "summaries"

        # Output
        self.output_dir = project_root / "output"
        self.pptx_output = self.output_dir / f"yearbook_{run_id}.pptx"

        # Logs
        self.logs_dir = project_root / "logs"
        self.log_file = self.logs_dir / f"{run_id}.log"

    def ensure_run_dirs(self) -> None:
        """Create all run-specific directories."""
        for d in [
            self.run_dir,
            self.daily_contexts_dir,
            self.daily_reasoning_dir,
            self.daily_summaries_dir,
            self.output_dir,
            self.logs_dir,
            self.cache_images,
            self.cache_video,
            self.cache_video_frames,
            self.cache_audio,
            self.cache_reasoning,
            self.cache_summaries,
        ]:
            d.mkdir(parents=True, exist_ok=True)

    def daily_context_path(self, date_str: str) -> Path:
        return self.daily_contexts_dir / f"{date_str}.json"

    def daily_reasoning_path(self, date_str: str) -> Path:
        return self.daily_reasoning_dir / f"{date_str}.json"

    def daily_summary_path(self, date_str: str) -> Path:
        return self.daily_summaries_dir / f"{date_str}.json"
