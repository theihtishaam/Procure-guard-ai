from __future__ import annotations

"""Unified collaboration session for ProcureGuard.

The workflow talks to ONE interface here, regardless of whether it is running
against the real Band platform or the local simulator. This keeps Band as the
actual coordination layer in live mode while preserving a reliable, fully
offline demo path.

Live mode (BAND_ENABLED=1 + agent_config.yaml present):
  - creates a real Band chat room (Human API)
  - adds every registered agent as a room participant
  - posts routed handoffs as real Band messages (>=1 @mention, real message ids)
  - emits broadcasts/status as real Band events (task type, no mention needed)
  - stores the shared context packet as a real cross-agent Band memory
  - rehydrates room context through the Band Agent API before the decision

Sim mode (default / fallback):
  - uses BandRoomSimulator with identical room + handoff semantics so the
    dashboard and evidence trail always render, even with no credentials.
"""

import logging
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

import yaml

from app.band_client import BandClient, BandError, BandParticipant
from app.band_room import BandRoomSimulator
from app.config import ROOT_DIR, Settings
from app.models import BandEventRecord, BandMemoryRecord, RoomMessage


logger = logging.getLogger("procureguard.band")

CONFIG_PATH = ROOT_DIR / "agent_config.yaml"

# message_type values that are broadcasts/status -> delivered as Band events
EVENT_MESSAGE_TYPES = {"event", "decision", "audit", "approval_gate"}


def load_agent_participants(role_to_name: dict[str, str]) -> dict[str, BandParticipant]:
    """Load per-agent Band credentials from agent_config.yaml, keyed by name."""
    if not CONFIG_PATH.exists():
        return {}
    raw = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    participants: dict[str, BandParticipant] = {}
    for role, name in role_to_name.items():
        entry = raw.get(role)
        if not isinstance(entry, dict):
            continue
        agent_id = str(entry.get("agent_id", "")).strip()
        api_key = str(entry.get("api_key", "")).strip()
        if not agent_id or not api_key or agent_id.startswith("<"):
            continue
        participants[name] = BandParticipant(
            role=role, agent_id=agent_id, api_key=api_key, name=name
        )
    return participants


class BandSession:
    """Routes workflow collaboration through real Band or the local simulator."""

    def __init__(
        self,
        *,
        settings: Settings,
        room_name: str,
        participant_names: list[str],
        role_to_name: dict[str, str],
        subject_key: str,
    ) -> None:
        self.settings = settings
        self.room_name = room_name
        self.participant_names = participant_names
        # Band memory subject_id must be a UUID. Derive a stable UUID5 from the
        # subject key (the vendor) so the same vendor maps to the same Band
        # memory subject across runs -> enables cross-session recall.
        self.subject_key = subject_key
        self.subject_id = str(uuid5(NAMESPACE_URL, f"procureguard:vendor:{subject_key.lower().strip()}"))
        self.messages: list[RoomMessage] = []
        self.events: list[BandEventRecord] = []
        self.memories: list[BandMemoryRecord] = []
        self.recalled_memories: list[dict[str, Any]] = []
        self.room_id: str | None = None
        self.room_url: str | None = None

        self._sim = BandRoomSimulator(room_name=room_name, participants=participant_names)
        self._agents = load_agent_participants(role_to_name)
        self._joined: set[str] = set()  # names confirmed as real room participants
        self._live = bool(settings.band_enabled and settings.band_user_api_key and self._agents)
        self._client: BandClient | None = None
        self._http = None
        self._fallback_reason: str | None = None

        if settings.band_enabled and not self._live:
            self._fallback_reason = self._diagnose_fallback()

    @property
    def mode(self) -> str:
        return "band-live" if self._live else "local-band-sim"

    @property
    def fallback_reason(self) -> str | None:
        return self._fallback_reason

    def _diagnose_fallback(self) -> str:
        if not self.settings.band_user_api_key:
            return "BAND_USER_API_KEY missing; running local Band simulation."
        if not self._agents:
            return "agent_config.yaml has no registered agents; running local Band simulation."
        return "Band live prerequisites incomplete; running local Band simulation."

    def _any_agent(self) -> BandParticipant | None:
        # Prefer an agent Band confirmed is in the room, so events never post
        # from a non-participant.
        for name, participant in self._agents.items():
            if name in self._joined:
                return participant
        return next(iter(self._agents.values()), None)

    async def open(self) -> None:
        """Create the real Band room and add agents, or no-op in sim mode."""
        if not self._live:
            return
        self._client = BandClient(
            base_url=self.settings.band_app_url,
            user_api_key=self.settings.band_user_api_key,
            timeout_seconds=self.settings.aimlapi_timeout_seconds,
        )
        self._http = self._client.client()
        # The Coordinator agent opens the room and recruits its siblings using
        # its OWN agent key (Agent API). This avoids the Enterprise-gated Human
        # API and is truer to Band's "agents recruit each other" model. The
        # opener is implicitly a room participant.
        opener = self._agents.get("Intake Coordinator") or self._any_agent()
        try:
            if opener is None:
                raise BandError("No registered agent available to open the room.")
            self.room_id = await self._client.create_room_as_agent(
                self._http, opener, self.room_name
            )
            self.room_url = f"{self.settings.band_app_url}/chats/{self.room_id}"
            self._joined.add(opener.name)
            for participant in self._agents.values():
                if participant.name == opener.name:
                    continue
                try:
                    await self._client.add_participant_as_agent(
                        self._http, self.room_id, opener, participant.agent_id
                    )
                    self._joined.add(participant.name)
                except BandError as exc:
                    logger.warning("Could not add %s to Band room: %s", participant.name, exc)
        except BandError as exc:
            logger.warning("Band live open failed (%s); falling back to simulation.", exc)
            self._live = False
            self._fallback_reason = f"Band room setup failed: {exc}"
            await self._close_http()
            return

        # A "live" run that joined no agents would silently deliver zero real
        # messages while still claiming band-live. Treat that as a failed live
        # open and fall back honestly rather than masking it.
        if len(self._joined) < 3:
            logger.warning(
                "Only %d agent(s) joined the Band room; falling back to simulation.",
                len(self._joined),
            )
            self._live = False
            self._fallback_reason = (
                f"Only {len(self._joined)} agent(s) joined the Band room; "
                "running local Band simulation instead of an unverifiable live run."
            )
            await self._close_http()

    async def send(
        self,
        sender: str,
        content: str,
        *,
        message_type: str = "chat",
        payload: dict[str, Any] | None = None,
        mentions: list[str] | None = None,
    ) -> RoomMessage:
        """Record a room message, posting through real Band when live."""
        message = self._sim.send(
            sender,
            content,
            message_type=message_type,
            payload=payload,
            mentions=mentions,
        )
        if self._live and self._client and self._http is not None:
            await self._deliver_live(sender, content, message_type, message)
        self.messages = self._sim.messages
        return message

    async def _deliver_live(
        self, sender: str, content: str, message_type: str, message: RoomMessage
    ) -> None:
        assert self._client and self._http is not None
        sender_agent = self._agents.get(sender) if sender in self._joined else None
        # Only mention agents Band confirmed as room participants; mentioning a
        # non-participant returns 422 mentioned_participant_not_in_room.
        mention_agents = [
            self._agents[name]
            for name in message.mentions
            if name in self._agents and name in self._joined
        ]
        # Broadcasts/status, or anything we cannot route to a real agent, go as
        # Band events (which require no mention). True handoffs go as messages.
        route_as_event = message_type in EVENT_MESSAGE_TYPES or not mention_agents
        try:
            if route_as_event:
                event_sender = sender_agent or self._any_agent()
                if event_sender is None:
                    return
                event_id = await self._client.create_event(
                    self._http, self.room_id, event_sender, content, "task"
                )
                message.band_delivery = "event"
                message.band_message_id = event_id or None
                self.events.append(
                    BandEventRecord(
                        event_id=event_id or None,
                        sender=sender,
                        event_type="task",
                        content=content[:500],
                    )
                )
            else:
                if sender_agent is None:
                    # Sender is not a registered agent (e.g. human); emit as event.
                    event_sender = self._any_agent()
                    if event_sender is not None:
                        event_id = await self._client.create_event(
                            self._http, self.room_id, event_sender, content, "task"
                        )
                        message.band_delivery = "event"
                        message.band_message_id = event_id or None
                    return
                result = await self._client.send_message(
                    self._http, self.room_id, sender_agent, content, mention_agents
                )
                message.band_delivery = "message"
                message.band_message_id = result.message_id or None
                message.band_recipients = result.recipients
        except BandError as exc:
            logger.warning("Band delivery failed for %s message: %s", sender, exc)

    async def recall_memories(self, reader: str) -> list[dict[str, Any]]:
        """Recall prior subject-scoped memories for this vendor (cross-session).

        Returns Band memory records about the same vendor from earlier runs, so
        the room can open with prior-review context instead of a cold start.
        """
        if not (self._live and self._client and self._http is not None):
            return []
        reader_agent = self._agents.get(reader) or self._any_agent()
        if reader_agent is None:
            return []
        try:
            return await self._client.list_memories(
                self._http, reader_agent, subject_id=self.subject_id
            )
        except BandError as exc:
            logger.warning("Band memory recall failed: %s", exc)
            return []

    async def memory(
        self,
        author: str,
        *,
        content: str,
        thought: str,
        tags: list[str] | None = None,
    ) -> None:
        """Store a shared cross-agent memory in Band (subject scope)."""
        record = BandMemoryRecord(
            author=author, subject_id=self.subject_id, summary=content[:500], tags=tags or []
        )
        if self._live and self._client and self._http is not None:
            author_agent = self._agents.get(author) or self._any_agent()
            if author_agent is not None:
                try:
                    memory_id = await self._client.store_memory(
                        self._http,
                        author_agent,
                        content=content,
                        thought=thought,
                        subject_id=self.subject_id,
                        tags=tags or ["procureguard", "context-packet"],
                    )
                    record.memory_id = memory_id or None
                except BandError as exc:
                    logger.warning("Band memory store failed: %s", exc)
        self.memories.append(record)

    async def rehydrate_context(self, reader: str) -> int:
        """Read shared room context back through Band before the decision."""
        if not (self._live and self._client and self._http is not None):
            return len(self.messages)
        reader_agent = self._agents.get(reader) or self._any_agent()
        if reader_agent is None:
            return len(self.messages)
        try:
            context = await self._client.get_context(self._http, self.room_id, reader_agent)
            return len(context)
        except BandError as exc:
            logger.warning("Band context rehydration failed: %s", exc)
            return len(self.messages)

    async def close(self) -> None:
        await self._close_http()

    async def _close_http(self) -> None:
        if self._http is not None:
            try:
                await self._http.aclose()
            finally:
                self._http = None
