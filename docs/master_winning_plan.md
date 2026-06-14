# ProcureGuard AI — Master Winning Plan (Real Band Edition)

> Target: Band of Agents Hackathon, $10K+ pool, deadline 2026-06-19 08:00 PDT.
> Track 1 (Internal Enterprise Workflows) + AI/ML API partner prize.
> This plan supersedes `deep_winning_plan.md`. It converts the existing
> simulator-based submission into a system where **Band is the real
> coordination layer**, which is what every judging criterion rewards.

---

## 1. The brutal truth about the current submission

The repo already contains a polished product:

- A FastAPI dashboard with timeline, handoff map, task state, governance
  controls, business impact, evidence bundle, SHA-256 audit seal.
- A real, well-structured 8-agent procurement workflow engine (`app/agents.py`,
  `app/workflow.py`) with LLM + deterministic fallback.
- Real Band scaffolding that is currently *optional and unused*
  (`scripts/register_band_agents.py`, `scripts/live_band_agent.py`, `thenvoi`).

But the running workflow uses `app/band_room.py::BandRoomSimulator` — a **local
stand-in** for Band. The judging rubric's first and heaviest criterion is:

> "How effectively does the solution use **Band as the coordination layer**
>  between multiple specialized agents? ... Band should be part of the actual
>  collaboration layer, not only a thin wrapper, final notification system,
>  or simple output channel."

A simulator is the textbook definition of what they say will lose. Our own
`deep_winning_plan.md` already lists this as the top risk. **This plan fixes it
by making the default, demonstrated path run on real Band**, while keeping the
deterministic engine only as an explicitly-labeled offline rehearsal mode.

---

## 2. Verified facts about real Band (researched 2026-06-14)

SDK and runtime:
- Install: `uv add "band-sdk[langgraph]"` (also `[crewai]`, `[openai]`,
  `[anthropic]`, `[pydantic-ai]`). Import package is `thenvoi`.
- Run an agent: `Agent.create(adapter=..., agent_id=..., api_key=...)` then
  `await agent.run()` — opens a persistent WebSocket, subscribes to channels,
  responds when @mentioned in rooms.
- Adapters wrap any framework's LLM loop; the Agent handles platform
  connection, message routing, room lifecycle.
- SDK exposes platform tools the LLM can call: `thenvoi_lookup_peers`,
  `thenvoi_add_participant`, `thenvoi_remove_participant`,
  `thenvoi_get_participants`, `thenvoi_send_message`, contact tools.

REST (base `https://app.band.ai`, header `X-API-Key`):
- Human — create room: `POST /api/v1/me/chats` body `{"chat":{"title":...}}`
  → `{"data":{"id": <chat_id>, ...}}`.
- Human — register agent: `POST /api/v1/me/agents/register` (existing script
  path) OR UI at app.band.ai/agents → New Agent → External Agent. API key shown
  once; agent UUID from settings.
- Human — send/list messages: `POST/GET /api/v1/me/chats/{id}/messages`.
- Agent — send message: `POST /api/v1/agent/chats/{id}/messages`
  body `{"message":{"content":"@x ...","mentions":[{"id","handle","name"}]}}`.
  **Every message needs >=1 @mention** or 422 `mentions_required`.
- Agent — events: `POST /api/v1/agent/chats/{id}/events`
  body `{"event":{"content","message_type"}}` where message_type is one of
  `tool_call|tool_result|thought|error|task`. **No mention required** — this is
  how we surface visible task state and reasoning to judges.
- Agent — context rehydration: `GET /api/v1/agent/chats/{id}/context` → all
  messages relevant to the agent (chronological, cursor pagination).
- Agent — memories (the differentiator): `POST /api/v1/agent/memories`
  body `{"memory":{content, segment, system, type, thought, scope, subject_id,
  metadata:{tags,references}}}`. `scope:"subject"` + `subject_id` =
  **cross-agent shared memory** about that subject; `scope:"organization"` =
  visible to all org agents. This is real shared structured context, not a wrapper.
- WebSocket: real-time `message-created`, participant add/remove, room events
  (agent + human channels).

Implication: we can build genuine agent-to-agent collaboration (discover,
recruit, @mention handoff, shared memory, task events) entirely on real Band,
and observe it live from the dashboard via the Human API + WebSocket.

---

## 3. Winning thesis (what we tell judges)

> ProcureGuard is an enterprise **vendor-approval war room** where eight agents,
> each built on a **different framework**, discover and recruit each other inside
> a real Band room, hand off structured findings by @mention, write shared
> context into Band's cross-agent memory, run an adversarial red-team challenge
> that can **veto** a decision, route to a human gate, and seal a tamper-evident
> audit record. Band is not a notifier — it is the nervous system: every
> handoff, every shared fact, every task state transition is a real Band
> primitive.

Edge over the already-submitted "GateKeeper" vendor-risk competitor (sharpened,
not abandoned — per decision):
1. **Adversarial veto loop** — Red Team Auditor posts a real challenge that
   forces re-work/escalation before the Approval Manager can decide. Most
   submissions are linear pipelines; this is a control loop.
2. **Cross-agent shared memory** — Evidence Clerk writes consensus + unresolved
   questions to Band memories (scope=subject), and downstream agents *read* them
   back via context. Visible proof of structured context exchange.
3. **True cross-framework** — LangGraph + CrewAI + OpenAI + Anthropic +
   Pydantic AI + raw Agent API agents in one room. This is Band's signature
   capability and few teams will do it for real.
4. **Live observability dashboard** — a control tower that renders the *real*
   Band room (timeline, handoff graph, task state, recruitment ledger) plus the
   governance artifacts (audit seal, evidence bundle, control matrix).
5. **Human-in-the-loop gate + tamper-evident seal** — enterprise governance,
   not a chat transcript.

---

## 4. Agent roster (each on a distinct framework — cross-framework proof)

| Role | Framework adapter | Why this framework | Band primitives used |
|---|---|---|---|
| Intake Coordinator | LangGraph | stateful recruiter/router | lookup_peers, add_participant, send_message, event(task) |
| Vendor Research | CrewAI | role/goal specialist | send_message handoff, event(thought) |
| Finance ROI | Pydantic AI | structured/typed output | send_message handoff |
| Security Compliance | OpenAI adapter | tool-using policy review | send_message handoff, memory(write) |
| Legal Policy | Anthropic adapter | long-context contract review | send_message handoff, memory(write) |
| Evidence Clerk | LangGraph | context steward | **memory(create scope=subject)**, context(read), send_message |
| Red Team Auditor | CrewAI | adversarial reviewer | send_message challenge, event(error/thought) |
| Approval Manager | OpenAI adapter | decision synthesis | context(read), memory(read), send_message decision |
| Human Procurement Lead | Human (real person/UI) | governance gate | human message in room |

Minimum 3 required; we field 8 AI + 1 human, each genuinely different.

---

## 5. Architecture

```
                         ┌─────────────────────────────────────────┐
                         │              REAL BAND ROOM               │
                         │  (app.band.ai, 1 chat room per case)      │
                         │                                           │
 dashboard ──create──▶   │  msgs(@mention) · events(task/thought)    │
 (Human API)             │  memories(scope=subject shared context)   │
      ▲                  └──────▲───────▲───────▲───────▲────────────┘
      │ WebSocket+REST          │       │       │       │
      │ (observe live)          │       │       │       │  (each agent = own process,
      │                    ┌────┴──┐ ┌──┴───┐ ┌─┴────┐ ┌┴─────┐  own framework adapter,
 ┌────┴───────┐           │Coord. │ │Vendor│ │Finance│ │ ...  │  thenvoi Agent.run())
 │  FastAPI    │           │LangGr.│ │CrewAI│ │Pydan. │ │      │
 │  control    │           └───────┘ └──────┘ └───────┘ └──────┘
 │  tower UI   │
 │  + audit    │   Offline rehearsal mode (labeled): existing deterministic
 │  + bundle   │   engine in app/workflow.py — demo safety net only.
 └─────────────┘
```

Two execution modes, both honest:
- **LIVE (default, demonstrated):** dashboard creates a real Band room, posts
  the opening case, the 8 agent processes collaborate on Band; dashboard
  observes via Human API + WebSocket and renders/scores the real transcript,
  then builds the audit seal + evidence bundle from real Band data.
- **REHEARSAL (fallback):** the current deterministic workflow, clearly badged
  "offline rehearsal — not live Band," kept so a flaky network never kills a demo.

---

## 6. Work breakdown (priority order)

### P0 — Make Band real (the criterion that wins)
1. `app/band_client.py` — async httpx client for Band: create room, send agent
   message (+mentions), post event, create/read memory, get context, list room
   messages (human). Typed, retry+timeout, secrets from env, never logged.
2. `app/band_agents/` — 8 runnable agents using `thenvoi` adapters (one file per
   role or a parameterized runner), each on its assigned framework, wired to the
   existing role prompts in `app/agents.py`. Reuse the AI/ML API model via the
   OpenAI-compatible base URL inside each adapter (partner-prize fit).
3. Real coordination protocol encoded in role custom_sections:
   coordinator recruits peers → specialists @mention handoffs → Evidence Clerk
   writes shared memory + posts context message → Red Team challenge (veto loop)
   → Approval Manager decision → human gate.
4. `scripts/register_band_agents.py` — confirm/repair against current API; write
   `agent_config.yaml` (gitignored).
5. `scripts/launch_band_room.py` — one command: create room, add participants,
   post opening case, print room URL for recording.

### P1 — Observe + score real Band from the dashboard
6. `app/band_observer.py` — poll/stream the real room (Human API + WebSocket),
   normalize Band messages/events/memories into the existing `RoomMessage` /
   `WorkflowRun` models so all current UI panels light up from real data.
7. New API routes: `POST /api/band/launch` (start live run),
   `GET /api/band/runs/{id}` (observed state), `GET /api/band/stream/{id}` (SSE).
8. Recompute audit seal, collaboration score, task state, governance,
   evidence bundle from the **real** transcript.

### P2 — Dashboard upgrade to a credible control tower
9. Mode badge (LIVE BAND vs OFFLINE REHEARSAL), real room link, live message
   stream, handoff graph from real mentions, shared-memory panel, veto-loop
   highlight, human-gate action.
10. Keep the polished visuals; rewire data source from simulator → observer.

### P3 — Proof, partner fit, and submission assets
11. AI/ML API everywhere the agents reason (document it for the $1K partner prize).
12. Smoke/verify scripts updated to exercise the live path (with a mockable Band
    base URL for CI) and the rehearsal path.
13. Demo video script: show the real Band room side-by-side with the control
    tower; trigger a veto; show shared memory; download evidence bundle.
14. README, submission form, slides, judging map rewritten around real Band.
15. Deploy (Render) the dashboard; agents run from a documented launch script
    during the recorded demo.

---

## 7. Judging-criteria map

- **Application of technology (Band):** real rooms, @mention routing, agent-to-
  agent handoffs, cross-agent memory, task/thought events, peer recruitment,
  cross-framework adapters. Directly hits every word of the rubric.
- **Presentation:** control-tower dashboard + side-by-side real Band room +
  90-sec narrated flow; mode badge keeps it honest.
- **Business value:** compresses multi-department vendor approval into one
  auditable room; quantified spend exposure, readiness, cycle compression.
- **Originality:** adversarial veto loop + shared-memory steward +
  cross-framework + tamper-evident seal — beyond linear automation and beyond
  the GateKeeper competitor.

---

## 8. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Band API/SDK drift | All calls in one client; verify against live docs before build; pin SDK version. |
| Live demo flakiness | Rehearsal mode badged + recorded backup video of a real run. |
| 8 processes hard to run live | `launch_band_room.py` + a single `run_all_agents` helper; record once, replay video. |
| Mentions/participants 422s | Use real handles/UUIDs from `agent_config.yaml`; never generic names like "User". |
| Secrets leakage | `.env.local`, `agent_config.yaml` gitignored; client never logs keys; pre-commit grep. |
| Cost | Compact prompts; AI/ML API; cap max_tokens; rehearsal mode is free. |

---

## 9. Definition of done

- [ ] 8 real Band External Agents registered; `agent_config.yaml` populated.
- [ ] One command launches a real room and the agents collaborate end-to-end.
- [ ] Dashboard renders that real room live and scores it from real data.
- [ ] Red-team veto loop demonstrably changes the outcome on a high-risk case.
- [ ] Evidence bundle + audit seal generated from the real transcript.
- [ ] Recorded demo shows Band room + control tower together.
- [ ] README/slides/submission form/judging map all describe real Band.
- [ ] Secrets clean; smoke + verify pass for both modes.
