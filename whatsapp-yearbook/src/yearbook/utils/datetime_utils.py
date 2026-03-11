from __future__ import annotations

from datetime import datetime, date
from typing import Optional


def parse_whatsapp_timestamp(raw: str, fmt: str = "%d/%m/%y, %H:%M") -> Optional[datetime]:
    """Parse a WhatsApp timestamp string into a datetime."""
    try:
        return datetime.strptime(raw.strip(), fmt)
    except ValueError:
        return None


def date_to_str(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def datetime_to_str(dt: datetime) -> str:
    return dt.isoformat()
