from __future__ import annotations

SCHEMA_VERSION = "1.0"

# Message types
MSG_TEXT = "text"
MSG_IMAGE = "image"
MSG_VIDEO = "video"
MSG_VOICE = "voice"
MSG_DOCUMENT = "document"
MSG_STICKER = "sticker"
MSG_SYSTEM = "system"
MSG_UNKNOWN = "unknown"

# Media kinds
MEDIA_IMAGE = "image"
MEDIA_VIDEO = "video"
MEDIA_VOICE = "voice"
MEDIA_DOCUMENT = "document"
MEDIA_STICKER = "sticker"

MEDIA_EXTENSIONS: dict[str, str] = {
    ".jpg": MEDIA_IMAGE,
    ".jpeg": MEDIA_IMAGE,
    ".png": MEDIA_IMAGE,
    ".webp": MEDIA_IMAGE,
    ".gif": MEDIA_IMAGE,
    ".heic": MEDIA_IMAGE,
    ".mp4": MEDIA_VIDEO,
    ".mov": MEDIA_VIDEO,
    ".avi": MEDIA_VIDEO,
    ".opus": MEDIA_VOICE,
    ".ogg": MEDIA_VOICE,
    ".m4a": MEDIA_VOICE,
    ".mp3": MEDIA_VOICE,
    ".aac": MEDIA_VOICE,
    ".pdf": MEDIA_DOCUMENT,
    ".docx": MEDIA_DOCUMENT,
    ".webp": MEDIA_STICKER,
}

# Pipeline stage names
STAGE_BOOTSTRAP = "bootstrap"
STAGE_PARSE = "parse"
STAGE_MEDIA_REGISTRY = "media_registry"
STAGE_IMAGE_ANALYSIS = "image_analysis"
STAGE_VIDEO_ANALYSIS = "video_analysis"
STAGE_VOICE_TRANSCRIPTION = "voice_transcription"
STAGE_DAY_GROUPING = "day_grouping"
STAGE_EVENT_DETECTION = "event_detection"
STAGE_RANKING = "ranking"
STAGE_CONTEXT_BUILD = "context_build"
STAGE_REASONING = "reasoning"
STAGE_SUMMARIZE = "summarize"
STAGE_RENDER = "render"

PIPELINE_STAGES = [
    STAGE_BOOTSTRAP,
    STAGE_PARSE,
    STAGE_MEDIA_REGISTRY,
    STAGE_IMAGE_ANALYSIS,
    STAGE_VIDEO_ANALYSIS,
    STAGE_VOICE_TRANSCRIPTION,
    STAGE_DAY_GROUPING,
    STAGE_EVENT_DETECTION,
    STAGE_RANKING,
    STAGE_CONTEXT_BUILD,
    STAGE_REASONING,
    STAGE_SUMMARIZE,
    STAGE_RENDER,
]

# Artifact filenames
ARTIFACT_RUN_MANIFEST = "run_manifest.json"
ARTIFACT_INPUT_INVENTORY = "input_inventory.json"
ARTIFACT_MESSAGES_RAW = "messages_raw.jsonl"
ARTIFACT_MESSAGES_NORMALIZED = "messages_normalized.parquet"
ARTIFACT_MEDIA_REGISTRY = "media_registry.json"
ARTIFACT_IMAGE_ANALYSIS = "image_analysis.jsonl"
ARTIFACT_VOICE_TRANSCRIPTS = "voice_transcripts.jsonl"
ARTIFACT_EVENTS = "events.jsonl"
ARTIFACT_RANKED_DAY_ASSETS = "ranked_day_assets.jsonl"
ARTIFACT_RUN_REPORT = "run_report.json"

# LLM defaults
GPT_OSS_DEFAULT_MODEL = "gpt-oss:20b"
WHISPER_DEFAULT_MODEL = "large-v3"
QWEN_DEFAULT_MODEL = "Qwen/Qwen2.5-VL-7B-Instruct"

OLLAMA_DEFAULT_URL = "http://localhost:11434"
QWEN_MAX_NEW_TOKENS = 512
