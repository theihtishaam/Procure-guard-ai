# Band Live Setup

ProcureGuard runs against the **real Band platform** (`app.band.ai`). This guide
covers the verified live path and what each plan tier unlocks.

## What is verified working

On the hackathon **Pro plan (BANDHACK26)**, a real live run produces:

- a real Band chat room (created by the Intake Coordinator agent),
- all eight agents added as real room participants,
- routed `@mention` messages with real Band-issued message IDs,
- task events through the Agent API,
- messages readable back through Band's context endpoint.

Captured proof lives in `docs/proof/live-band-proof.json` (room URL + real
message IDs from an actual run).

## Plan tiers (confirmed against the live API)

- **Agent API** (room create, add participant, messages, events, context):
  works on Pro. This is the path ProcureGuard uses by default.
- **Human API** (`/api/v1/me/chats...`) and **Memory API** (`/api/v1/agent/memories`):
  return `403 plan_required` on Pro — they require an Enterprise plan.

ProcureGuard therefore opens the room as the **Coordinator agent** (Agent API),
which also matches Band's "agents recruit each other" model better than a
human-created room. Cross-agent Band memory is wired and works on Enterprise;
on Pro it degrades gracefully and shared context still flows through real Band
messages.

## 1. Register the agents

Add your Band user API key to `.env.local` as `BAND_USER_API_KEY`, then:

```powershell
uv run python scripts/register_band_agents.py --confirm-create
```

This registers the eight agents and writes their one-time credentials to
`agent_config.yaml` (gitignored).

## 2. Configure local secrets

`.env.local` (never committed):

```text
AIMLAPI_API_KEY=...
AIMLAPI_BASE_URL=https://api.aimlapi.com/v1
AIMLAPI_MODEL_PRIMARY=gpt-4o-mini
AIMLAPI_MODEL_FAST=gpt-4o-mini
ENABLE_LIVE_LLM=1
BAND_ENABLED=1
BAND_USER_API_KEY=...
```

## 3. Run a live workflow (server-orchestrated)

With `BAND_ENABLED=1` and `agent_config.yaml` present, every dashboard run
executes against real Band: the Coordinator opens a room, recruits the peers,
and each handoff is posted as a real Band message/event. The dashboard's
"Live Band Proof" panel shows the room link and real message IDs.

```powershell
uv run python -m app.main
```

## 4. Run as independent cross-framework SDK agents (optional, Originality proof)

Each role can also run as its own long-lived Band Remote Agent on a different
framework, all joining one room:

```powershell
uv sync --extra band
uv run --extra band python scripts/live_band_agent.py coordinator         # LangGraph
uv run --extra band python scripts/live_band_agent.py vendor_research      # CrewAI
uv run --extra band python scripts/live_band_agent.py finance_roi          # Pydantic AI
uv run --extra band python scripts/live_band_agent.py security_compliance  # Anthropic
uv run --extra band python scripts/live_band_agent.py legal_policy         # Pydantic AI
uv run --extra band python scripts/live_band_agent.py evidence_clerk       # LangGraph
uv run --extra band python scripts/live_band_agent.py red_team_auditor     # CrewAI
uv run --extra band python scripts/live_band_agent.py approval_manager     # Anthropic
```

These require `THENVOI_REST_URL` / `THENVOI_WS_URL` (defaults point at
`app.band.ai`) and the relevant provider keys. Then in Band, mention the
Coordinator:

```text
@Intake Coordinator Open procurement case: VectorCRM, CRM enrichment and lead routing, $42,000, Salesforce/HubSpot/Slack integrations, customer contact and opportunity data, SOC 2 under NDA, DPA not reviewed. Coordinate peer review and produce a final decision memo.
```

The coordinator mentions the specialists; specialists hand off to
`@Evidence Clerk Agent`; the Evidence Clerk mentions `@Red Team Auditor Agent`;
the auditor challenges or clears; the manager produces the decision and human gate.
