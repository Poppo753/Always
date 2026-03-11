from __future__ import annotations

import logging
from typing import Any

from yearbook.ai.gpt_oss_client import GptOssClient
from yearbook.constants import GPT_OSS_DEFAULT_MODEL, OLLAMA_DEFAULT_URL
from yearbook.contracts.reasoning import DailyReasoning, DailySummary
from yearbook.pipeline.state import PipelineState
from yearbook.storage.cache_store import CacheStore
from yearbook.utils.hashing import sha256_str

logger = logging.getLogger(__name__)

_DEFAULT_NARRATIVE_PROMPT = """Based on the day analysis below, write the yearbook slide content for this day.
The tone should be warm, personal, and evocative — like a love story diary.

Return a JSON object with these exact fields:
{
  "title": "short evocative title for the day (max 8 words)",
  "summary": "2-4 sentence narrative about the day, warm and personal",
  "key_moments": ["moment 1", "moment 2", "moment 3"],
  "quote": "a real memorable phrase from the conversation (or empty string if none available)",
  "mood": "same mood from reasoning"
}
Return ONLY the JSON, no other text.

DAY ANALYSIS:
"""


class NarrativeGenerator:
    def __init__(self, state: PipelineState) -> None:
        cfg = state.config
        model_name = cfg.get("models", {}).get("reasoning", GPT_OSS_DEFAULT_MODEL)
        ollama_url = cfg.get("ollama", {}).get("base_url", OLLAMA_DEFAULT_URL)
        timeout = cfg.get("ollama", {}).get("timeout_seconds", 120)

        self.client = GptOssClient(
            model_name=model_name,
            base_url=ollama_url,
            timeout=timeout,
        )
        self.cache = CacheStore(state.paths.cache_summaries)
        self.prompt_version = "narrative_generation_v1"

        prompts = cfg.get("prompts", {})
        prompt_cfg = prompts.get(self.prompt_version, {})
        self.prompt = prompt_cfg.get("prompt", _DEFAULT_NARRATIVE_PROMPT)

    def generate(self, reasoning: DailyReasoning) -> DailySummary:
        reasoning_text = reasoning.model_dump_json(indent=2)
        ck = sha256_str(reasoning_text + self.prompt_version + self.client.model_name)

        if self.cache.has(ck):
            logger.debug("Cache hit for summary: %s", reasoning.date)
            raw = self.cache.get_raw(ck) or {}
        else:
            logger.info("Generating summary for: %s", reasoning.date)
            raw = self.client.generate_summary(reasoning_text, self.prompt) or {}
            if raw:
                self.cache.set_raw(ck, raw)

        # Validate quote: if the model invented something, drop it
        quote = raw.get("quote", "")
        if not self._is_safe_quote(quote):
            quote = ""

        return DailySummary(
            date=reasoning.date,
            title=raw.get("title", f"Day {reasoning.date}"),
            summary=raw.get("summary", reasoning.reasoning_summary),
            key_moments=raw.get("key_moments", []),
            quote=quote,
            mood=raw.get("mood", reasoning.mood),
            selected_image_media_ids=reasoning.selected_image_media_ids,
            stats={},
            source_evidence=reasoning.evidence,
        )

    def _is_safe_quote(self, quote: str) -> bool:
        """Accept quotes that are non-empty and reasonably short."""
        return bool(quote) and len(quote) <= 200


def run_summarize(state: PipelineState) -> None:
    """Generate narrative summaries from reasoning outputs."""
    paths = state.paths

    reasoning_files = sorted(paths.daily_reasoning_dir.glob("*.json"))
    logger.info("Found %d reasoning files to summarize", len(reasoning_files))

    if not reasoning_files:
        logger.warning("No reasoning files found. Skipping summarize stage.")
        return

    generator = NarrativeGenerator(state)
    paths.daily_summaries_dir.mkdir(parents=True, exist_ok=True)
    count = 0

    for r_path in reasoning_files:
        reasoning = DailyReasoning.model_validate_json(r_path.read_text(encoding="utf-8"))
        summary = generator.generate(reasoning)
        out_path = paths.daily_summary_path(reasoning.date)
        out_path.write_text(summary.model_dump_json(indent=2), encoding="utf-8")
        count += 1

    logger.info("Summarize complete: %d summaries generated", count)
