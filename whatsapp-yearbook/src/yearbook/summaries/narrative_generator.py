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

_DEFAULT_NARRATIVE_PROMPT = """You are Botta. Write YOUR personal diary about your day with Ana.
Rules:
- FIRST PERSON ONLY. Use "I", "we", "my", "me", "our" in EVERY sentence.
- NEVER third person. NEVER "Botta and Ana", "the pair", "the couple", "their".
- NEVER use "Ana Pau Herrera" or "Ana Pau". Just "Ana".
- Write like you're actually talking, casual and real. No flowery literary prose.
- key_moments: give 2 to 5 bullet points. Vary the number! Not always the same amount.
- quote: MUST start with "Ana: " or "Botta: " followed by the actual words from the chat. If no good quote exists, use empty string "".

GOOD summary:
"Woke up to a voice note from Ana going on about her coworker drama — I was dying laughing. We spent the afternoon planning that lake trip, I'm so hyped. She told me she misses my cooking, and honestly that made my entire day. Also figured out we both hate the same Netflix show."

GOOD key_moments:
["I laughed so hard at her coworker story", "We planned the lake trip for next weekend"]

BAD (NEVER write like this):
"The day unfolded as a tapestry of shared moments. Botta and Ana exchanged playful banter. Their love shone through affectionate gestures."

GOOD quote: "Ana: te extraño mucho bebé 😂"
GOOD quote: "Botta: sei pazza lo sai?"
BAD quote (no speaker): "I love you"

Return ONLY valid JSON:
{"title": "max 5 words", "summary": "3-5 sentences, casual diary", "key_moments": ["2 to 5 items"], "quote": "Speaker: words", "mood": "from reasoning"}"""


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
        ck = sha256_str(reasoning_text + self.prompt + self.client.model_name)

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

        summary_text = self._fix_text(raw.get("summary", reasoning.reasoning_summary))
        title_text = self._fix_text(raw.get("title", f"Day {reasoning.date}"))
        moments = [self._fix_text(m) for m in raw.get("key_moments", [])]

        return DailySummary(
            date=reasoning.date,
            title=title_text,
            summary=summary_text,
            key_moments=moments,
            quote=quote,
            mood=raw.get("mood", reasoning.mood),
            selected_image_media_ids=reasoning.selected_image_media_ids,
            stats={},
            source_evidence=reasoning.evidence,
        )

    @staticmethod
    def _fix_text(text: str) -> str:
        """Post-process LLM output to enforce style rules."""
        import re
        # Fix full name → just Ana
        text = text.replace("Ana Pau Herrera", "Ana")
        text = text.replace("Ana Pau", "Ana")
        # Fix third-person references
        text = re.sub(r"\bBotta and Ana\b", "Ana and I", text)
        text = re.sub(r"\bAna and Botta\b", "we", text)
        text = re.sub(r"\bbetween Botta and Ana\b", "between us", text, flags=re.IGNORECASE)
        text = re.sub(r"\bbetween Ana and Botta\b", "between us", text, flags=re.IGNORECASE)
        # Fix common third-person patterns
        text = re.sub(r"\bThe pair\b", "We", text)
        text = re.sub(r"\bthe pair\b", "we", text)
        text = re.sub(r"\bThe couple\b", "We", text)
        text = re.sub(r"\bthe couple\b", "we", text)
        text = re.sub(r"\bTheir love\b", "Our love", text)
        text = re.sub(r"\btheir love\b", "our love", text)
        text = re.sub(r"\btheir shared\b", "our shared", text, flags=re.IGNORECASE)
        text = re.sub(r"\btheir conversations?\b", "our conversations", text, flags=re.IGNORECASE)
        text = re.sub(r"\bBotta's\b", "my", text)
        return text

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
