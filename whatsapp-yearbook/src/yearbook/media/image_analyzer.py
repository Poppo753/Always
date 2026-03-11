from __future__ import annotations

import json
import logging
from pathlib import Path

from yearbook.ai.qwen_vl_client import QwenVLClient
from yearbook.constants import MEDIA_IMAGE, QWEN_MAX_NEW_TOKENS
from yearbook.contracts.media import ImageAnalysisRecord, MediaRegistryRecord
from yearbook.pipeline.state import PipelineState
from yearbook.storage.cache_store import CacheStore
from yearbook.storage.jsonl_store import JsonlStore
from yearbook.utils.hashing import cache_key

logger = logging.getLogger(__name__)

_DEFAULT_CAPTION_PROMPT = """Describe this image. Return ONLY a JSON object:
{"caption":"detailed description","short_caption":"2-4 words","category":"selfie|food_restaurant|travel_outdoor|screenshot|meme|document|room_interior|pet|people_group|object|other","subcategory":"","ocr_text":"","people_count_estimate":0,"contains_screenshot":false,"contains_meme":false,"tags":[],"aesthetic_score":0.7,"narrative_relevance_score":0.8,"confidence":0.85}
No markdown, no explanation, just JSON."""


class ImageAnalyzer:
    def __init__(self, state: PipelineState) -> None:
        cfg = state.config
        model_name = cfg.get("models", {}).get("image", "Qwen/Qwen2.5-VL-7B-Instruct")
        self.client = QwenVLClient(model_name=model_name, max_new_tokens=QWEN_MAX_NEW_TOKENS)
        self.cache = CacheStore(state.paths.cache_images)
        self.root = state.paths.root
        self.prompt_version = "image_caption_v1"
        # Load prompt from config if available
        prompts = cfg.get("prompts", {})
        prompt_cfg = prompts.get(self.prompt_version, {})
        self.prompt = prompt_cfg.get("prompt", _DEFAULT_CAPTION_PROMPT)

    def analyze(self, record: MediaRegistryRecord) -> ImageAnalysisRecord:
        image_path = self.root / record.relative_path

        ck = cache_key(record.sha256, self.prompt_version, self.client.model_name)

        # Cache hit
        if self.cache.has(ck):
            logger.debug("Cache hit for image: %s", record.filename)
            raw = self.cache.get_raw(ck)
            return self._build_record(record, raw or {})

        if not image_path.exists():
            logger.warning("Image not found: %s", image_path)
            return self._build_record(record, {})

        logger.info("Analyzing image: %s", record.filename)
        raw = self.client.analyze_image(image_path, self.prompt)

        if raw:
            self.cache.set_raw(ck, raw)
        return self._build_record(record, raw or {})

    def _build_record(self, record: MediaRegistryRecord, raw: dict) -> ImageAnalysisRecord:
        analysis_id = f"img_analysis_{record.media_id}"
        return ImageAnalysisRecord(
            analysis_id=analysis_id,
            media_id=record.media_id,
            filename=record.filename,
            model_name=self.client.model_name,
            prompt_version=self.prompt_version,
            caption=raw.get("caption", ""),
            short_caption=raw.get("short_caption", ""),
            category=raw.get("category", "other"),
            subcategory=raw.get("subcategory", ""),
            ocr_text=raw.get("ocr_text", ""),
            people_count_estimate=raw.get("people_count_estimate", 0),
            contains_screenshot=raw.get("contains_screenshot", False),
            contains_document_like_layout=raw.get("contains_document_like_layout", False),
            contains_meme=raw.get("contains_meme", False),
            tags=raw.get("tags", []),
            aesthetic_score=float(raw.get("aesthetic_score", 0.5)),
            narrative_relevance_score=float(raw.get("narrative_relevance_score", 0.5)),
            technical_quality_score=float(raw.get("technical_quality_score", 0.5)),
            confidence=float(raw.get("confidence", 0.5)),
            warnings=raw.get("warnings", []),
        )


def run_image_analysis(state: PipelineState) -> None:
    """Analyze all images using Qwen2.5-VL."""
    paths = state.paths

    registry = _load_registry(paths)
    images = [r for r in registry.values() if r.media_kind in (MEDIA_IMAGE, "sticker")]
    logger.info("Found %d images to analyze", len(images))

    if not images:
        logger.info("No images to analyze.")
        return

    analyzer = ImageAnalyzer(state)
    store = JsonlStore(paths.image_analysis)
    store.write_all([])  # Reset file

    for record in images:
        result = analyzer.analyze(record)
        store.append(result)

    logger.info("Image analysis complete: %d records", len(images))


def _load_registry(paths) -> dict[str, MediaRegistryRecord]:
    if not paths.media_registry.exists():
        return {}
    data = json.loads(paths.media_registry.read_text(encoding="utf-8"))
    return {k: MediaRegistryRecord.model_validate(v) for k, v in data.items()}
