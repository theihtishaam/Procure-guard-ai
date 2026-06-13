from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.models import RoomMessage


MENTION_RE = re.compile(r"@([A-Za-z][A-Za-z0-9 &/-]+?)(?=\s{2,}|[,.!?;:]|\n|$)")


@dataclass
class BandRoomSimulator:
    """Local stand-in for Band room semantics: participants, @mentions, and audit trail."""

    room_name: str
    participants: list[str]
    messages: list[RoomMessage] = field(default_factory=list)

    def send(
        self,
        sender: str,
        content: str,
        *,
        message_type: str = "chat",
        payload: dict | None = None,
        mentions: list[str] | None = None,
    ) -> RoomMessage:
        resolved_mentions = mentions or self.extract_mentions(content)
        visible_to = self.route_to(resolved_mentions)
        message = RoomMessage(
            sender=sender,
            content=content,
            mentions=resolved_mentions,
            visible_to=visible_to,
            message_type=message_type,  # type: ignore[arg-type]
            payload=payload or {},
        )
        self.messages.append(message)
        return message

    def extract_mentions(self, content: str) -> list[str]:
        mentions: list[str] = []
        for participant in self.participants:
            token = f"@{participant}"
            if token.lower() in content.lower():
                mentions.append(participant)
        if mentions:
            return mentions
        loose = [match.group(1).strip() for match in MENTION_RE.finditer(content)]
        return [name for name in loose if name in self.participants]

    def route_to(self, mentions: list[str]) -> list[str]:
        return [name for name in mentions if name in self.participants]
