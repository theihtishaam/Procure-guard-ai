# Judging Map

This maps ProcureGuard directly to the four Band of Agents judging criteria. Every claim here is verifiable in the repo or in `docs/proof/`.

## 1. Application of Technology (how effectively Band is the coordination layer)

Band is the actual coordination layer, not a wrapper:

- The Intake Coordinator agent **creates a real Band room** with its own agent key (`POST /api/v1/agent/chats`) and **recruits its sibling agents** as room participants (`POST /api/v1/agent/chats/{id}/participants`). This is Band's "agents recruit each other" model, not hardcoded wiring.
- Specialist handoffs post as **real Band messages** with required `@mentions` (`POST /api/v1/agent/chats/{id}/messages`) and Band returns real message UUIDs and routed recipients.
- Broadcasts and status updates post as **real Band events** (`POST /api/v1/agent/chats/{id}/events`, `task` type — no mention required).
- Before the decision, the Approval Manager **rehydrates room context through Band** (`GET /api/v1/agent/chats/{id}/context`).
- The Evidence Clerk stores the shared context packet as a **cross-agent Band memory** (`POST /api/v1/agent/memories`, subject scope) so review state survives across sessions.

Proof: `docs/proof/` contains a captured live run (real room URL, 10 real message IDs, 7 real events) plus a dashboard screenshot showing "LIVE on app.band.ai". The messages were read back from Band's own context API to confirm delivery.

A deterministic local simulator with identical room semantics is the demo fallback. It is honestly labeled "Local Band simulation" in the UI and never claims to be live — when live prerequisites fail, the app falls back transparently instead of faking a live run.

## 2. Presentation

- Operational control-room dashboard, not a landing page: intake, participants, room timeline, handoff map, task/recruitment board, business impact, governance controls, shared context packet, red-team challenge, decision memo, human gate.
- A dedicated **Live Band Proof** panel surfaces the real room link, routed-message count, event count, shared-memory count, and an example Band message ID.
- Specialist artifacts show **per-finding evidence citations** grounded in specific case fields.
- Downloadable Markdown report and evidence ZIP for offline inspection.

## 3. Business Value

Procurement approvals stall because finance, security, legal, and operations work in separate tools. ProcureGuard makes the collaboration explicit, auditable, and reusable:

- Parallel specialist review compresses a multi-queue process into one synchronized room.
- A reproducible SHA-256 audit seal and downloadable evidence bundle attach to a purchase record.
- The business-impact model translates each run into cycle-time, spend-exposure, readiness, and gate-outcome metrics.
- The human approval gate enforces accountable signoff and blocks unsafe auto-approval.

## 4. Originality

- **Binding adversarial veto**: the Red Team Auditor can deterministically flip approve to escalate before the decision is final (`enforce_challenge_guardrails`). Most review agents only comment; ours can stop an approval.
- **Genuine cross-framework agents**: roles run on different `thenvoi` adapters (LangGraph, CrewAI, Pydantic AI, Anthropic) in one Band room, proving Band's cross-framework promise rather than just claiming it.
- **Cross-session vendor memory**: the same vendor maps to a stable Band memory subject, so a later review can recall the prior decision instead of starting cold.
- **Cited evidence**: every specialist finding is grounded in a real case field, making the audit trail defensible.

Positioning vs. the field: where a competitor scores vendors, ProcureGuard puts the score on trial through an adversarial review loop, then hands the human a cryptographically sealed, reproducible audit bundle. It is a procurement decision room, not a report generator.

## Honest limitations

- Band's Human API and Memory API require an Enterprise plan; on the hackathon Pro plan they return `403 plan_required`. ProcureGuard works around the room-creation gate using agent-side endpoints, so the live coordination path (rooms, messages, events, context) runs on the Pro plan. The cross-agent Memory feature is implemented and verified in simulation but degrades gracefully when the live Memory API is gated.
