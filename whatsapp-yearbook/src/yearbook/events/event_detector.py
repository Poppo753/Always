from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path

from yearbook.contracts.events import EventRecord
from yearbook.contracts.media import ImageAnalysisRecord, MediaRegistryRecord
from yearbook.contracts.messages import MessageRecord
from yearbook.events.temporal_clusterer import MessageCluster, TemporalClusterer
from yearbook.pipeline.state import PipelineState
from yearbook.storage.jsonl_store import JsonlStore
from yearbook.utils.text_utils import has_emotion_signal, has_planning_signal, has_narrative_signal

logger = logging.getLogger(__name__)

_EVENT_COUNTER = 0


def _next_event_id() -> str:
    global _EVENT_COUNTER
    _EVENT_COUNTER += 1
    return f"evt_{_EVENT_COUNTER:06d}"


class EventDetector:
    def __init__(self, config: dict) -> None:
        gap = config.get("default_events", {}).get(
            "temporal_clustering", {}
        ).get("cluster_gap_minutes", 45)
        self.clusterer = TemporalClusterer(gap_minutes=gap)

    def detect_events(
        self,
        day_messages: list[MessageRecord],
        media_records: list[MediaRegistryRecord],
    ) -> list[EventRecord]:
        if not day_messages:
            return []

        date = day_messages[0].date
        clusters = self.clusterer.cluster(day_messages)
        events: list[EventRecord] = []

        # Build media id set for the day
        media_by_msg: dict[str, list[str]] = {}
        for rec in media_records:
            if rec.message_id:
                media_by_msg.setdefault(rec.message_id, []).append(rec.media_id)

        for cluster in clusters:
            event = self._cluster_to_event(cluster, media_by_msg, date)
            events.append(event)

        return events

    def _cluster_to_event(
        self,
        cluster: MessageCluster,
        media_by_msg: dict[str, list[str]],
        date: str,
    ) -> EventRecord:
        msgs = cluster.messages
        all_text = " ".join(m.text for m in msgs if m.text)

        # Classify
        event_type = "conversation"
        trigger_signals: list[str] = []

        if cluster.has_image:
            trigger_signals.append("image_shared")
            event_type = "image_event"
        if cluster.has_voice:
            trigger_signals.append("voice_shared")
            event_type = "voice_event"
        if has_planning_signal(all_text):
            trigger_signals.append("planning_phrase")
            if event_type == "conversation":
                event_type = "plan_event"
        if has_emotion_signal(all_text):
            trigger_signals.append("emotional_signal")
            if event_type == "conversation":
                event_type = "emotion_event"
        if has_narrative_signal(all_text):
            trigger_signals.append("narrative_signal")

        # Collect media IDs
        media_ids: list[str] = []
        for msg in msgs:
            for mid in media_by_msg.get(msg.message_id, []):
                media_ids.append(mid)

        # Score
        base = 0.5
        if cluster.has_image:
            base += 0.15
        if cluster.has_voice:
            base += 0.12
        if has_emotion_signal(all_text):
            base += 0.10
        if has_planning_signal(all_text):
            base += 0.08
        score = min(base, 1.0)

        ts_start = msgs[0].timestamp if msgs else None
        ts_end = msgs[-1].timestamp if msgs else None

        description = f"Cluster of {len(msgs)} messages" + (
            f" with {sum([cluster.has_image, cluster.has_voice, cluster.has_video])} media types"
            if cluster.has_image or cluster.has_voice else ""
        )

        return EventRecord(
            event_id=_next_event_id(),
            date=date,
            time_start=ts_start,
            time_end=ts_end,
            event_type=event_type,
            confidence=0.75,
            description=description,
            message_ids=[m.message_id for m in msgs],
            media_ids=media_ids,
            trigger_signals=trigger_signals,
            score=score,
        )


def run_event_detection(state: PipelineState) -> None:
    """Detect events in each day's messages."""
    paths = state.paths
    config = state.config

    messages = JsonlStore(paths.messages_raw).read_all(MessageRecord)
    registry = _load_registry(paths)

    # Group messages by date
    from collections import defaultdict
    by_date: dict[str, list[MessageRecord]] = defaultdict(list)
    for msg in messages:
        by_date[msg.date].append(msg)

    # Group registry by date
    reg_by_date: dict[str, list[MediaRegistryRecord]] = defaultdict(list)
    for rec in registry.values():
        if rec.date:
            reg_by_date[rec.date].append(rec)

    detector = EventDetector(config)
    all_events: list[EventRecord] = []

    for date_str, day_msgs in sorted(by_date.items()):
        events = detector.detect_events(day_msgs, reg_by_date.get(date_str, []))
        all_events.extend(events)

    store = JsonlStore(paths.events)
    store.write_all(all_events)
    logger.info("Event detection complete: %d events across %d days", len(all_events), len(by_date))


def _load_registry(paths) -> dict[str, MediaRegistryRecord]:
    if not paths.media_registry.exists():
        return {}
    data = json.loads(paths.media_registry.read_text(encoding="utf-8"))
    return {k: MediaRegistryRecord.model_validate(v) for k, v in data.items()}
