from __future__ import annotations

import re


# Emotion keywords (multilingual)
EMOTION_PATTERNS = re.compile(
    r"mi manchi|ti amo|non vedo l'ora|bellissim[ao]|miss you|love you|can't wait|amazing|"
    r"fantastic[ao]|gorgeous|wonderful|incredibil[ei]|❤️|😍|🥹|😘|💕|💞|💓",
    re.IGNORECASE,
)

PLANNING_PATTERNS = re.compile(
    r"\bandiamo\b|\bvediamoci\b|\bstasera\b|\bdomani\b|\bprenoto\b|\bpranzo\b|\bcena\b|"
    r"\btonight\b|\btomorrow\b|\blet'?s\b|\bmeet\b|\bbook\b|\breserve\b|\bplan\b",
    re.IGNORECASE,
)

NARRATIVE_PATTERNS = re.compile(
    r"successo|indovina|ti racconto|non ci crederai|guess what|you won't believe|"
    r"something happened|hai sentito|listen to this",
    re.IGNORECASE,
)


def count_words(text: str) -> int:
    return len(text.split())


def has_emotion_signal(text: str) -> bool:
    return bool(EMOTION_PATTERNS.search(text))


def has_planning_signal(text: str) -> bool:
    return bool(PLANNING_PATTERNS.search(text))


def has_narrative_signal(text: str) -> bool:
    return bool(NARRATIVE_PATTERNS.search(text))


def is_noise_candidate(text: str) -> bool:
    """Return True if a message is likely noise (no informational value)."""
    wc = count_words(text)
    if wc >= 3:
        return False
    # Short but has meaningful emoji or signal
    if has_emotion_signal(text):
        return False
    return True


def is_quote_candidate(text: str) -> bool:
    """Return True if a message is a good quote candidate."""
    wc = count_words(text)
    if not (5 <= wc <= 20):
        return False
    if not has_emotion_signal(text) and not has_narrative_signal(text):
        return False
    # Avoid purely logistical
    if has_planning_signal(text) and not has_emotion_signal(text):
        return False
    return True


def truncate_text(text: str, max_chars: int = 200) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "…"
