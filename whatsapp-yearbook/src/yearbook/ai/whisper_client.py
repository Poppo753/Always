from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_whisper_model = None


def _load_whisper(model_name: str):
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model
    import whisper
    logger.info("Loading Whisper model: %s", model_name)
    _whisper_model = whisper.load_model(model_name, device="cuda")
    logger.info("Whisper loaded.")
    return _whisper_model


class WhisperClient:
    """Client for Whisper speech-to-text transcription."""

    def __init__(self, model_name: str = "large-v3") -> None:
        self.model_name = model_name

    def transcribe(self, audio_path: Path) -> Optional[dict]:
        """Transcribe an audio file. Returns dict with transcript, language, duration."""
        try:
            import subprocess
            import os
            import tempfile

            model = _load_whisper(self.model_name)

            # Free GPU memory before inference
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            # Convert opus/ogg to wav using ffmpeg
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name

            cmd = [
                "ffmpeg", "-y", "-i", str(audio_path),
                "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                tmp_path,
            ]
            subprocess.run(cmd, check=True, capture_output=True)

            result = model.transcribe(tmp_path, fp16=torch.cuda.is_available(), condition_on_previous_text=False)
            os.remove(tmp_path)

            # Free GPU memory after inference
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            transcript = result.get("text", "").strip()
            language = result.get("language", "")
            segments = result.get("segments", [])
            duration = segments[-1]["end"] if segments else 0.0

            return {
                "transcript": transcript,
                "language": language,
                "duration_seconds": duration,
                "confidence": 0.8,  # Whisper doesn't expose confidence directly
            }
        except Exception as e:
            logger.error("Whisper transcription failed for %s: %s", audio_path, e)
            return None
