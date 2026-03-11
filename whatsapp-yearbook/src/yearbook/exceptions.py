from __future__ import annotations


class YearbookError(Exception):
    """Base exception for all yearbook errors."""


class InputValidationError(YearbookError):
    """Raised when input files or structure are invalid."""


class ParseError(YearbookError):
    """Raised when the WhatsApp chat cannot be parsed."""


class MediaRegistryError(YearbookError):
    """Raised when media indexing fails."""


class ImageAnalysisError(YearbookError):
    """Raised when image analysis fails."""


class TranscriptionError(YearbookError):
    """Raised when voice transcription fails."""


class ReasoningError(YearbookError):
    """Raised when GPT-OSS reasoning fails."""


class SummaryGenerationError(YearbookError):
    """Raised when summary generation fails."""


class RenderingError(YearbookError):
    """Raised when PPTX rendering fails."""


class CacheError(YearbookError):
    """Raised when cache read/write fails."""


class SchemaValidationError(YearbookError):
    """Raised when a data record fails JSON schema validation."""


class StageAlreadyCompletedError(YearbookError):
    """Raised when attempting to re-run a completed pipeline stage without force."""


class ModelNotAvailableError(YearbookError):
    """Raised when a required AI model cannot be loaded or reached."""
