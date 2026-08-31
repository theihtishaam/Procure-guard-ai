# ProcureGuard AI — Narrated Video Script

Target length: 2.5–3 minutes. Tool: Loom (screen + mic). Record in one take; small stumbles are fine.

## Before you hit record (setup checklist)

1. Open TWO browser tabs:
   - Tab A: the dashboard — `https://procureguard-ai-band-agents.onrender.com/` (or localhost in live mode for the real Band labels)
   - Tab B: your Band room at `app.band.ai` — open the most recent ProcureGuard room so real messages are visible
2. Have the VectorCRM case selected on the dashboard, not yet run.
3. Close Notepad/credential windows and anything personal — Loom captures the whole screen.
4. Mic check: speak normally, ~1 foot from mic.

Tip: `[SHOW: ...]` = what's on screen. Plain text = what you say out loud. Pause ~1s between sections.

---

## 0:00–0:20 — Hook (open on the LIVE Band room, not the dashboard)

[SHOW: Tab B — the real Band room at app.band.ai with agent messages visible]

"This is a real Band room, live on app.band.ai. Eight AI agents just reviewed a vendor purchase request together — not in a simulator, on the actual Band platform. I'm going to show you how they collaborate, challenge each other, and hand a human a sealed, auditable decision. This is ProcureGuard AI."

---

## 0:20–0:40 — The problem (why this matters)

[SHOW: Tab A — the dashboard, VectorCRM case visible, not yet run]

"Enterprise vendor approval is slow because it's fragmented — procurement, finance, security, and legal all review in separate tools, and nobody sees the whole picture. ProcureGuard turns that into one coordinated decision room on Band. Here's a real case: VectorCRM, a forty-two-thousand-dollar CRM tool that wants access to customer data."

---

## 0:40–1:10 — Run it + the agent team

[SHOW: Click "Run Review". As the timeline populates, scroll slowly through it.]

"I click Run Review. An Intake Coordinator opens a Band room and recruits its specialist peers by @mention — Vendor Research, Finance, Security Compliance, and Legal Policy. They review in parallel, then hand their findings to an Evidence Clerk. Watch the room timeline fill — every one of these is a real routed message between agents."

[SHOW: Scroll to the "Live Band Proof" panel showing room URL + message IDs]

"And here's the proof it's real Band: the room ID, ten real Band messages, seven task events — every one with a Band-issued ID."

---

## 1:10–1:40 — The differentiator: cited findings + the veto loop

[SHOW: Scroll to a specialist artifact card showing the evidence citations]

"What makes this trustworthy: every finding is cited — tied back to a specific field in the request, so there are no hallucinated claims."

[SHOW: Scroll to the Red Team Challenge panel]

"Then the part most systems don't have — a Red Team Auditor challenges the conclusion before approval. It can issue a binding veto. Watch: it found unresolved data-protection gaps, so it vetoed — and that deterministically forced the decision to escalate, even though the business case was strong. The system can overrule its own approval. That's a safety control, not a rubber stamp."

---

## 1:40–2:10 — Decision, human gate, audit seal

[SHOW: Scroll to the Decision Memo, then the Human Approval Gate]

"The Approval Manager synthesizes everything into a decision — here, escalate, with conditions — and routes it to a human procurement lead with the exact signoffs required. A human stays in control of the final call."

[SHOW: Scroll to the Framework & Audit Record / SHA-256 seal]

"And the whole record is sealed with a SHA-256 hash — tamper-evident. You can download the full report and an evidence bundle. This is an audit artifact a real procurement team could attach to a purchase order."

---

## 2:10–2:35 — The Band + cross-framework story (the technical win)

[SHOW: Tab B again — the real Band room, scroll through the agent messages]

"Back in the real Band room — this is the actual collaboration layer, not a notification feed. And the agents are genuinely cross-framework: LangGraph, CrewAI, Pydantic AI, and Anthropic, all joining one Band room. That's Band's signature capability — coordinating agents across different runtimes — and we're using it for real."

---

## 2:35–2:55 — Close

[SHOW: Tab A — dashboard top, full populated view]

"So that's ProcureGuard: eight cross-framework agents, collaborating on real Band, with cited evidence, an adversarial veto, a human gate, and a cryptographically sealed audit trail. It's not a report generator — it's a procurement decision court. Thanks for watching."

[SHOW: hold on the dashboard for ~2 seconds before stopping the recording]

---

## After recording

1. Loom gives you a link automatically — set sharing to "Anyone with the link".
2. Paste that link back and I'll put it in the submission form + lablab_submission_form.md.

## If you want to show the AI/ML API call (partner prize bonus)

If recording in live mode (localhost with keys), you can briefly mention:
"The agents' reasoning is powered by AI/ML API" while a specialist artifact renders. Optional, ~3 seconds, but it helps claim the partner prize.
