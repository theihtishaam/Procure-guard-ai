# ProcureGuard AI Lablab Submission Packet

Use this file as the copy-paste source for the lablab.ai submission form after the public repository, hosted URL, and video URL are ready.

## Project Title

ProcureGuard AI

## Short Description

ProcureGuard AI is a Band-powered vendor approval room where eight AI agents coordinate procurement, finance, security, legal, evidence consolidation, adversarial review, and approval management to produce an auditable enterprise decision with human signoff.

## Long Description

ProcureGuard AI turns enterprise vendor approval into a collaborative Band room. An Intake Coordinator opens a purchase request, recruits specialized peer agents with @mentions, and preserves a shared room record. Vendor Research, Finance ROI, Security Compliance, and Legal Policy agents review the case in parallel, then hand off structured artifacts to the Evidence Clerk Agent. The Evidence Clerk creates a shared context packet with consensus, unresolved questions, readiness score, and state. A Red Team Auditor challenges the packet before approval, routes objections back to Security and Legal when needed, and hands the reviewed packet to the Approval Manager. The Approval Manager synthesizes the full audit trail into an approve, conditional approve, reject, or escalate decision, then routes the final packet to a Human Procurement Lead.

The dashboard makes the collaboration visible: Band room timeline, coordination handoff map, task state and recruitment ledger, business impact metrics, governance control matrix, shared context packet, red-team challenge, human gate, framework profiles, SHA-256 audit seal, downloadable Markdown report, and evidence bundle ZIP. Judges can run the prepared VectorCRM case or enter a custom vendor request to see the same multi-agent governance workflow replay on new inputs.

This is designed for Track 1: Internal Enterprise Workflows. It addresses a real enterprise problem: vendor approvals often stall because procurement, finance, security, legal, and operations work in separate tools. ProcureGuard compresses that process into one auditable decision room while improving risk visibility, control ownership, human review, and leadership-ready reporting.

## Technology Tags

Band, AI/ML API, Multi-Agent, Enterprise Workflow, Procurement, Compliance, FastAPI, Human-in-the-loop, Agent Coordination, Governance, Audit Trail

## Track

Track 1: Internal Enterprise Workflows

## Main Demo Flow

1. Open the dashboard.
2. Enable Fast demo mode for reliable recording.
3. Run the VectorCRM case.
4. Show the Coordination Handoff Map with routed @mention edges.
5. Show Task State & Recruitment with owners, status, and peer routing.
6. Show Business Impact & Controls with spend exposure, readiness, gate outcome, and blocked controls.
7. Show Shared Context Packet and Red Team Challenge.
8. Show Framework & Audit Proof with SHA-256 digest.
9. Download the run report and evidence bundle.
10. Include real Band Remote Agent room proof from `docs/band_live_setup.md` in the final video.

## Required URLs To Fill Before Submission

- Public GitHub Repository: `TODO`
- Demo Application URL: `TODO`
- Video Presentation URL: `TODO`
- Slide Presentation URL or PDF: `TODO`

## Local Artifacts

- Cover image: `output/submission/procureguard-cover.png`
- Slides preview: `output/submission/procureguard-slides-preview.png`
- Public-safe package: `output/submission/procureguard-public-submission-package.zip`
- Latest report: `output/submission/procureguard-latest-report.md`
- Evidence bundle: `output/submission/procureguard-evidence-bundle-latest.zip`

## Final Local Commands

```powershell
uv run python scripts/verify_submission.py
uv run python scripts/final_submission_audit.py
uv run python scripts/build_submission_package.py
```
