from __future__ import annotations

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from yearbook.contracts.media import ImageAnalysisRecord, MediaRegistryRecord, VideoAnalysisRecord, VoiceTranscriptRecord
from yearbook.contracts.messages import MessageRecord
from yearbook.pipeline.state import PipelineState
from yearbook.storage.jsonl_store import JsonlStore

logger = logging.getLogger(__name__)


@dataclass
class DayBundle:
    """All raw data for a single day, ready for further processing."""
    date: str  # YYYY-MM-DD
    messages: list[MessageRecord] = field(default_factory=list)
    media_records: list[MediaRegistryRecord] = field(default_factory=list)
    image_analyses: list[ImageAnalysisRecord] = field(default_factory=list)
    video_analyses: list[VideoAnalysisRecord] = field(default_factory=list)
    voice_transcripts: list[VoiceTranscriptRecord] = field(default_factory=list)


class DayGrouper:
    def __init__(self, year_target: int | None) -> None:
        self.year_target = year_target

    def group(
        self,
        messages: list[MessageRecord],
        registry: dict[str, MediaRegistryRecord],
        image_analyses: list[ImageAnalysisRecord],
        video_analyses: list[VideoAnalysisRecord],
        voice_transcripts: list[VoiceTranscriptRecord],
    ) -> list[DayBundle]:
        # Filter to target year only if year_target is set
        if self.year_target:
            year_msgs = [m for m in messages if m.timestamp and m.timestamp.year == self.year_target]
        else:
            year_msgs = [m for m in messages if m.timestamp]

        # Build lookup tables
        img_by_media_id = {r.media_id: r for r in image_analyses}
        vid_by_media_id = {r.media_id: r for r in video_analyses}
        voice_by_media_id = {r.media_id: r for r in voice_transcripts}
        media_by_message_id: dict[str, list[MediaRegistryRecord]] = defaultdict(list)
        for rec in registry.values():
            if rec.message_id:
                media_by_message_id[rec.message_id].append(rec)

        # Group messages by date
        by_date: dict[str, list[MessageRecord]] = defaultdict(list)
        for msg in year_msgs:
            by_date[msg.date].append(msg)

        bundles = []
        for date_str in sorted(by_date.keys()):
            day_messages = by_date[date_str]
            day_media: list[MediaRegistryRecord] = []
            day_images: list[ImageAnalysisRecord] = []
            day_videos: list[VideoAnalysisRecord] = []
            day_voices: list[VoiceTranscriptRecord] = []

            for msg in day_messages:
                for media_rec in media_by_message_id.get(msg.message_id, []):
                    day_media.append(media_rec)
                    if media_rec.media_id in img_by_media_id:
                        day_images.append(img_by_media_id[media_rec.media_id])
                    if media_rec.media_id in vid_by_media_id:
                        day_videos.append(vid_by_media_id[media_rec.media_id])
                    if media_rec.media_id in voice_by_media_id:
                        day_voices.append(voice_by_media_id[media_rec.media_id])

            bundles.append(DayBundle(
                date=date_str,
                messages=day_messages,
                media_records=day_media,
                image_analyses=day_images,
                video_analyses=day_videos,
                voice_transcripts=day_voices,
            ))

        logger.info(
            "Grouped %d messages into %d days (year_target=%s)",
            len(year_msgs),
            len(bundles),
            self.year_target,
        )
        return bundles


def run_day_grouping(state: PipelineState) -> None:
    """Group messages and media by day."""
    paths = state.paths
    config = state.config
    year_target = config.get("year_target", 2025)

    messages = JsonlStore(paths.messages_raw).read_all(MessageRecord)
    registry = _load_registry(paths)
    image_analyses = JsonlStore(paths.image_analysis).read_all(ImageAnalysisRecord) if paths.image_analysis.exists() else []
    video_analyses = JsonlStore(paths.video_analysis).read_all(VideoAnalysisRecord) if paths.video_analysis.exists() else []
    voice_transcripts = JsonlStore(paths.voice_transcripts).read_all(VoiceTranscriptRecord) if paths.voice_transcripts.exists() else []

    grouper = DayGrouper(year_target=year_target)
    bundles = grouper.group(messages, registry, image_analyses, video_analyses, voice_transcripts)

    # Persist day bundles as individual JSON files for later stages
    paths.daily_contexts_dir.mkdir(parents=True, exist_ok=True)
    for bundle in bundles:
        bundle_path = paths.run_dir / "day_bundles" / f"{bundle.date}.json"
        bundle_path.parent.mkdir(parents=True, exist_ok=True)
        bundle_data = {
            "date": bundle.date,
            "message_count": len(bundle.messages),
            "message_ids": [m.message_id for m in bundle.messages],
            "media_ids": [r.media_id for r in bundle.media_records],
            "image_analysis_ids": [i.analysis_id for i in bundle.image_analyses],
            "video_analysis_ids": [v.analysis_id for v in bundle.video_analyses],
            "voice_transcript_ids": [v.transcript_id for v in bundle.voice_transcripts],
        }
        bundle_path.write_text(json.dumps(bundle_data, indent=2), encoding="utf-8")

    logger.info("Day grouping complete: %d days", len(bundles))

    # Store bundles to state for next stages
    state._day_bundles = bundles  # type: ignore[attr-defined]


def _load_registry(paths) -> dict[str, MediaRegistryRecord]:
    if not paths.media_registry.exists():
        return {}
    data = json.loads(paths.media_registry.read_text(encoding="utf-8"))
    return {k: MediaRegistryRecord.model_validate(v) for k, v in data.items()}
