from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Lazy imports — loaded only once when first called
_model = None
_processor = None


def _load_model(model_name: str) -> tuple:
    global _model, _processor

    if _model is not None:
        return _model, _processor

    from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if device == "cuda" else torch.float32

    logger.info("Loading Qwen2.5-VL model: %s  device=%s  dtype=%s", model_name, device, dtype)
    _model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        model_name,
        torch_dtype=dtype,
        device_map="auto",  # splits across GPU+CPU if model > VRAM
        attn_implementation="sdpa",  # built-in PyTorch SDPA, no flash_attn needed
    )
    _model.eval()
    # Smaller resolution = much faster inference, still enough for captioning
    _processor = AutoProcessor.from_pretrained(
        model_name,
        min_pixels=64 * 28 * 28,
        max_pixels=256 * 28 * 28,
    )
    logger.info("Qwen2.5-VL loaded successfully on %s.", device)
    return _model, _processor


class QwenVLClient:
    """Client for Qwen2.5-VL multimodal perception (caption, OCR, classification)."""

    def __init__(self, model_name: str, max_new_tokens: int = 256) -> None:
        self.model_name = model_name
        self.max_new_tokens = max_new_tokens

    def analyze_image(self, image_path: Path, prompt: str) -> Optional[dict[str, Any]]:
        """Analyze a single image and return structured JSON output."""
        try:
            from PIL import Image
            from qwen_vl_utils import process_vision_info

            model, processor = _load_model(self.model_name)

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": str(image_path)},
                        {"type": "text", "text": prompt},
                    ],
                }
            ]

            text = processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            image_inputs, video_inputs = process_vision_info(messages)
            inputs = processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt",
            )
            import torch
            inputs = inputs.to(model.device)

            with torch.no_grad():
                generated_ids = model.generate(
                    **inputs,
                    max_new_tokens=self.max_new_tokens,
                )

            generated_ids_trimmed = [
                out_ids[len(in_ids):]
                for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            output_text = processor.batch_decode(
                generated_ids_trimmed,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )[0]

            return self._parse_json_output(output_text)

        except Exception as e:
            logger.error("Qwen analysis failed for %s: %s", image_path, e)
            return None

    def _parse_json_output(self, text: str) -> Optional[dict[str, Any]]:
        """Extract JSON from model output, handling markdown code blocks and truncation."""
        text = text.strip()
        # Strip markdown code fences
        m = re.search(r"```(?:json)?\s*(.*?)(\s*```|$)", text, re.DOTALL)
        if m:
            text = m.group(1).strip()
        # Try clean parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # Find the opening brace
        brace_start = text.find("{")
        if brace_start == -1:
            logger.warning("Could not parse JSON from Qwen output: %s", text[:200])
            return None
        json_text = text[brace_start:]
        # Try as-is
        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            pass
        # Truncated JSON — try to recover by extracting what we can field by field
        result = {}
        for key in ("caption", "short_caption", "category", "ocr_text"):
            km = re.search(r'"' + key + r'"\s*:\s*"((?:[^"\\]|\\.)*)"', json_text)
            if km:
                result[key] = km.group(1)
        if result.get("caption"):
            logger.debug("Partial JSON recovery for keys: %s", list(result.keys()))
            return result
        logger.warning("Could not parse JSON from Qwen output: %s", text[:200])
        return None
