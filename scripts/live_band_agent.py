from __future__ import annotations

"""
Optional live Band runner.

Create one Remote Agent in Band per role, add credentials to agent_config.yaml,
then run this file with a role key such as:

    uv run --extra band python scripts/live_band_agent.py vendor_research

The local dashboard already demonstrates the workflow with the same room and
handoff semantics. This file is the bridge for real Band rooms once credentials
exist.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
ROLE_INSTRUCTIONS = {
    "coordinator": "You are Intake Coordinator. Recruit peer agents, preserve shared context, and keep the procurement room moving.",
    "vendor_research": "You are Vendor Research Agent. Produce concise vendor diligence artifacts and hand off to Approval Manager Agent.",
    "finance_roi": "You are Finance ROI Agent. Analyze budget fit, ROI, spend controls, and pilot success criteria.",
    "security_compliance": "You are Security Compliance Agent. Analyze data access, integrations, privacy, and security controls.",
    "legal_policy": "You are Legal Policy Agent. Analyze DPA, audit rights, retention, subprocessors, and policy exceptions.",
    "evidence_clerk": "You are Evidence Clerk Agent. Consolidate specialist handoffs into one shared context packet and route it to Approval Manager Agent.",
    "red_team_auditor": "You are Red Team Auditor Agent. Challenge the shared context, identify unsafe assumptions, and route vetoes or warnings before approval.",
    "approval_manager": "You are Approval Manager Agent. Synthesize room artifacts into approve, conditional approve, reject, or escalate decisions.",
}


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    load_dotenv(ROOT_DIR / ".env.local")
    load_dotenv(ROOT_DIR / ".env")

    if len(sys.argv) < 2 or sys.argv[1] not in ROLE_INSTRUCTIONS:
        roles = ", ".join(ROLE_INSTRUCTIONS)
        raise SystemExit(f"Usage: python scripts/live_band_agent.py <role>. Roles: {roles}")

    try:
        from langchain_openai import ChatOpenAI
        from langgraph.checkpoint.memory import InMemorySaver
        from thenvoi import Agent
        from thenvoi.adapters import LangGraphAdapter
        from thenvoi.config import load_agent_config
    except ImportError as exc:
        raise SystemExit("Install live Band dependencies first: uv sync --extra band") from exc

    role = sys.argv[1]
    agent_id, api_key = load_agent_config(role)
    llm = ChatOpenAI(
        model=os.getenv("AIMLAPI_MODEL_PRIMARY", "gpt-4o-mini"),
        api_key=os.environ["AIMLAPI_API_KEY"],
        base_url=os.getenv("AIMLAPI_BASE_URL", "https://api.aimlapi.com/v1"),
        temperature=0.2,
    )
    adapter = LangGraphAdapter(
        llm=llm,
        checkpointer=InMemorySaver(),
        custom_section=ROLE_INSTRUCTIONS[role],
    )
    agent = Agent.create(adapter=adapter, agent_id=agent_id, api_key=api_key)
    logging.info("Band agent %s is running. Press Ctrl+C to stop.", role)
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
