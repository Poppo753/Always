from __future__ import annotations

import json
import logging
from collections import defaultdict

from yearbook.contracts.events import EventRecord
from yearbook.contracts.media import ImageAnalysisRecord, MediaRegistryRecord, VideoAnalysisRecord, VoiceTranscriptRecord
from yearbook.contracts.messages import MessageRecord
from yearbook.contracts.ranking import RankedDayAssets, CandidateQuote, ScoredEvent, ScoredImage, ScoredMessage, ScoredVoice
from yearbook.contracts.reasoning import DailyContext, DayStats
from yearbook.pipeline.state import PipelineState
from yearbook.storage.jsonl_store import JsonlStore
from yearbook.utils.text_utils import is_quote_candidate

logger = logging.getLogger(__name__)


class DailyContextBuilder:
    """Builds a compact, LLM-ready context for a single day."""

    def build(
        self,
        date: str,
        messages_by_id: dict[str, MessageRecord],
        events_by_id: dict[str, EventRecord],
        imgs_by_id: dict[str, ImageAnalysisRecord],
        videos_by_id: dict[str, VideoAnalysisRecord],
        voices_by_id: dict[str, VoiceTranscriptRecord],
        ranked: RankedDayAssets,
        all_day_messages: list[MessageRecord],
    ) -> DailyContext:
        # Stats
        img_count = sum(1 for m in all_day_messages if m.message_type == "image")
        voice_count = sum(1 for m in all_day_messages if m.message_type == "voice")
        video_count = sum(1 for m in all_day_messages if m.message_type == "video")

        stats = DayStats(
            message_count=len(all_day_messages),
            image_count=img_count,
            voice_count=voice_count,
            video_count=video_count,
        )

        # Top messages
        top_messages: list[ScoredMessage] = []
        for msg_id in ranked.top_message_ids:
            msg = messages_by_id.get(msg_id)
            if msg and msg.text:
                top_messages.append(ScoredMessage(
                    message_id=msg.message_id,
                    sender=msg.sender,
                    timestamp=msg.timestamp.isoformat(),
                    text=msg.text,
                    score=0.7,
                ))

        # Top events
        top_events: list[ScoredEvent] = []
        for evt_id in ranked.top_event_ids:
            evt = events_by_id.get(evt_id)
            if evt:
                top_events.append(ScoredEvent(
                    event_id=evt.event_id,
                    event_type=evt.event_type,
                    description=evt.description,
                    score=evt.score,
                ))

        # Top images
        top_images: list[ScoredImage] = []
        for media_id in ranked.top_image_media_ids:
            img = imgs_by_id.get(media_id)
            if img:
                top_images.append(ScoredImage(
                    media_id=media_id,
                    filename=img.filename,
                    caption=img.caption or img.short_caption,
                    score=img.narrative_relevance_score,
                ))

        # Top videos
        top_videos: list[dict] = []
        for media_id, vid in videos_by_id.items():
            if vid.narrative:
                top_videos.append({
                    'media_id': media_id,
                    'filename': vid.filename,
                    'narrative': vid.narrative,
                    'duration_seconds': vid.duration_seconds,
                    'audio_transcript': vid.audio_transcript,
                })

        # Top voices
        top_voices: list[ScoredVoice] = []
        for media_id in ranked.top_voice_media_ids:
            voice = voices_by_id.get(media_id)
            if voice:
                top_voices.append(ScoredVoice(
                    media_id=media_id,
                    short_summary=voice.short_summary or voice.transcript[:80],
                    score=voice.confidence,
                ))

        # Candidate quotes (from top messages meeting quote criteria)
        candidate_quotes: list[CandidateQuote] = []
        for sm in top_messages:
            if is_quote_candidate(sm.text):
                candidate_quotes.append(CandidateQuote(
                    message_id=sm.message_id,
                    text=sm.text,
                    score=sm.score,
                ))
        candidate_quotes = candidate_quotes[:3]

        return DailyContext(
            date=date,
            stats=stats,
            top_messages=top_messages,
            top_events=top_events,
            top_images=top_images,
            top_videos=top_videos,
            top_voice_transcripts=top_voices,
            candidate_quotes=candidate_quotes,
        )

    def to_text(self, ctx: DailyContext) -> str:
        """Render a DailyContext as compact LLM-ready text (~600-1200 tokens)."""
        lines = [f"DATE: {ctx.date}", ""]
        lines.append(f"DAY STATS: {ctx.stats.message_count} messages, "
                     f"{ctx.stats.image_count} images, {ctx.stats.voice_count} voices")
        lines.append("")

        if ctx.top_events:
            lines.append("TOP EVENTS:")
            for e in ctx.top_events:
                lines.append(f"  [{e.event_type}] {e.description}")
            lines.append("")

        if ctx.top_messages:
            lines.append("CONVERSATION:")
            # Group top messages into a readable format
            for msg in ctx.top_messages[:15]:
                lines.append(f"  {msg.sender}: {msg.text[:120]}")
            lines.append("")

        if ctx.top_images:
            lines.append("TOP IMAGES:")
            for img in ctx.top_images:
                lines.append(f"  - {img.caption}")
            lines.append("")

        if ctx.top_videos:
            lines.append("VIDEOS:")
            for vid in ctx.top_videos:
                dur = f"{vid['duration_seconds']:.0f}s"
                lines.append(f"  [{dur}] {vid['narrative'][:200]}")
            lines.append("")

        if ctx.top_voice_transcripts:
            lines.append("VOICE MESSAGES:")
            for v in ctx.top_voice_transcripts:
                lines.append(f"  - {v.short_summary}")
            lines.append("")

        if ctx.candidate_quotes:
            lines.append("CANDIDATE QUOTES:")
            for q in ctx.candidate_quotes:
                lines.append(f'  "{q.text}" (id: {q.message_id})')

        return "\n".join(lines)


def run_context_build(state: PipelineState) -> None:
    """Build daily context JSON for every day."""
    paths = state.paths

    # Load all data
    messages = JsonlStore(paths.messages_raw).read_all(MessageRecord)
    events = JsonlStore(paths.events).read_all(EventRecord) if paths.events.exists() else []
    images = JsonlStore(paths.image_analysis).read_all(ImageAnalysisRecord) if paths.image_analysis.exists() else []
    videos = JsonlStore(paths.video_analysis).read_all(VideoAnalysisRecord) if paths.video_analysis.exists() else []
    voices = JsonlStore(paths.voice_transcripts).read_all(VoiceTranscriptRecord) if paths.voice_transcripts.exists() else []
    ranked_list = JsonlStore(paths.ranked_day_assets).read_all(RankedDayAssets) if paths.ranked_day_assets.exists() else []

    # Build lookup dicts
    msgs_by_id = {m.message_id: m for m in messages}
    events_by_id = {e.event_id: e for e in events}
    imgs_by_id = {i.media_id: i for i in images}
    videos_by_id = {v.media_id: v for v in videos}
    voices_by_id = {v.media_id: v for v in voices}
    ranked_by_date = {r.date: r for r in ranked_list}

    # Group messages by date
    msgs_by_date: dict[str, list[MessageRecord]] = defaultdict(list)
    for m in messages:
        msgs_by_date[m.date].append(m)

    builder = DailyContextBuilder()
    paths.daily_contexts_dir.mkdir(parents=True, exist_ok=True)
    count = 0

    for date_str, ranked in sorted(ranked_by_date.items()):
        ctx = builder.build(
            date=date_str,
            messages_by_id=msgs_by_id,
            events_by_id=events_by_id,
            imgs_by_id=imgs_by_id,
            videos_by_id=videos_by_id,
            voices_by_id=voices_by_id,
            ranked=ranked,
            all_day_messages=msgs_by_date.get(date_str, []),
        )
        out_path = paths.daily_context_path(date_str)
        out_path.write_text(ctx.model_dump_json(indent=2), encoding="utf-8")
        count += 1

    logger.info("Context build complete: %d daily contexts saved", count)
