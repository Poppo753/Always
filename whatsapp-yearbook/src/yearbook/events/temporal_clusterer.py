from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Optional

from yearbook.contracts.messages import MessageRecord

logger = logging.getLogger(__name__)


@dataclass
class MessageCluster:
    """A temporal burst of messages."""
    cluster_id: int
    date: str
    messages: list[MessageRecord] = field(default_factory=list)
    has_image: bool = False
    has_voice: bool = False
    has_video: bool = False


class TemporalClusterer:
    """Groups messages into temporal clusters based on inactivity gaps."""

    def __init__(self, gap_minutes: int = 45) -> None:
        self.gap = timedelta(minutes=gap_minutes)

    def cluster(self, messages: list[MessageRecord]) -> list[MessageCluster]:
        if not messages:
            return []

        # Sort by timestamp
        sorted_msgs = sorted(messages, key=lambda m: m.timestamp)
        clusters: list[MessageCluster] = []
        current: Optional[MessageCluster] = None
        cluster_id = 0

        for msg in sorted_msgs:
            if current is None:
                cluster_id += 1
                current = MessageCluster(
                    cluster_id=cluster_id, date=msg.date, messages=[msg]
                )
            else:
                last_ts = current.messages[-1].timestamp
                if msg.timestamp and last_ts and (msg.timestamp - last_ts) > self.gap:
                    clusters.append(current)
                    cluster_id += 1
                    current = MessageCluster(
                        cluster_id=cluster_id, date=msg.date, messages=[msg]
                    )
                else:
                    current.messages.append(msg)

            # Track media presence
            if current and msg.message_type == "image":
                current.has_image = True
            elif current and msg.message_type == "voice":
                current.has_voice = True
            elif current and msg.message_type == "video":
                current.has_video = True

        if current:
            clusters.append(current)

        return clusters
