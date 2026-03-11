from __future__ import annotations

import json
import logging
from collections import defaultdict

from yearbook.contracts.events import EventRecord
from yearbook.contracts.media import ImageAnalysisRecord, MediaRegistryRecord, VoiceTranscriptRecord
from yearbook.contracts.messages import MessageRecord
from yearbook.contracts.ranking import (
    CandidateQuote,
    RankedDayAssets,
    ScoredEvent,
    ScoredImage,
    ScoredMessage,
    ScoredVoice,
    SelectionMetadata,
)
from yearbook.pipeline.state import PipelineState
from yearbook.storage.jsonl_store import JsonlStore
from yearbook.utils.text_utils import (
    count_words,
    has_emotion_signal,
    has_planning_signal,
    has_narrative_signal,
    is_noise_candidate,
    is_quote_candidate,
)

logger = logging.getLogger(__name__)


class MessageRanker:
    def __init__(self, cfg: dict) -> None:
        r = cfg.get("ranking", {}).get("message_scoring", {})
        self.w_semantic = r.get("semantic_score_weight", 0.35)
        self.w_media = r.get("media_proximity_weight", 0.25)
        self.w_len = r.get("message_length_weight", 0.15)
        self.w_reply = r.get("reply_depth_weight", 0.15)
        self.w_emotion = r.get("emotional_signal_weight", 0.10)

        prox = cfg.get("ranking", {}).get("media_proximity_bonuses", {})
        self.img_bonus = prox.get("image_bonus", 0.30)
        self.voice_bonus = prox.get("voice_bonus", 0.25)
        self.video_bonus = prox.get("video_bonus", 0.20)
        self.max_dist = prox.get("max_distance", 2)

    def score(self, msg: MessageRecord, msgs_list: list[MessageRecord]) -> float:
        if is_noise_candidate(msg.text):
            return 0.05

        # Semantic score
        semantic = 0.5
        if has_emotion_signal(msg.text):
            semantic += 0.25
        if has_narrative_signal(msg.text):
            semantic += 0.15
        if has_planning_signal(msg.text):
            semantic += 0.10
        semantic = min(semantic, 1.0)

        # Media proximity
        idx = msgs_list.index(msg)
        media_prox = 0.0
        for dist in range(1, self.max_dist + 1):
            for i in [idx - dist, idx + dist]:
                if 0 <= i < len(msgs_list):
                    neighbor = msgs_list[i]
                    if neighbor.message_type == "image":
                        media_prox = max(media_prox, self.img_bonus * (1 - dist * 0.3))
                    elif neighbor.message_type == "voice":
                        media_prox = max(media_prox, self.voice_bonus * (1 - dist * 0.3))
                    elif neighbor.message_type == "video":
                        media_prox = max(media_prox, self.video_bonus * (1 - dist * 0.3))
        # Bonus if message itself IS media (caption context)
        if msg.message_type in ("image", "voice", "video"):
            media_prox = max(media_prox, self.img_bonus)

        # Length score (normalised at ~50 words)
        wc = count_words(msg.text)
        len_score = min(wc / 50.0, 1.0)

        # Reply score — simple heuristic, real reply detection would need more data
        reply_score = 0.5  # flat

        # Emotion signal
        emo_score = 1.0 if has_emotion_signal(msg.text) else 0.0

        total = (
            semantic * self.w_semantic
            + media_prox * self.w_media
            + len_score * self.w_len
            + reply_score * self.w_reply
            + emo_score * self.w_emotion
        )
        return round(min(total, 1.0), 4)


class DayAssetRanker:
    """Ranks and selects the best assets for a day."""

    def __init__(self, cfg: dict) -> None:
        self.msg_ranker = MessageRanker(cfg)
        limits = cfg.get("ranking", {}).get("top_n_limits", {})
        self.msg_limit = limits.get("messages_per_day", 20)
        self.img_limit = limits.get("images_per_day", 4)
        self.voice_limit = limits.get("voices_per_day", 2)
        self.event_limit = limits.get("events_per_day", 6)
        self.quote_limit = limits.get("candidate_quotes", 3)

        img_cfg = cfg.get("ranking", {}).get("image_scoring", {})
        self.img_w_nar = img_cfg.get("narrative_relevance_weight", 0.50)
        self.img_w_aes = img_cfg.get("aesthetic_score_weight", 0.20)
        self.img_w_evt = img_cfg.get("event_proximity_weight", 0.20)
        self.img_w_clu = img_cfg.get("cluster_weight", 0.10)

    def rank_day(
        self,
        date: str,
        messages: list[MessageRecord],
        events: list[EventRecord],
        images: list[ImageAnalysisRecord],
        voices: list[VoiceTranscriptRecord],
        registry: dict[str, MediaRegistryRecord],
    ) -> RankedDayAssets:
        # Score messages
        non_system = [m for m in messages if not m.is_system]
        scored_msgs = sorted(
            [(m, self.msg_ranker.score(m, non_system)) for m in non_system],
            key=lambda x: -x[1],
        )
        top_msgs = scored_msgs[: self.msg_limit]
        discarded = scored_msgs[self.msg_limit :]

        # Score events
        top_events = sorted(events, key=lambda e: -e.score)[: self.event_limit]

        # Score images
        event_media_ids: set[str] = set()
        for ev in events:
            event_media_ids.update(ev.media_ids)

        scored_imgs = []
        for img in images:
            event_prox = 0.3 if img.media_id in event_media_ids else 0.0
            score = (
                img.narrative_relevance_score * self.img_w_nar
                + img.aesthetic_score * self.img_w_aes
                + event_prox * self.img_w_evt
                + 0.5 * self.img_w_clu  # flat cluster weight for now
            )
            # Penalise memes and low-quality screenshots
            if img.contains_meme:
                score *= 0.5
            scored_imgs.append((img, round(min(score, 1.0), 4)))

        top_imgs = sorted(scored_imgs, key=lambda x: -x[1])[: self.img_limit]

        # Score voices (by duration as proxy — longer = more content)
        scored_voices = sorted(voices, key=lambda v: -v.duration_seconds)[: self.voice_limit]

        # Quote candidates
        quotes: list[tuple[MessageRecord, float]] = []
        for msg, score in scored_msgs:
            if is_quote_candidate(msg.text):
                quotes.append((msg, score))
        top_quotes = quotes[: self.quote_limit]

        return RankedDayAssets(
            date=date,
            top_message_ids=[m.message_id for m, _ in top_msgs],
            top_event_ids=[e.event_id for e in top_events],
            top_image_media_ids=[i.media_id for i, _ in top_imgs],
            top_voice_media_ids=[v.media_id for v in scored_voices],
            discarded_message_ids=[m.message_id for m, _ in discarded],
            selection_metadata=SelectionMetadata(
                message_limit=self.msg_limit,
                image_limit=self.img_limit,
                voice_limit=self.voice_limit,
                event_limit=self.event_limit,
            ),
        )


def run_ranking(state: PipelineState) -> None:
    """Rank and select best assets for each day."""
    paths = state.paths
    config = state.config

    messages = JsonlStore(paths.messages_raw).read_all(MessageRecord)
    events = JsonlStore(paths.events).read_all(EventRecord) if paths.events.exists() else []
    images = JsonlStore(paths.image_analysis).read_all(ImageAnalysisRecord) if paths.image_analysis.exists() else []
    voices = JsonlStore(paths.voice_transcripts).read_all(VoiceTranscriptRecord) if paths.voice_transcripts.exists() else []
    registry = _load_registry(paths)

    # Group by date
    from collections import defaultdict
    msgs_by_date: defaultdict[str, list[MessageRecord]] = defaultdict(list)
    for m in messages:
        msgs_by_date[m.date].append(m)

    events_by_date: defaultdict[str, list[EventRecord]] = defaultdict(list)
    for e in events:
        events_by_date[e.date].append(e)

    imgs_by_date: defaultdict[str, list[ImageAnalysisRecord]] = defaultdict(list)
    for img in images:
        rec = registry.get(img.media_id)
        if rec and rec.date:
            imgs_by_date[rec.date].append(img)

    voices_by_date: defaultdict[str, list[VoiceTranscriptRecord]] = defaultdict(list)
    for v in voices:
        rec = registry.get(v.media_id)
        if rec and rec.date:
            voices_by_date[rec.date].append(v)

    ranker = DayAssetRanker(config)
    ranked: list[RankedDayAssets] = []

    for date_str in sorted(msgs_by_date.keys()):
        result = ranker.rank_day(
            date=date_str,
            messages=msgs_by_date[date_str],
            events=events_by_date.get(date_str, []),
            images=imgs_by_date.get(date_str, []),
            voices=voices_by_date.get(date_str, []),
            registry=registry,
        )
        ranked.append(result)

    JsonlStore(paths.ranked_day_assets).write_all(ranked)
    logger.info("Ranking complete: %d days ranked", len(ranked))


def _load_registry(paths) -> dict[str, MediaRegistryRecord]:
    if not paths.media_registry.exists():
        return {}
    data = json.loads(paths.media_registry.read_text(encoding="utf-8"))
    return {k: MediaRegistryRecord.model_validate(v) for k, v in data.items()}
