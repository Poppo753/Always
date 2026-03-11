from __future__ import annotations

import json
import logging
import subprocess
import tempfile
from pathlib import Path

from yearbook.ai.qwen_vl_client import QwenVLClient
from yearbook.ai.whisper_client import WhisperClient
from yearbook.constants import MEDIA_VIDEO, QWEN_MAX_NEW_TOKENS
from yearbook.contracts.media import MediaRegistryRecord, VideoAnalysisRecord, VideoFrameAnalysis
from yearbook.pipeline.state import PipelineState
from yearbook.storage.cache_store import CacheStore
from yearbook.storage.jsonl_store import JsonlStore
from yearbook.utils.hashing import cache_key

logger = logging.getLogger(__name__)

_FRAME_PROMPT = (
    'Describe this video frame. Return ONLY JSON:\n'
    '{"caption":"...","short_caption":"2-4 words","category":"selfie|food_restaurant|travel_outdoor|screenshot|meme|document|room_interior|pet|people_group|object|other","people_count_estimate":0,"contains_meme":false,"tags":[],"aesthetic_score":0.7,"confidence":0.85}\n'
    'No markdown, no explanation, just JSON.'
)


def _get_duration(video_path: Path) -> float:
    """Return video duration in seconds via ffprobe."""
    try:
        r = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', str(video_path)],
            capture_output=True, text=True, check=True
        )
        info = json.loads(r.stdout)
        return float(next(
            (s['duration'] for s in info.get('streams', []) if 'duration' in s), 0
        ))
    except Exception as e:
        logger.warning("ffprobe failed for %s: %s", video_path, e)
        return 0.0


def _frame_interval(duration_sec: float) -> float:
    """Adaptive frame sampling interval based on video duration."""
    if duration_sec <= 30:
        return 1.0
    elif duration_sec <= 120:
        return 5.0
    elif duration_sec <= 300:
        return 10.0
    else:
        return 30.0


def _extract_frames(video_path: Path, interval: float, duration: float) -> list[tuple[float, Path]]:
    """
    Extract frames at the given interval into temp files.
    Returns list of (timestamp_sec, tmp_path).
    """
    frames: list[tuple[float, Path]] = []
    t = interval / 2.0  # start at midpoint of first interval, not at 0
    while t < duration:
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            tmp = Path(f.name)
        try:
            subprocess.run(
                [
                    'ffmpeg', '-y', '-ss', str(t), '-i', str(video_path),
                    '-vframes', '1', '-q:v', '3', str(tmp)
                ],
                capture_output=True, check=True
            )
            frames.append((t, tmp))
        except Exception as e:
            logger.warning("Frame extract failed at %.1fs for %s: %s", t, video_path.name, e)
            tmp.unlink(missing_ok=True)
        t += interval
    return frames


def _extract_audio(video_path: Path) -> Path | None:
    """Extract audio track to a temp wav file. Returns None if no audio."""
    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            tmp = Path(f.name)
        result = subprocess.run(
            [
                'ffmpeg', '-y', '-i', str(video_path),
                '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', str(tmp)
            ],
            capture_output=True
        )
        # Check if the output file has audio (size > 1KB means real audio)
        if result.returncode == 0 and tmp.stat().st_size > 1024:
            return tmp
        tmp.unlink(missing_ok=True)
        return None
    except Exception as e:
        logger.warning("Audio extraction failed for %s: %s", video_path.name, e)
        return None


def _aggregate_captions(frames: list[VideoFrameAnalysis], audio_transcript: str) -> tuple[str, str]:
    """Build a combined narrative caption from frame descriptions + audio."""
    # Deduplicate very similar short captions
    seen: set[str] = set()
    unique_captions: list[str] = []
    for f in frames:
        key = f.short_caption.lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique_captions.append(f.caption)

    video_desc = '. '.join(unique_captions) if unique_captions else ''

    if audio_transcript and video_desc:
        narrative = f"{video_desc}. Audio: {audio_transcript}"
    elif audio_transcript:
        narrative = f"Audio: {audio_transcript}"
    else:
        narrative = video_desc

    short = frames[0].short_caption if frames else 'video'
    return narrative, short


class VideoAnalyzer:
    def __init__(self, state: PipelineState) -> None:
        cfg = state.config
        model_name = cfg.get('models', {}).get('image', 'Qwen/Qwen2.5-VL-3B-Instruct')
        audio_model = cfg.get('models', {}).get('audio', 'large-v3')
        self.qwen = QwenVLClient(model_name=model_name, max_new_tokens=QWEN_MAX_NEW_TOKENS)
        self.whisper = WhisperClient(model_name=audio_model)
        self.cache = CacheStore(state.paths.cache_video)
        self.thumbs_dir = state.paths.cache_video_frames
        self.thumbs_dir.mkdir(parents=True, exist_ok=True)
        self.root = state.paths.root

    def analyze(self, record: MediaRegistryRecord) -> VideoAnalysisRecord:
        video_path = self.root / record.relative_path
        ck = cache_key(record.sha256, 'video_analysis_v1', self.qwen.model_name)

        if self.cache.has(ck):
            logger.debug('Cache hit for video: %s', record.filename)
            raw = self.cache.get_raw(ck) or {}
            return self._build_record(record, raw)

        if not video_path.exists():
            logger.warning('Video not found: %s', video_path)
            return self._build_record(record, {})

        logger.info('Analyzing video: %s', record.filename)
        raw = self._do_analyze(video_path)
        if raw:
            self.cache.set_raw(ck, raw)
            self._save_thumbnail(record.media_id, video_path, raw)
        return self._build_record(record, raw or {})

    def _save_thumbnail(self, media_id: str, video_path: Path, raw: dict) -> None:
        """Save the best-scoring frame as a permanent JPEG thumbnail."""
        thumb_path = self.thumbs_dir / f"{media_id}_thumb.jpg"
        if thumb_path.exists():
            return
        frames = raw.get('frames', [])
        if not frames:
            return
        best = max(frames, key=lambda f: f.get('aesthetic_score', 0))
        ts = best.get('timestamp_sec', 0)
        try:
            subprocess.run(
                ['ffmpeg', '-y', '-ss', str(ts), '-i', str(video_path),
                 '-vframes', '1', '-q:v', '2', str(thumb_path)],
                capture_output=True, check=True
            )
            logger.info('Saved thumbnail: %s', thumb_path.name)
        except Exception as e:
            logger.warning('Could not save thumbnail for %s: %s', video_path.name, e)

    def _do_analyze(self, video_path: Path) -> dict:
        duration = _get_duration(video_path)
        interval = _frame_interval(duration)
        logger.info('  Duration: %.1fs, sampling every %.0fs', duration, interval)

        # --- Extract and analyze frames ---
        frame_tmp_list = _extract_frames(video_path, interval, duration)
        frame_results: list[dict] = []
        for ts, tmp_path in frame_tmp_list:
            raw_frame = self.qwen.analyze_image(tmp_path, _FRAME_PROMPT)
            tmp_path.unlink(missing_ok=True)
            if raw_frame:
                frame_results.append({'timestamp_sec': ts, **raw_frame})
        logger.info('  Analyzed %d/%d frames', len(frame_results), len(frame_tmp_list))

        # --- Extract and transcribe audio ---
        audio_transcript = ''
        audio_language = ''
        audio_tmp = _extract_audio(video_path)
        if audio_tmp:
            logger.info('  Transcribing audio...')
            tx = self.whisper.transcribe(audio_tmp)
            audio_tmp.unlink(missing_ok=True)
            if tx:
                audio_transcript = tx.get('transcript', '')
                audio_language = tx.get('language', '')
                logger.info('  Audio transcript: %s', audio_transcript[:80])

        return {
            'duration_seconds': duration,
            'frames': frame_results,
            'audio_transcript': audio_transcript,
            'audio_language': audio_language,
        }

    def _build_record(self, record: MediaRegistryRecord, raw: dict) -> VideoAnalysisRecord:
        frames_raw = raw.get('frames', [])
        frames = [
            VideoFrameAnalysis(
                timestamp_sec=f.get('timestamp_sec', 0.0),
                caption=f.get('caption', ''),
                short_caption=f.get('short_caption', ''),
                category=f.get('category', 'other'),
                people_count_estimate=f.get('people_count_estimate', 0),
                contains_meme=f.get('contains_meme', False),
                tags=f.get('tags', []),
                aesthetic_score=float(f.get('aesthetic_score', 0.5)),
                confidence=float(f.get('confidence', 0.5)),
            )
            for f in frames_raw
        ]

        audio_transcript = raw.get('audio_transcript', '')
        narrative, short_caption = _aggregate_captions(frames, audio_transcript)

        all_tags: list[str] = []
        for f in frames:
            all_tags.extend(f.tags)
        # Deduplicate tags preserving order
        seen_tags: set[str] = set()
        unique_tags = [t for t in all_tags if not (t in seen_tags or seen_tags.add(t))]  # type: ignore

        max_people = max((f.people_count_estimate for f in frames), default=0)

        return VideoAnalysisRecord(
            analysis_id=f'vid_analysis_{record.media_id}',
            media_id=record.media_id,
            filename=record.filename,
            model_name=self.qwen.model_name,
            duration_seconds=raw.get('duration_seconds', 0.0),
            frame_count=len(frames),
            frames=frames,
            caption=narrative,
            short_caption=short_caption,
            audio_transcript=audio_transcript,
            audio_language=raw.get('audio_language', ''),
            narrative=narrative,
            tags=unique_tags[:20],
            people_count_estimate=max_people,
            narrative_relevance_score=0.7 if narrative else 0.3,
            confidence=frames[0].confidence if frames else 0.0,
        )


def run_video_analysis(state: PipelineState) -> None:
    """Analyze all videos: extract frames + transcribe audio."""
    paths = state.paths

    registry = _load_registry(paths)
    videos = [r for r in registry.values() if r.media_kind == MEDIA_VIDEO]
    logger.info('Found %d videos to analyze', len(videos))

    if not videos:
        logger.info('No videos to analyze.')
        return

    analyzer = VideoAnalyzer(state)
    store = JsonlStore(paths.video_analysis)
    store.write_all([])

    succeeded = 0
    failed = 0
    for record in videos:
        try:
            result = analyzer.analyze(record)
            succeeded += 1
        except Exception as e:
            logger.error('Unhandled error analyzing video %s: %s — skipping', record.filename, e)
            result = VideoAnalysisRecord(
                analysis_id=f'vid_analysis_{record.media_id}',
                media_id=record.media_id,
                filename=record.filename,
                model_name='error',
            )
            failed += 1
        store.append(result)

    logger.info('Video analysis complete: %d ok, %d failed', succeeded, failed)


def _load_registry(paths) -> dict[str, MediaRegistryRecord]:
    if not paths.media_registry.exists():
        return {}
    data = json.loads(paths.media_registry.read_text(encoding='utf-8'))
    return {k: MediaRegistryRecord.model_validate(v) for k, v in data.items()}
