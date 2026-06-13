# ProcureGuard AI

## Short Description

ProcureGuard AI is a Band-powered vendor approval room where eight AI agents collaborate across procurement, finance, security, legal, evidence consolidation, adversarial review, and management to produce an auditable enterprise approval decision with a human signoff gate.

## Long Description

Enterprise vendor approval is slow because the work is split across departments, tools, and approval chains. ProcureGuard AI turns that process into a collaborative Band room. An Intake Coordinator opens a case, recruits specialist agents with @mentions, and preserves shared context. Vendor Research, Finance ROI, Security Compliance, and Legal Policy agents review the case in parallel and hand off structured artifacts to the Evidence Clerk Agent. The Evidence Clerk creates a shared context packet with consensus, unresolved questions, readiness score, and shared state. A Red Team Auditor challenges the packet before approval, routes objections back to security/legal when needed, and then hands the reviewed packet to the Approval Manager. The Approval Manager synthesizes the audit trail into a final approve, conditional approve, reject, or escalate decision, then routes the approval packet to a Human Procurement Lead.

Band is central to the workflow. The agents coordinate through a room, use @mention routing, exchange structured context, hand off tasks, challenge unsafe assumptions, and leave a unified audit trail. The dashboard visualizes the same collaboration as an enterprise workflow: case intake, participants, room timeline, agent artifacts, shared context packet, red-team challenge, framework profile, SHA-256 audit seal, judging evidence, human gate, risk register, conditions, downloadable report, and final memo.

The competitive angle is governance replay, not simple vendor scoring. Judges can run the prepared case or enter a new vendor, watch the routed handoff graph form from actual @mentions, inspect the red-team veto loop, review business-impact and control metrics, and download a ZIP containing the raw run JSON, report, audit manifest, and seal. Fast demo mode keeps recordings reliable, while the live AI/ML API and Band setup paths remain available for provider-backed proof.

## Track

Track 1: Internal Enterprise Workflows

## Core Agents

- Intake Coordinator
- Vendor Research Agent
- Finance ROI Agent
- Security Compliance Agent
- Legal Policy Agent
- Evidence Clerk Agent
- Red Team Auditor Agent
- Approval Manager Agent
- Human Procurement Lead gate

## Tech Stack

- Python
- FastAPI
- AI/ML API with OpenAI-compatible chat completions
- Band SDK live-mode bridge
- Local Band-room simulator for reliable demo rehearsal
- Static enterprise dashboard
- SHA-256 audit seal and Markdown report export
- Evidence bundle ZIP export with raw run JSON and audit manifest
- Business-impact and governance-control matrix
- Fast demo mode for stable recordings and quota-safe judge rehearsal

## Demo Case

VectorCRM: AI-assisted CRM enrichment and lead routing for Revenue Operations. The vendor touches customer contacts, opportunity notes, email metadata, Salesforce, HubSpot, and Slack. Agents must decide whether to approve, conditionally approve, reject, or escalate.
