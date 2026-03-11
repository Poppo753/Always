from __future__ import annotations

import json
import logging
from pathlib import Path

from yearbook.ai.whisper_client import WhisperClient
from yearbook.constants import MEDIA_VOICE
from yearbook.contracts.media import VoiceTranscriptRecord, MediaRegistryRecord
from yearbook.pipeline.state import PipelineState
from yearbook.storage.cache_store import CacheStore
from yearbook.storage.jsonl_store import JsonlStore
from yearbook.utils.hashing import cache_key

logger = logging.getLogger(__name__)


class VoiceTranscriber:
    def __init__(self, state: PipelineState) -> None:
        cfg = state.config
        model_name = cfg.get("models", {}).get("audio", "large-v3")
        self.client = WhisperClient(model_name=model_name)
        self.cache = CacheStore(state.paths.cache_audio)
        self.paths = state.paths

    def transcribe(self, record: MediaRegistryRecord) -> VoiceTranscriptRecord:
        audio_path = self.paths.root / record.relative_path
        ck = cache_key(record.sha256, self.client.model_name)
        transcript_id = f"voice_tx_{record.media_id}"

        if self.cache.has(ck):
            logger.debug("Cache hit for voice: %s", record.filename)
            raw = self.cache.get_raw(ck) or {}
        else:
            logger.info("Transcribing voice: %s", record.filename)
            raw = self.client.transcribe(audio_path) or {}
            if raw:
                self.cache.set_raw(ck, raw)

        transcript_text = raw.get("transcript", "")
        # Build a short summary (first 80 chars)
        short_summary = transcript_text[:80].rsplit(" ", 1)[0] if len(transcript_text) > 80 else transcript_text

        return VoiceTranscriptRecord(
            transcript_id=transcript_id,
            media_id=record.media_id,
            filename=record.filename,
            model_name=self.client.model_name,
            duration_seconds=raw.get("duration_seconds", 0.0),
            language=raw.get("language"),
            transcript=transcript_text,
            short_summary=short_summary,
            confidence=raw.get("confidence", 0.5),
        )


def run_voice_transcription(state: PipelineState) -> None:
    """Transcribe all voice messages using Whisper."""
    paths = state.paths

    registry = _load_registry(paths)
    voices = [r for r in registry.values() if r.media_kind == MEDIA_VOICE]
    logger.info("Found %d voice messages to transcribe", len(voices))

    if not voices:
        logger.info("No voice messages to transcribe.")
        return

    transcriber = VoiceTranscriber(state)
    store = JsonlStore(paths.voice_transcripts)
    store.write_all([])

    succeeded = 0
    failed = 0
    for record in voices:
        try:
            result = transcriber.transcribe(record)
        except Exception as e:
            logger.error("Unhandled error transcribing %s: %s — skipping", record.filename, e)
            result = VoiceTranscriptRecord(
                transcript_id=f"voice_tx_{record.media_id}",
                media_id=record.media_id,
                filename=record.filename,
                model_name="error",
                duration_seconds=0.0,
                language=None,
                transcript="",
                short_summary="",
                confidence=0.0,
            )
            failed += 1
        else:
            succeeded += 1
        store.append(result)

    logger.info("Voice transcription complete: %d ok, %d failed", succeeded, failed)


def _load_registry(paths) -> dict[str, MediaRegistryRecord]:
    if not paths.media_registry.exists():
        return {}
    data = json.loads(paths.media_registry.read_text(encoding="utf-8"))
    return {k: MediaRegistryRecord.model_validate(v) for k, v in data.items()}
