from __future__ import annotations

import logging

from yearbook.ai.gpt_oss_client import GptOssClient
from yearbook.constants import GPT_OSS_DEFAULT_MODEL, OLLAMA_DEFAULT_URL
from yearbook.contracts.reasoning import DailyContext, DailyReasoning
from yearbook.contexts.context_builder import DailyContextBuilder
from yearbook.pipeline.state import PipelineState
from yearbook.storage.cache_store import CacheStore
from yearbook.utils.hashing import sha256_str

logger = logging.getLogger(__name__)

_DEFAULT_REASONING_PROMPT = """You are analyzing a day in a WhatsApp conversation between Botta and Ana (a couple in a long-distance relationship).
Based on the structured context below, identify the main theme, mood, and significance of the day.
Always refer to her as "Ana" (never "Ana Pau Herrera").

Return a JSON object with these exact fields:
{
  "main_theme": "brief description of the day's main theme",
  "day_type": "one of: quiet_day, social_evening, outing, emotional_moment, planning_day, milestone, mixed",
  "importance_level": "one of: low, medium, high",
  "mood": "one of: warm_playful, romantic, nostalgic, cheerful, neutral, tense, melancholy, excited",
  "reasoning_summary": "2-3 sentences explaining what this day was about",
  "evidence": {"message_ids": [], "event_ids": [], "media_ids": []},
  "selected_quote_message_id": null,
  "selected_image_media_ids": []
}
Return ONLY the JSON, no other text.

CONTEXT:
"""


class DayReasoner:
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
        self.cache = CacheStore(state.paths.cache_reasoning)
        self.prompt_version = "day_reasoning_v1"

        prompts = cfg.get("prompts", {})
        prompt_cfg = prompts.get(self.prompt_version, {})
        self.prompt = prompt_cfg.get("prompt", _DEFAULT_REASONING_PROMPT)
        self.ctx_builder = DailyContextBuilder()

    def reason(self, ctx: DailyContext) -> DailyReasoning:
        context_text = self.ctx_builder.to_text(ctx)
        ck = sha256_str(context_text + self.prompt_version + self.client.model_name)

        if self.cache.has(ck):
            logger.debug("Cache hit for reasoning: %s", ctx.date)
            raw = self.cache.get_raw(ck) or {}
        else:
            logger.info("Reasoning day: %s", ctx.date)
            raw = self.client.reason_day(context_text, self.prompt) or {}
            if raw:
                self.cache.set_raw(ck, raw)

        # Coerce evidence IDs to strings (GPT-OSS sometimes returns ints)
        evidence = raw.get("evidence", {})
        if isinstance(evidence, dict):
            evidence = {k: [str(v) for v in vals] if isinstance(vals, list) else vals
                        for k, vals in evidence.items()}

        return DailyReasoning(
            date=ctx.date,
            model_name=self.client.model_name,
            prompt_version=self.prompt_version,
            main_theme=raw.get("main_theme", ""),
            day_type=raw.get("day_type", "quiet_day"),
            importance_level=raw.get("importance_level", "medium"),
            mood=raw.get("mood", "neutral"),
            reasoning_summary=raw.get("reasoning_summary", ""),
            evidence=evidence,
            selected_quote_message_id=str(raw["selected_quote_message_id"]) if raw.get("selected_quote_message_id") is not None else None,
            selected_image_media_ids=[str(x) for x in raw.get("selected_image_media_ids", [])],
        )


def run_reasoning(state: PipelineState) -> None:
    """Run GPT-OSS reasoning for every day."""
    paths = state.paths

    context_files = sorted(paths.daily_contexts_dir.glob("*.json"))
    logger.info("Found %d daily context files to reason over", len(context_files))

    if not context_files:
        logger.warning("No daily context files found. Skipping reasoning stage.")
        return

    reasoner = DayReasoner(state)
    paths.daily_reasoning_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    failed = 0

    for ctx_path in context_files:
        try:
            ctx = DailyContext.model_validate_json(ctx_path.read_text(encoding="utf-8"))
            reasoning = reasoner.reason(ctx)
            out_path = paths.daily_reasoning_path(ctx.date)
            out_path.write_text(reasoning.model_dump_json(indent=2), encoding="utf-8")
            count += 1
        except Exception as exc:
            failed += 1
            logger.error("Reasoning failed for %s: %s", ctx_path.stem, exc)

    logger.info("Reasoning complete: %d ok, %d failed", count, failed)
