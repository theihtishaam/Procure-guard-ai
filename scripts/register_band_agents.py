from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import httpx
import yaml
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT_DIR / "agent_config.yaml"

AGENTS = {
    "coordinator": (
        "Intake Coordinator",
        "Opens procurement cases, recruits peer agents, and preserves shared state in the Band room.",
    ),
    "vendor_research": (
        "Vendor Research Agent",
        "Reviews vendor maturity, diligence gaps, references, and operational fit.",
    ),
    "finance_roi": (
        "Finance ROI Agent",
        "Reviews spend exposure, ROI, pilot caps, success metrics, and renewal guardrails.",
    ),
    "security_compliance": (
        "Security Compliance Agent",
        "Reviews data access, integrations, controls, privacy risk, and compliance evidence.",
    ),
    "legal_policy": (
        "Legal Policy Agent",
        "Reviews DPA, subprocessors, retention, audit rights, and policy exceptions.",
    ),
    "evidence_clerk": (
        "Evidence Clerk Agent",
        "Consolidates specialist handoffs into a shared context packet and audit record.",
    ),
    "red_team_auditor": (
        "Red Team Auditor Agent",
        "Challenges unsafe assumptions and routes warnings or vetoes before approval.",
    ),
    "approval_manager": (
        "Approval Manager Agent",
        "Synthesizes the reviewed packet into a decision memo and human approval gate.",
    ),
}


def load_existing() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}


def save_config(config: dict) -> None:
    CONFIG_PATH.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")


def require_key() -> str:
    load_dotenv(ROOT_DIR / ".env.local", encoding="utf-8-sig")
    load_dotenv(ROOT_DIR / ".env", encoding="utf-8-sig")
    key = os.getenv("BAND_USER_API_KEY")
    if not key:
        raise SystemExit("BAND_USER_API_KEY is missing. Add it to .env.local first.")
    return key


def register_agent(client: httpx.Client, base_url: str, api_key: str, role: str) -> dict:
    name, description = AGENTS[role]
    response = client.post(
        f"{base_url.rstrip('/')}/api/v1/me/agents/register",
        headers={"X-API-Key": api_key, "Content-Type": "application/json"},
        json={"agent": {"name": name, "description": description}},
    )
    if response.status_code >= 400:
        raise RuntimeError(f"{role}: Band returned HTTP {response.status_code}: {response.text[:300]}")
    payload = response.json()["data"]
    return {
        "agent_id": payload["agent"]["id"],
        "api_key": payload["credentials"]["api_key"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Register ProcureGuard Remote Agents in Band.")
    parser.add_argument("--confirm-create", action="store_true", help="Actually create agents in Band.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing roles in agent_config.yaml.")
    args = parser.parse_args()

    if not args.confirm_create:
        print("Dry run. Re-run with --confirm-create to create Band Remote Agents.")
        for role, (name, description) in AGENTS.items():
            print(f"- {role}: {name} - {description}")
        return

    api_key = require_key()
    base_url = os.getenv("BAND_APP_URL", "https://app.band.ai")
    config = load_existing()
    created: list[str] = []
    skipped: list[str] = []

    with httpx.Client(timeout=45) as client:
        for role in AGENTS:
            if role in config and not args.overwrite:
                skipped.append(role)
                continue
            config[role] = register_agent(client, base_url, api_key, role)
            created.append(role)

    save_config(config)
    print({"created": created, "skipped_existing": skipped, "config_path": str(CONFIG_PATH)})
    if created:
        print("Agent API keys were saved to agent_config.yaml. Do not commit that file.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise
