# Band Live Setup

ProcureGuard can run locally without Band credentials, but the hackathon submission should include a real Band room recording. Use this checklist to switch from local simulation to Band live mode.

## 1. Create Remote Agents In Band

Option A, automated: add your human API key to `.env.local` as `BAND_USER_API_KEY`, then run:

```powershell
uv run python scripts/register_band_agents.py --confirm-create
```

This registers the eight external agents through the Human API and writes their one-time agent credentials to `agent_config.yaml`.

Option B, manual: in Band, create one Remote Agent for each role:

- Intake Coordinator
- Vendor Research Agent
- Finance ROI Agent
- Security Compliance Agent
- Legal Policy Agent
- Evidence Clerk Agent
- Red Team Auditor Agent
- Approval Manager Agent

For each Remote Agent, copy the Agent UUID and API key when Band shows it. Store them in `agent_config.yaml`, using `agent_config.example.yaml` as the template.

## 2. Configure Local Secrets

Add these values to `.env.local`:

```text
AIMLAPI_API_KEY=...
AIMLAPI_BASE_URL=https://api.aimlapi.com/v1
AIMLAPI_MODEL_PRIMARY=gpt-4o-mini
AIMLAPI_MODEL_FAST=gpt-4o-mini
BAND_ENABLED=1
BAND_USER_API_KEY=...
```

Do not commit `.env.local` or `agent_config.yaml`. The human API key is only needed to register agents; the live runners use the per-agent keys in `agent_config.yaml`.

## 3. Install Live Dependencies

```powershell
uv sync --extra band
```

## 4. Run Agents

Open one terminal per role:

```powershell
uv run --extra band python scripts/live_band_agent.py coordinator
uv run --extra band python scripts/live_band_agent.py vendor_research
uv run --extra band python scripts/live_band_agent.py finance_roi
uv run --extra band python scripts/live_band_agent.py security_compliance
uv run --extra band python scripts/live_band_agent.py legal_policy
uv run --extra band python scripts/live_band_agent.py evidence_clerk
uv run --extra band python scripts/live_band_agent.py red_team_auditor
uv run --extra band python scripts/live_band_agent.py approval_manager
```

## 5. Demo Flow In Band

Create a Band chat room and add all eight remote agents. Start with:

```text
@Intake Coordinator Open procurement case: VectorCRM, AI-assisted CRM enrichment, $42,000, Salesforce/HubSpot/Slack integrations, customer contact and opportunity data, SOC 2 under NDA, DPA not reviewed. Coordinate peer review and produce a final decision memo.
```

The coordinator should mention the specialist agents. Specialists should hand off artifacts to `@Evidence Clerk Agent`, the Evidence Clerk should mention `@Red Team Auditor Agent`, the Red Team Auditor should challenge or clear the packet, and the manager should produce the final decision plus human gate.
