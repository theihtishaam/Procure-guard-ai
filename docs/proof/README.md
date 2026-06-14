# Real Band Live-Run Proof

This folder contains committed evidence that ProcureGuard ran on the **real Band
platform** (`app.band.ai`), not only the local simulator. It addresses the
hackathon's central requirement: Band must be the actual coordination layer.

## What is here

- `live-band-proof.json` — compact proof summary: live mode, the real Band room
  ID/URL, counts of real Band messages and events, sample Band-issued message
  UUIDs, decision, and collaboration score.
- `live-band-run.json` — the full workflow run as returned by the API during a
  live run (no secrets; agent API keys are never serialized).
- `../../output/playwright/procureguard-live-dashboard.png` — the dashboard in
  live mode.
- `../../output/playwright/procureguard-live-band-proof.png` — the "Live Band
  Proof" panel showing the `LIVE on app.band.ai` tag, the room link, and real
  message/event counts.

## How it was produced

1. Registered 8 Remote Agents in Band (`scripts/register_band_agents.py`), which
   wrote one-time per-agent credentials to the gitignored `agent_config.yaml`.
2. Ran the workflow with `BAND_ENABLED=1`. The Intake Coordinator agent created
   a real Band chat room with its own Agent-API key and recruited its seven
   sibling agents as room participants.
3. Each handoff was posted as a real Band message (`POST /agent/chats/{id}/messages`,
   with `@mention` routing) and each broadcast/status as a real Band task event
   (`POST /agent/chats/{id}/events`). Band returned a real UUID for each.
4. The same messages were read back through Band's context API
   (`GET /agent/chats/{id}/context`, HTTP 200), confirming they actually landed
   on the platform.

## Verified findings about the Band plan

- **Room creation + participant recruitment**: work on the hackathon Pro plan via
  the **Agent API** (`POST /api/v1/agent/chats`, `.../participants`). The Human
  API equivalents (`/api/v1/me/chats`) are **Enterprise-gated** (`403 plan_required`).
- **Memory API** (`/api/v1/agent/memories`) is **Enterprise-gated** on Pro. The
  app degrades gracefully: it still exchanges shared context through real Band
  messages, and the shared-context packet is recorded locally. No fake success is
  ever reported — the run mode honestly reflects what happened.

## Reproduce

With Band credentials in `.env.local` (`BAND_ENABLED=1`, `BAND_USER_API_KEY=...`)
and registered agents in `agent_config.yaml`:

```powershell
uv run python -m app.main
# open the dashboard, run a case; the Live Band Proof panel shows the real room.
```
