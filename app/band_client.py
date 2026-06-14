from __future__ import annotations

"""Real Band platform client (https://app.band.ai).

This is the actual coordination layer for ProcureGuard. It speaks the Band
Human API (create a room, add agent participants) and the Band Agent API
(post @mentioned messages, emit task/tool_call/thought events, and store or
read cross-agent memories). Every endpoint here is exercised against the live
platform when Band credentials are present.

Endpoints used (verified against https://docs.band.ai):
  Human API
    POST /api/v1/me/chats                      create a chat room
    POST /api/v1/me/chats/{chat_id}/participants  add an agent to the room
    POST /api/v1/me/agents/register            register a remote agent
  Agent API
    POST /api/v1/agent/chats/{chat_id}/messages   send a message (mentions)
    POST /api/v1/agent/chats/{chat_id}/events      emit task/tool_call/thought
    POST /api/v1/agent/memories                    store cross-agent memory
    GET  /api/v1/agent/chats/{chat_id}/context     rehydrate room context
"""

import logging
from dataclasses import dataclass, field
from typing import Any

import httpx


logger = logging.getLogger("procureguard.band")

EVENT_TYPES = {"tool_call", "tool_result", "thought", "error", "task"}


class BandError(RuntimeError):
    """Raised when the Band platform returns an error or is unreachable."""


@dataclass
class BandParticipant:
    """A registered Band agent that can act in a room."""

    role: str
    agent_id: str
    api_key: str
    name: str


@dataclass
class BandMessageResult:
    message_id: str
    recipients: list[dict[str, Any]] = field(default_factory=list)


class BandClient:
    """Thin, typed wrapper over the Band REST API.

    The client is transport-only: it does not decide *what* agents say, just
    moves real messages, events, and memories through Band. Orchestration lives
    in the workflow layer.
    """

    def __init__(
        self,
        *,
        base_url: str,
        user_api_key: str | None,
        timeout_seconds: int = 45,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.user_api_key = user_api_key
        self.timeout = httpx.Timeout(timeout_seconds)

    # ----- transport ---------------------------------------------------

    async def _request(
        self,
        client: httpx.AsyncClient,
        method: str,
        path: str,
        *,
        api_key: str,
        json_body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
        try:
            response = await client.request(method, url, headers=headers, json=json_body, params=params)
        except httpx.HTTPError as exc:
            raise BandError(f"Band request failed: {exc.__class__.__name__} on {method} {path}") from exc
        if response.status_code >= 400:
            raise BandError(
                f"Band returned HTTP {response.status_code} on {method} {path}: {response.text[:300]}"
            )
        if not response.content:
            return {}
        return response.json()

    # ----- human API ---------------------------------------------------

    async def create_room(self, client: httpx.AsyncClient, title: str) -> str:
        if not self.user_api_key:
            raise BandError("BAND_USER_API_KEY is required to create a room.")
        payload = {"chat": {"title": title[:120]}}
        data = await self._request(
            client, "POST", "/api/v1/me/chats", api_key=self.user_api_key, json_body=payload
        )
        room_id = data.get("data", {}).get("id")
        if not room_id:
            raise BandError("Band did not return a room id.")
        return room_id

    async def add_participant(
        self,
        client: httpx.AsyncClient,
        room_id: str,
        participant_id: str,
        *,
        role: str = "member",
    ) -> dict[str, Any]:
        if not self.user_api_key:
            raise BandError("BAND_USER_API_KEY is required to add participants.")
        payload = {"participant": {"participant_id": participant_id, "role": role}}
        data = await self._request(
            client,
            "POST",
            f"/api/v1/me/chats/{room_id}/participants",
            api_key=self.user_api_key,
            json_body=payload,
        )
        return data.get("data", {})

    # ----- agent-side room creation (no Enterprise plan needed) --------

    async def create_room_as_agent(
        self, client: httpx.AsyncClient, creator: BandParticipant, title: str
    ) -> str:
        """Create a chat room using an agent's own key (Agent API).

        The Human API room endpoint requires an Enterprise plan; the Agent API
        lets a registered agent open its own room, which also matches Band's
        "agents recruit each other" model more directly.
        """
        payload = {"chat": {"title": title[:120]}}
        data = await self._request(
            client,
            "POST",
            "/api/v1/agent/chats",
            api_key=creator.api_key,
            json_body=payload,
        )
        room_id = data.get("data", {}).get("id")
        if not room_id:
            raise BandError("Band did not return a room id (agent create).")
        return room_id

    async def add_participant_as_agent(
        self,
        client: httpx.AsyncClient,
        room_id: str,
        adder: BandParticipant,
        participant_id: str,
        *,
        role: str = "member",
    ) -> dict[str, Any]:
        """Add a sibling agent to a room using the adding agent's own key."""
        payload = {"participant": {"participant_id": participant_id, "role": role}}
        data = await self._request(
            client,
            "POST",
            f"/api/v1/agent/chats/{room_id}/participants",
            api_key=adder.api_key,
            json_body=payload,
        )
        return data.get("data", {})

    async def register_agent(
        self, client: httpx.AsyncClient, name: str, description: str
    ) -> dict[str, str]:
        if not self.user_api_key:
            raise BandError("BAND_USER_API_KEY is required to register agents.")
        payload = {"agent": {"name": name, "description": description}}
        data = await self._request(
            client,
            "POST",
            "/api/v1/me/agents/register",
            api_key=self.user_api_key,
            json_body=payload,
        )
        body = data.get("data", {})
        return {
            "agent_id": body.get("agent", {}).get("id", ""),
            "api_key": body.get("credentials", {}).get("api_key", ""),
        }

    # ----- agent API ---------------------------------------------------

    async def send_message(
        self,
        client: httpx.AsyncClient,
        room_id: str,
        sender: BandParticipant,
        content: str,
        mentions: list[BandParticipant],
    ) -> BandMessageResult:
        """Post a routed message as an agent. Band requires >=1 @mention."""
        mention_payload = [
            {"id": peer.agent_id, "name": peer.name} for peer in mentions if peer.agent_id
        ]
        if not mention_payload:
            raise BandError(
                f"{sender.name} tried to post without a routable @mention; Band rejects unrouted messages."
            )
        payload = {"message": {"content": content, "mentions": mention_payload}}
        data = await self._request(
            client,
            "POST",
            f"/api/v1/agent/chats/{room_id}/messages",
            api_key=sender.api_key,
            json_body=payload,
        )
        body = data.get("data", {})
        return BandMessageResult(
            message_id=body.get("id", ""),
            recipients=body.get("recipients", []),
        )

    async def create_event(
        self,
        client: httpx.AsyncClient,
        room_id: str,
        sender: BandParticipant,
        content: str,
        message_type: str,
    ) -> str:
        """Emit a task/tool_call/thought event (no mention required)."""
        if message_type not in EVENT_TYPES:
            raise BandError(f"Invalid Band event type: {message_type}")
        payload = {"event": {"content": content[:2000], "message_type": message_type}}
        data = await self._request(
            client,
            "POST",
            f"/api/v1/agent/chats/{room_id}/events",
            api_key=sender.api_key,
            json_body=payload,
        )
        return data.get("data", {}).get("id", "")

    async def store_memory(
        self,
        client: httpx.AsyncClient,
        sender: BandParticipant,
        *,
        content: str,
        thought: str,
        subject_id: str,
        segment: str = "agent",
        system: str = "long_term",
        type: str = "semantic",
        tags: list[str] | None = None,
    ) -> str:
        """Store a cross-agent memory (subject scope = shared across agents)."""
        memory: dict[str, Any] = {
            "content": content[:4000],
            "segment": segment,
            "system": system,
            "type": type,
            "thought": thought[:1000],
            "scope": "subject",
            "subject_id": subject_id,
        }
        if tags:
            memory["metadata"] = {"tags": tags}
        data = await self._request(
            client,
            "POST",
            "/api/v1/agent/memories",
            api_key=sender.api_key,
            json_body={"memory": memory},
        )
        return data.get("data", {}).get("id", "")

    async def get_context(
        self, client: httpx.AsyncClient, room_id: str, reader: BandParticipant
    ) -> list[dict[str, Any]]:
        """Rehydrate the room's message history relevant to the reader agent."""
        data = await self._request(
            client,
            "GET",
            f"/api/v1/agent/chats/{room_id}/context",
            api_key=reader.api_key,
        )
        return data.get("data", [])

    async def list_memories(
        self,
        client: httpx.AsyncClient,
        reader: BandParticipant,
        *,
        subject_id: str,
        page_size: int = 20,
    ) -> list[dict[str, Any]]:
        """Recall prior subject-scoped memories (cross-session shared context)."""
        data = await self._request(
            client,
            "GET",
            "/api/v1/agent/memories",
            api_key=reader.api_key,
            params={"subject_id": subject_id, "scope": "subject", "page_size": page_size},
        )
        return data.get("data", [])

    def client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=self.timeout)
