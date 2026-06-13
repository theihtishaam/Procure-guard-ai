# Submission Checklist

## Basic Information

- Project title: `ProcureGuard AI`
- Short description: use `docs/submission.md`
- Long description: use `docs/submission.md`
- Tags: `Band`, `AI/ML API`, `Multi-Agent`, `Enterprise Workflow`, `Procurement`, `Compliance`, `FastAPI`, `Human-in-the-loop`

## Cover And Presentation

- Cover image: `output/submission/procureguard-cover.png`
- Slide deck: `http://127.0.0.1:8765/static/slides.html`
- Public-safe package: `output/submission/procureguard-public-submission-package.zip`
- Package manifest: `output/submission/procureguard-public-submission-manifest.json`
- Demo script: `docs/demo_script.md`
- Copy-paste submission packet: `docs/lablab_submission_form.md`
- Suggested video length: 3 minutes

## App And Code

- Local app URL: `http://127.0.0.1:8765`
- Deploy config: `render.yaml`
- Docker config: `Dockerfile`
- Public repository: https://github.com/theihtisham/procureguard-ai-band-agents

## Demo Proof To Show

- Agent Board with 8 AI agents plus Human Procurement Lead.
- Band Room Timeline with @mentions and 17-message audit trail.
- Shared Context Packet from Evidence Clerk.
- Red Team Challenge with cleared/not-cleared state.
- Decision Memo with escalation guardrail.
- Human Approval Gate with blocked or ready status.
- Coordination Handoff Map showing routed @mention edges.
- Task State & Recruitment board showing owners, statuses, evidence references, and peer routing.
- Business Impact & Controls panel showing cycle-time value, spend exposure, readiness, gate outcome, and control status.
- Framework & Audit Proof with SHA-256 seal.
- Download Run Report export.
- Download Evidence Bundle export.
- Custom Case panel for a judge-entered vendor.
- Fast demo mode for reliable recording and quota-safe rehearsals.

## Final Local Commands

```powershell
uv run python scripts/verify_submission.py
uv run python scripts/final_submission_audit.py
uv run python scripts/build_submission_package.py
```

## Required Final Step

Before final submission, record a real Band room using `docs/band_live_setup.md`. If you have a Band human API key, create remote agents with:

```powershell
uv run python scripts/register_band_agents.py --confirm-create
```

The local simulator is useful for reliable product demo, but the video should include proof that real Band Remote Agents can join a room and hand off work.
