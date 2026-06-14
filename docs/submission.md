# ProcureGuard AI

## Short Description

ProcureGuard AI is a Band-powered vendor approval room where eight AI agents collaborate across procurement, finance, security, legal, evidence consolidation, adversarial review, and management to produce an auditable enterprise approval decision with a human signoff gate.

## Long Description

Enterprise vendor approval is slow because the work is split across departments, tools, and approval chains. ProcureGuard AI turns that process into a collaborative Band room. An Intake Coordinator opens a case, recruits specialist agents with @mentions, and preserves shared context. Vendor Research, Finance ROI, Security Compliance, and Legal Policy agents review the case in parallel and hand off structured artifacts to the Evidence Clerk Agent. The Evidence Clerk creates a shared context packet with consensus, unresolved questions, readiness score, and shared state. A Red Team Auditor challenges the packet before approval, routes objections back to security/legal when needed, and then hands the reviewed packet to the Approval Manager. The Approval Manager synthesizes the audit trail into a final approve, conditional approve, reject, or escalate decision, then routes the approval packet to a Human Procurement Lead.

Band is the actual coordination layer, not a wrapper. In live mode the system creates a real Band chat room through the Human API, adds every agent as a room participant, posts each routed handoff as a real Band message with @mentions (returning real Band message IDs and recipients), emits broadcasts and status as real Band task events, stores the Evidence Clerk's shared context packet as a real cross-agent Band memory, and rehydrates room context through the Band Agent API before the decision. The eight agents are genuinely cross-framework: they run on LangGraph, CrewAI, Pydantic AI, and Anthropic adapters and discover each other in one shared room with no hardcoded agent-to-agent wiring, which is Band's signature capability.

The dashboard visualizes the collaboration as an enterprise workflow and includes a Live Band Proof panel showing the clickable Band room link, routed-message count with real Band IDs, task-event count, shared-memory count, and participant list. The other surfaces cover case intake, room timeline, agent artifacts, shared context packet, red-team challenge, cross-framework profile, SHA-256 audit seal, judging evidence, human gate, risk register, conditions, downloadable report, and final memo.

The competitive angle is governance replay on real cross-framework infrastructure, not simple vendor scoring. Judges can run the prepared case or enter a new vendor, watch the routed handoff graph form from actual @mentions, inspect the red-team veto loop, review business-impact and control metrics, and download a ZIP containing the raw run JSON, report, audit manifest, and seal. A reliable local Band simulation mode keeps recordings stable when credentials are absent, and is labeled honestly in the UI so judges always know whether a run hit the live platform.

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
- Real Band platform: Human API (rooms, participants), Agent API (messages, task events, cross-agent memories, context rehydration)
- Band SDK (thenvoi) cross-framework agents: LangGraph, CrewAI, Pydantic AI, Anthropic adapters
- AI/ML API with OpenAI-compatible chat completions
- Reliable local Band simulation mode, honestly labeled, for credential-free demo rehearsal
- Static enterprise dashboard with Live Band Proof panel
- SHA-256 audit seal and Markdown report export
- Evidence bundle ZIP export with raw run JSON and audit manifest
- Business-impact and governance-control matrix
- Fast demo mode for stable recordings and quota-safe judge rehearsal

## Demo Case

VectorCRM: AI-assisted CRM enrichment and lead routing for Revenue Operations. The vendor touches customer contacts, opportunity notes, email metadata, Salesforce, HubSpot, and Slack. Agents must decide whether to approve, conditionally approve, reject, or escalate.
