from __future__ import annotations

"""Live, cross-framework Band Remote Agent runner.

Each ProcureGuard role runs on a *different* agent framework, all joining the
same Band room. This proves Band's signature capability: agents built on
LangGraph, CrewAI, Pydantic AI, and Anthropic discover each other and
collaborate through one shared room, with no hardcoded agent-to-agent wiring.

Setup (see docs/band_live_setup.md):
  1. Register one Band Remote Agent per role (scripts/register_band_agents.py)
     and store credentials in agent_config.yaml.
  2. Put provider keys in .env.local:
       AIMLAPI_API_KEY=...        # OpenAI-compatible (LangGraph, CrewAI, Pydantic AI)
       ANTHROPIC_API_KEY=...      # optional, for the Anthropic-adapter roles
  3. Install: uv sync --extra band
  4. Run one process per role:
       uv run --extra band python scripts/live_band_agent.py coordinator
       uv run --extra band python scripts/live_band_agent.py vendor_research
       ... (one terminal per role)

The local dashboard demonstrates the same workflow against the Band simulator;
this runner is the real-platform proof.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]

# role -> (framework, display name, instruction)
ROLES: dict[str, tuple[str, str, str]] = {
    "coordinator": (
        "langgraph",
        "Intake Coordinator",
        "You are the Intake Coordinator. Open the procurement case, recruit the "
        "specialist peers by @mention, preserve shared context, and keep the room moving "
        "toward a decision. Route specialist handoffs to @Evidence Clerk Agent.",
    ),
    "vendor_research": (
        "crewai",
        "Vendor Research Agent",
        "You are the Vendor Research Agent. Assess vendor maturity, product fit, missing "
        "diligence evidence, and operational readiness. Hand your findings to "
        "@Evidence Clerk Agent.",
    ),
    "finance_roi": (
        "pydantic_ai",
        "Finance ROI Agent",
        "You are the Finance ROI Agent. Evaluate spend exposure, ROI, pilot economics, and "
        "renewal guardrails. Hand your findings to @Evidence Clerk Agent.",
    ),
    "security_compliance": (
        "anthropic",
        "Security Compliance Agent",
        "You are the Security Compliance Agent. Assess data access, integrations, security "
        "controls, and privacy posture. Hand your findings to @Evidence Clerk Agent.",
    ),
    "legal_policy": (
        "pydantic_ai",
        "Legal Policy Agent",
        "You are the Legal Policy Agent. Review DPA, subprocessors, retention, audit rights, "
        "and regulated-data terms. Hand your findings to @Evidence Clerk Agent.",
    ),
    "evidence_clerk": (
        "langgraph",
        "Evidence Clerk Agent",
        "You are the Evidence Clerk Agent. Consolidate specialist handoffs into one shared "
        "context packet, store it as shared memory, and route it to @Red Team Auditor Agent.",
    ),
    "red_team_auditor": (
        "crewai",
        "Red Team Auditor Agent",
        "You are the Red Team Auditor Agent. Challenge the shared context, identify unsafe "
        "assumptions, and route warnings to @Security Compliance Agent and @Legal Policy Agent "
        "before clearing @Approval Manager Agent to decide.",
    ),
    "approval_manager": (
        "anthropic",
        "Approval Manager Agent",
        "You are the Approval Manager Agent. Synthesize the reviewed packet into approve, "
        "conditional approve, reject, or escalate, then route the gate to @Human Procurement Lead.",
    ),
}


def build_adapter(framework: str, instruction: str):
    """Construct the real thenvoi adapter for the given framework."""
    aiml_key = os.environ.get("AIMLAPI_API_KEY")
    aiml_base = os.getenv("AIMLAPI_BASE_URL", "https://api.aimlapi.com/v1")
    openai_model = os.getenv("AIMLAPI_MODEL_PRIMARY", "gpt-4o-mini")

    if framework == "langgraph":
        from langchain_openai import ChatOpenAI
        from langgraph.checkpoint.memory import InMemorySaver
        from thenvoi.adapters import LangGraphAdapter

        return LangGraphAdapter(
            llm=ChatOpenAI(
                model=openai_model,
                api_key=aiml_key,
                base_url=aiml_base,
                temperature=0.2,
            ),
            checkpointer=InMemorySaver(),
            custom_section=instruction,
        )

    if framework == "crewai":
        # CrewAI reads OpenAI-compatible settings from the environment.
        os.environ.setdefault("OPENAI_API_KEY", aiml_key or "")
        os.environ.setdefault("OPENAI_API_BASE", aiml_base)
        from thenvoi.adapters import CrewAIAdapter

        return CrewAIAdapter(
            model=f"openai/{openai_model}",
            role="Enterprise procurement specialist",
            goal="Produce an audit-ready review and hand off cleanly to the next agent.",
            backstory="A meticulous enterprise reviewer who documents evidence and gaps.",
            custom_section=instruction,
        )

    if framework == "pydantic_ai":
        os.environ.setdefault("OPENAI_API_KEY", aiml_key or "")
        os.environ.setdefault("OPENAI_BASE_URL", aiml_base)
        from thenvoi.adapters import PydanticAIAdapter

        return PydanticAIAdapter(
            model=f"openai:{openai_model}",
            custom_section=instruction,
        )

    if framework == "anthropic":
        from thenvoi.adapters import AnthropicAdapter

        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        if not anthropic_key:
            # Fall back to LangGraph over AIMLAPI so the role still runs live.
            logging.warning(
                "ANTHROPIC_API_KEY not set; running this role on LangGraph/AIMLAPI instead."
            )
            return build_adapter("langgraph", instruction)
        return AnthropicAdapter(
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
            anthropic_api_key=anthropic_key,
            custom_section=instruction,
        )

    raise SystemExit(f"Unknown framework: {framework}")


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    load_dotenv(ROOT_DIR / ".env.local", encoding="utf-8-sig")
    load_dotenv(ROOT_DIR / ".env", encoding="utf-8-sig")

    if len(sys.argv) < 2 or sys.argv[1] not in ROLES:
        roles = ", ".join(ROLES)
        raise SystemExit(f"Usage: python scripts/live_band_agent.py <role>\nRoles: {roles}")

    role = sys.argv[1]
    framework, display_name, instruction = ROLES[role]

    if not os.environ.get("AIMLAPI_API_KEY"):
        raise SystemExit("AIMLAPI_API_KEY is required in .env.local for live agents.")

    try:
        from thenvoi import Agent
        from thenvoi.config import load_agent_config
    except ImportError as exc:
        raise SystemExit("Install live Band dependencies first: uv sync --extra band") from exc

    agent_id, api_key = load_agent_config(role)
    adapter = build_adapter(framework, instruction)
    # The Band SDK needs the platform REST + WebSocket URLs. Defaults point at
    # the hosted platform; override via THENVOI_REST_URL / THENVOI_WS_URL.
    rest_url = os.getenv("THENVOI_REST_URL", "https://app.band.ai/")
    ws_url = os.getenv("THENVOI_WS_URL", "wss://app.band.ai/api/v1/socket/websocket")
    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=ws_url,
        rest_url=rest_url,
    )
    logging.info("Band agent '%s' (%s, %s) is live. Ctrl+C to stop.", display_name, role, framework)
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
