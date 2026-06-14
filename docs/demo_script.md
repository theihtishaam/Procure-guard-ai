# Demo Script

## 30-Second Pitch

ProcureGuard turns vendor approval into a shared review room. Instead of one black-box recommendation, the request moves through intake, vendor research, finance, security, legal, evidence stewardship, red-team review, and approval management. The result is a decision memo, human approval packet, and audit record showing who reviewed what, what context was handed off, and which approval conditions remain.

## 3-Minute Demo

1. Open the dashboard with `BAND_ENABLED=1` so the run executes on the real Band platform.
2. Run the VectorCRM case.
3. Open the **Live Band Proof** panel first and show:
   - the "LIVE on app.band.ai" tag,
   - the clickable Band room link,
   - the count of real Band messages and task events (each carries a Band-issued ID).
4. Open the Band room link in Band to show the same messages landing in the real platform.
5. Walk the Band-room timeline:
   - Coordinator opens the room and recruits its peers (real Agent API calls).
   - Four specialist roles review in parallel.
   - Each specialist sends a structured handoff to Evidence Clerk.
   - Evidence Clerk creates the shared context packet.
   - Red Team Auditor challenges the packet before approval.
   - Approval Manager records the decision.
6. Open a Specialist Handoff card and show the **per-finding evidence citations** grounded in real case fields.
7. Open the Red Team Challenge panel and show the veto flipping approve -> escalate.
8. Open the Coordination Handoff Map and show the routed @mention edges.
9. Open Task State & Recruitment, Business Impact & Controls, and the SHA-256 audit record.
10. Open the human approval gate, download the run report (includes the Band room ID + message IDs), and download the evidence bundle.

Fast local mode (`Fast local mode` checkbox) is available as a quota-safe fallback if the provider or network is unavailable mid-recording; it keeps the full workflow rendering while honestly labeling the run as a local simulation.

## What Reviewers Should Notice

- The workflow runs on the **real Band platform**: real room, real message IDs, real task events, verifiable in Band itself.
- Band-style collaboration is central to the workflow.
- Review roles exchange structured context before the final decision.
- The red-team review loop prevents a shallow one-pass approval.
- @Mention routing makes the collaboration visible and explainable.
- Task state and recruitment records show coordinated work, not only chat.
- Business impact and controls connect the workflow to enterprise value, spend risk, and governance.
- The exported report and audit seal turn chat into an enterprise record.
- The evidence bundle gives reviewers the raw run JSON, report, and audit manifest.
- The workflow maps to real enterprise procurement, security, finance, and legal operations.
- Fast local mode keeps the presentation stable while the same app still supports live provider calls.
