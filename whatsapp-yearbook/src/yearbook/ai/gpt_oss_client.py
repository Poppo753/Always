from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

import requests

from yearbook.constants import OLLAMA_DEFAULT_URL, GPT_OSS_DEFAULT_MODEL
from yearbook.utils.retry import retry

logger = logging.getLogger(__name__)


class GptOssClient:
    """Client for GPT-OSS-20B via Ollama for reasoning and narrative generation."""

    def __init__(
        self,
        model_name: str = GPT_OSS_DEFAULT_MODEL,
        base_url: str = OLLAMA_DEFAULT_URL,
        timeout: int = 120,
    ) -> None:
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _call(self, prompt: str) -> Optional[str]:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
        }
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "")
        except requests.RequestException as e:
            logger.error("Ollama API error: %s", e)
            raise

    def _call_chat(self, system: str, user: str) -> Optional[str]:
        """Use /api/chat with system + user messages for better instruction following."""
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
        }
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "")
        except requests.RequestException as e:
            logger.error("Ollama chat API error: %s", e)
            raise

    def _call_with_retry(self, prompt: str) -> Optional[str]:
        return retry(self._call, prompt, max_attempts=3, delay=5.0, exceptions=(Exception,))

    def _call_chat_with_retry(self, system: str, user: str) -> Optional[str]:
        return retry(self._call_chat, system, user, max_attempts=3, delay=5.0, exceptions=(Exception,))

    def reason_day(self, daily_context_text: str, prompt_template: str) -> Optional[dict[str, Any]]:
        """Send daily context to GPT-OSS for reasoning. Returns parsed JSON."""
        full_prompt = f"{prompt_template}\n\n---\n\n{daily_context_text}"
        response = self._call_with_retry(full_prompt)
        if not response:
            return None
        return self._parse_json(response)

    def generate_summary(self, reasoning_text: str, prompt_template: str) -> Optional[dict[str, Any]]:
        """Generate narrative summary using chat API for better instruction following."""
        response = self._call_chat_with_retry(prompt_template, reasoning_text)
        if not response:
            return None
        return self._parse_json(response)

    def _parse_json(self, text: str) -> Optional[dict[str, Any]]:
        import re
        text = text.strip()
        m = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if m:
            text = m.group(1)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            m2 = re.search(r"\{.*\}", text, re.DOTALL)
            if m2:
                try:
                    return json.loads(m2.group(0))
                except json.JSONDecodeError:
                    pass
        logger.warning("Could not parse JSON from GPT-OSS output: %.200s", text)
        return None
