# ProcureGuard AI Lablab Submission Packet

Use this file as the copy-paste source for the lablab.ai submission form after the public repository, hosted URL, and video URL are ready.

## Project Title

ProcureGuard AI

## Short Description

ProcureGuard is a vendor approval workspace where procurement, finance, security, legal, and approval roles review the same request in a shared Band room, exchange context, challenge gaps, and produce an auditable decision packet for human signoff.

## Long Description

ProcureGuard turns enterprise vendor approval into a shared Band review room — and it runs on the real Band platform, not a simulation. The Intake Coordinator agent creates a real Band chat room with its own agent key, recruits its sibling agents as room participants, and routes every handoff as a real Band message with @mention routing (each message returns a Band-issued UUID). Vendor Research, Finance ROI, Security Compliance, and Legal Policy review the case in parallel and hand off structured findings — each grounded in cited evidence from real case fields — to the Evidence Clerk. The Evidence Clerk builds one shared context packet with consensus, unresolved questions, and a readiness score. A Red Team Auditor challenges the packet before approval and can issue a binding veto that deterministically forces escalation, routing objections back to Security and Legal. The Approval Manager synthesizes the audit trail into an approve, conditional approve, reject, or escalate recommendation, then routes the packet to a Human Procurement Lead.

The agents are genuinely cross-framework: roles run on LangGraph, CrewAI, Pydantic AI, and Anthropic adapters, all collaborating in one Band room — Band's signature capability. The dashboard makes the review visible: a Live Band Proof panel with the real room link, message IDs, and event counts; room timeline; coordination handoff map; task state and recruitment ledger; business impact metrics; governance controls; shared context packet; red-team challenge; human gate; framework profiles; SHA-256 audit seal; downloadable Markdown report; and evidence bundle ZIP. Reviewers can run the prepared VectorCRM case or enter a custom vendor request to replay the same governance workflow on new inputs. When Band credentials are absent, a labelled local simulator keeps the demo reliable without ever falsely claiming a live run.

This is designed for Track 1: Internal Enterprise Workflows. It addresses a real enterprise problem: vendor approvals often stall because procurement, finance, security, legal, and operations work in separate tools. ProcureGuard compresses that process into one auditable decision room while improving risk visibility, control ownership, human review, and leadership-ready reporting.

## Technology Tags

Band, AI/ML API, Multi-Agent, Enterprise Workflow, Procurement, Compliance, FastAPI, Human-in-the-loop, Agent Coordination, Governance, Audit Trail

## Track

Track 1: Internal Enterprise Workflows

## Main Demo Flow

1. Open the dashboard (Band live mode enabled).
2. Run the VectorCRM case.
3. Show the Live Band Proof panel: the "LIVE on app.band.ai" tag, the clickable real room link, real Band message IDs, and task-event counts.
4. Open the real Band room in a new tab to show the same conversation on app.band.ai.
5. Show the Coordination Handoff Map with routed @mention edges.
6. Show Specialist Handoffs with per-finding cited evidence grounded in real case fields.
7. Show Task State & Recruitment, Business Impact & Controls (spend exposure, readiness, blocked controls).
8. Show the Shared Context Packet and the Red Team Challenge issuing a binding veto that flips the decision to escalate.
9. Show the Human Approval Gate and the Framework & Audit Record with the SHA-256 digest.
10. Download the run report and evidence bundle; show `docs/proof/` committed proof of the live run.

## Required URLs To Fill Before Submission

- Public GitHub Repository: `https://github.com/theihtisham/procureguard-ai-band-agents`
- Demo Application URL: `TODO`
- Video Presentation URL/file: `https://github.com/theihtisham/procureguard-ai-band-agents/blob/main/output/submission/procureguard-demo.webm`
- Slide Presentation URL or PDF: `TODO`

## Local Artifacts

- Cover image: `output/submission/procureguard-cover.png`
- Slides preview: `output/submission/procureguard-slides-preview.png`
- Demo video: `output/submission/procureguard-demo.webm`
- Public-safe package: `output/submission/procureguard-public-submission-package.zip`
- Latest report: `output/submission/procureguard-latest-report.md`
- Evidence bundle: `output/submission/procureguard-evidence-bundle-latest.zip`

## Final Local Commands

```powershell
uv run python scripts/verify_submission.py
uv run python scripts/final_submission_audit.py
uv run python scripts/build_submission_package.py
```
