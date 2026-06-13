# Judging Map

## Technology

- Eight role-specific AI agents plus one human approval gate.
- Shared room timeline with @mention routing and handoffs.
- Coordination Handoff Map derived from actual message mentions.
- Task State & Recruitment board with owner/status/evidence records.
- Business Impact & Controls panel tying collaboration to cycle time, spend exposure, readiness, and governance controls.
- AI/ML API provider adapter with deterministic fallback.
- Live Band runner for Remote Agents once credentials are configured.
- Structured JSON artifacts, shared context packet, red-team challenge review, human gate, audit seal, and final decision memo.
- Deterministic escalation guardrail when Red Team does not clear the packet for decision.
- Judging Evidence panel that maps each run to hackathon requirements.
- Fast demo mode that proves the same workflow can be replayed reliably without spending credits.

## Design

- Operational dashboard, not a landing page.
- Dense enterprise workflow view: intake, participants, timeline, artifacts, decision.
- Clear audit trail, challenge review, and digest proof for reviewers and leadership.
- Evidence bundle export for offline inspection by judges.

## Completion

- Local app runs without external Band credentials for rehearsal.
- Live Band setup path is documented.
- Smoke test verifies participant count, handoffs, context packet, red-team challenge, human gate, audit seal, collaboration score, artifacts, and decision output.

## Business Value

Procurement approvals often stall because finance, security, legal, and operations work in separate tools. ProcureGuard makes the collaboration explicit and auditable, reducing delay while improving governance and giving leadership a reusable approval packet. The business-impact model translates each run into cycle-time, spend exposure, readiness, and gate outcome metrics.

## Originality

The project uses Band as an enterprise approval room, not a generic agent chat or simple vendor-risk scorer. The Red Team Auditor, Evidence Clerk, handoff map, custom case replay, human gate, evidence bundle, and audit seal turn the workflow into a traceable governance artifact that a real team could attach to a purchase record.
