from __future__ import annotations

import asyncio
import hashlib
import json

from app.agents import AGENTS, SPECIALIST_AGENT_IDS, AgentRunner, agent_by_id
from app.band_session import BandSession
from app.config import get_settings
from app.llm import AIMLAPIClient
from app.models import (
    AgentArtifact,
    AgentProfile,
    AuditSeal,
    BusinessImpactMetric,
    CollaborationEvidence,
    GovernanceControl,
    PeerRecruitmentRecord,
    TaskStateItem,
    VendorCase,
    WorkflowRun,
)


HUMAN_PARTICIPANTS = ["Human Procurement Lead"]


class ProcureGuardWorkflow:
    def __init__(self, *, force_heuristic: bool = False) -> None:
        self.settings = get_settings()
        self.force_heuristic = force_heuristic
        self.llm = AIMLAPIClient(self.settings, force_disabled=force_heuristic)
        self.runner = AgentRunner(self.llm)

    async def run(self, case: VendorCase) -> WorkflowRun:
        participants = [agent.name for agent in AGENTS] + HUMAN_PARTICIPANTS
        role_to_name = {agent.agent_id: agent.name for agent in AGENTS}
        session = BandSession(
            settings=self.settings,
            room_name=f"ProcureGuard: {case.vendor_name} approval",
            participant_names=participants,
            role_to_name=role_to_name,
            subject_key=case.vendor_name,
        )
        await session.open()
        room = session
        prior_reviews = await session.recall_memories("Intake Coordinator")

        workflow = WorkflowRun(
            mode=session.mode,  # type: ignore[arg-type]
            case=case,
            room_name=session.room_name,
            band_room_id=session.room_id,
            band_room_url=session.room_url,
            participants=participants,
            agent_profiles=build_agent_profiles(),
            human_participants=HUMAN_PARTICIPANTS,
            provider="aimlapi" if self.llm.enabled else "heuristic",
        )

        await room.send(
            "Intake Coordinator",
            (
                f"Opening case {case.case_id} for {case.vendor_name}. "
                "@Vendor Research Agent @Finance ROI Agent @Security Compliance Agent @Legal Policy Agent "
                "review the shared intake and return structured handoff artifacts to @Evidence Clerk Agent."
            ),
            message_type="recruitment",
            payload={
                "case": case.model_dump(),
                "collaboration_pattern": "parallel specialist review followed by context consolidation",
                "band_action": "peer_recruitment_and_task_routing",
            },
        )

        if prior_reviews:
            await room.send(
                "Intake Coordinator",
                (
                    f"@Evidence Clerk Agent Band memory shows {len(prior_reviews)} prior review(s) for "
                    f"{case.vendor_name}. Recall that shared context before specialists re-review so we "
                    "build on the last decision instead of starting cold."
                ),
                message_type="context",
                payload={"prior_reviews": prior_reviews[:5], "band_action": "cross_session_memory_recall"},
                mentions=["Evidence Clerk Agent"],
            )

        artifacts = await self._run_specialists(case)
        for artifact in artifacts:
            await room.send(
                artifact.agent_name,
                f"@Evidence Clerk Agent Handoff complete. {artifact.summary}",
                message_type="handoff",
                payload={"artifact": artifact.model_dump()},
                mentions=["Evidence Clerk Agent"],
            )

        await room.send(
            "Intake Coordinator",
            "@Evidence Clerk Agent Consolidate all specialist handoffs into one shared context packet for decision review.",
            message_type="event",
            payload={"artifact_count": len(artifacts)},
            mentions=["Evidence Clerk Agent"],
        )
        context_packet = await self.runner.run_context_packet(case, artifacts)
        await room.memory(
            "Evidence Clerk Agent",
            content=(
                f"Shared context packet {context_packet.packet_id} for {case.vendor_name}. "
                f"Readiness {context_packet.readiness_score}/100. {context_packet.summary} "
                f"Consensus: {'; '.join(context_packet.consensus_points[:3])}. "
                f"Open questions: {'; '.join(context_packet.unresolved_questions[:3])}."
            ),
            thought="Persist consolidated specialist findings as shared cross-agent memory so the decision uses one source of truth.",
            tags=["procureguard", "context-packet", case.case_id],
        )
        await room.send(
            "Evidence Clerk Agent",
            (
                f"@Red Team Auditor Agent Shared context packet {context_packet.packet_id} is ready for adversarial review. "
                f"Readiness score: {context_packet.readiness_score}/100. {context_packet.summary}"
            ),
            message_type="context",
            payload={"context_packet": context_packet.model_dump()},
            mentions=["Red Team Auditor Agent"],
        )
        challenge_review = await self.runner.run_challenge_review(case, artifacts, context_packet)
        if challenge_review.veto_level != "none":
            await room.send(
                "Red Team Auditor Agent",
                (
                    "@Security Compliance Agent @Legal Policy Agent Challenge issued before approval. "
                    f"{challenge_review.summary}"
                ),
                message_type="challenge",
                payload={"challenge_review": challenge_review.model_dump(), "loop": "mitigation_request"},
                mentions=["Security Compliance Agent", "Legal Policy Agent"],
            )
            await room.send(
                "Security Compliance Agent",
                "@Red Team Auditor Agent Mitigation acknowledged: production access should wait for SOC 2 evidence, SSO, logging, and scoped roles.",
                message_type="challenge",
                payload={"mitigation": "security controls acknowledged"},
                mentions=["Red Team Auditor Agent"],
            )
            await room.send(
                "Legal Policy Agent",
                "@Red Team Auditor Agent Mitigation acknowledged: DPA, subprocessors, retention, and audit rights must be cleared before purchase order.",
                message_type="challenge",
                payload={"mitigation": "legal controls acknowledged"},
                mentions=["Red Team Auditor Agent"],
            )
        await room.send(
            "Red Team Auditor Agent",
            (
                f"@Approval Manager Agent Red-team review complete: {challenge_review.veto_level}. "
                f"Cleared to decide: {challenge_review.cleared_to_decide}."
            ),
            message_type="challenge",
            payload={"challenge_review": challenge_review.model_dump(), "loop": "decision_handoff"},
            mentions=["Approval Manager Agent"],
        )
        await room.send(
            "Intake Coordinator",
            "@Approval Manager Agent Use the shared context packet, source artifacts, and red-team challenge to synthesize a decision memo with conditions.",
            message_type="event",
            payload={
                "artifact_count": len(artifacts),
                "context_packet_id": context_packet.packet_id,
                "challenge_veto_level": challenge_review.veto_level,
            },
            mentions=["Approval Manager Agent"],
        )

        rehydrated = await room.rehydrate_context("Approval Manager Agent")
        decision = await self.runner.run_approval(case, artifacts, context_packet, challenge_review)
        await room.send(
            "Approval Manager Agent",
            f"Decision recorded: {decision.decision.replace('_', ' ')}. {decision.executive_summary}",
            message_type="decision",
            payload={"decision": decision.model_dump(), "context_messages_rehydrated": rehydrated},
        )
        human_gate = self.runner.build_human_gate(case, decision, context_packet, challenge_review)
        await room.send(
            "Approval Manager Agent",
            (
                f"@Human Procurement Lead Human gate status: {human_gate.gate_status}. "
                f"Required signoffs: {', '.join(human_gate.required_signoffs)}."
            ),
            message_type="approval_gate",
            payload={"human_gate": human_gate.model_dump()},
            mentions=["Human Procurement Lead"],
        )
        await room.send(
            "Human Procurement Lead",
            "Acknowledged. Approval packet is ready for leadership review after listed conditions are cleared.",
            message_type="approval_gate",
            payload={"status": "acknowledged"},
        )
        workflow.messages = room.messages
        workflow.artifacts = artifacts
        workflow.context_packet = context_packet
        workflow.challenge_review = challenge_review
        workflow.decision = decision
        workflow.human_gate = human_gate
        workflow.peer_recruitment = build_peer_recruitment(workflow)
        workflow.task_state = build_task_state(workflow)
        workflow.business_impact = build_business_impact(workflow)
        workflow.governance_controls = build_governance_controls(workflow)
        workflow.collaboration_evidence = build_collaboration_evidence(workflow)
        workflow.collaboration_score = score_collaboration(workflow.collaboration_evidence)
        workflow.audit_seal = build_audit_seal(workflow)
        await room.send(
            "Evidence Clerk Agent",
            f"Audit seal generated with SHA-256 digest {workflow.audit_seal.digest[:16]}... for the decision packet.",
            message_type="audit",
            payload={"audit_seal": workflow.audit_seal.model_dump(mode="json")},
        )
        await room.send(
            "Intake Coordinator",
            "Workflow closed with a complete Band-room audit trail, red-team review, audit seal, and approval memo.",
            message_type="event",
            payload={"status": "closed"},
        )
        workflow.messages = room.messages
        workflow.band_events = room.events
        workflow.band_memories = room.memories
        workflow.prior_reviews_recalled = len(prior_reviews)
        workflow.band_room_id = room.room_id
        workflow.band_room_url = room.room_url
        workflow.collaboration_evidence = build_collaboration_evidence(workflow)
        workflow.collaboration_score = score_collaboration(workflow.collaboration_evidence)
        await room.close()
        return workflow

    async def _run_specialists(self, case: VendorCase) -> list[AgentArtifact]:
        tasks = [self.runner.run_specialist(case, agent_by_id(agent_id)) for agent_id in SPECIALIST_AGENT_IDS]
        return list(await asyncio.gather(*tasks))


def build_agent_profiles() -> list[AgentProfile]:
    profiles = [
        AgentProfile(
            agent_id=agent.agent_id,
            name=agent.name,
            role=agent.title,
            framework_profile=agent.framework_profile,
            model_provider="AI/ML API" if agent.agent_id != "coordinator" else "AI/ML API + Band tools",
            coordination_style=agent.coordination_style,
        )
        for agent in AGENTS
    ]
    profiles.append(
        AgentProfile(
            agent_id="human_procurement_lead",
            name="Human Procurement Lead",
            role="Human approver",
            framework_profile="Band human participant",
            model_provider="Human-in-the-loop",
            coordination_style="approval gate",
        )
    )
    return profiles


def build_peer_recruitment(workflow: WorkflowRun) -> list[PeerRecruitmentRecord]:
    return [
        PeerRecruitmentRecord(
            recruiter="Intake Coordinator",
            peer="Vendor Research Agent",
            reason="Validate vendor maturity, diligence gaps, and operating fit.",
            band_action="@mention routed peer recruitment into the procurement room",
            status="joined",
        ),
        PeerRecruitmentRecord(
            recruiter="Intake Coordinator",
            peer="Finance ROI Agent",
            reason="Review spend exposure, pilot economics, and renewal guardrails.",
            band_action="@mention routed peer recruitment into the procurement room",
            status="joined",
        ),
        PeerRecruitmentRecord(
            recruiter="Intake Coordinator",
            peer="Security Compliance Agent",
            reason="Review data access, integrations, controls, and compliance risk.",
            band_action="@mention routed peer recruitment into the procurement room",
            status="joined",
        ),
        PeerRecruitmentRecord(
            recruiter="Intake Coordinator",
            peer="Legal Policy Agent",
            reason="Review DPA, subprocessors, retention, audit rights, and approval authority.",
            band_action="@mention routed peer recruitment into the procurement room",
            status="joined",
        ),
        PeerRecruitmentRecord(
            recruiter="Intake Coordinator",
            peer="Evidence Clerk Agent",
            reason="Consolidate specialist outputs into one shared context packet.",
            band_action="@mention routed context stewardship assignment",
            status="joined",
        ),
        PeerRecruitmentRecord(
            recruiter="Evidence Clerk Agent",
            peer="Red Team Auditor Agent",
            reason="Challenge the shared packet before a decision is made.",
            band_action="@mention routed adversarial review handoff",
            status="routed",
        ),
        PeerRecruitmentRecord(
            recruiter="Red Team Auditor Agent",
            peer="Approval Manager Agent",
            reason="Hand off the challenged packet for decision synthesis.",
            band_action="@mention routed decision handoff",
            status="routed",
        ),
        PeerRecruitmentRecord(
            recruiter="Approval Manager Agent",
            peer="Human Procurement Lead",
            reason="Route the final approval packet to accountable human signoff.",
            band_action="@mention routed human approval gate",
            status="routed",
        ),
    ]


def build_task_state(workflow: WorkflowRun) -> list[TaskStateItem]:
    gate_status = workflow.human_gate.gate_status if workflow.human_gate else "blocked"
    human_status = "human_review" if gate_status == "ready_for_human" else "blocked" if gate_status == "blocked" else "complete"
    return [
        TaskStateItem(
            task_id="intake",
            label="Open procurement room",
            owner="Intake Coordinator",
            status="complete",
            summary=f"Case {workflow.case.case_id} opened for {workflow.case.vendor_name}.",
            evidence_refs=["recruitment message", "case payload"],
        ),
        TaskStateItem(
            task_id="recruit_peers",
            label="Recruit specialist peers",
            owner="Intake Coordinator",
            status="complete" if len(workflow.peer_recruitment) >= 5 else "active",
            summary=f"{len(workflow.peer_recruitment)} peer routing records created through Band-style mentions.",
            evidence_refs=["peer_recruitment", "handoff map"],
        ),
        TaskStateItem(
            task_id="specialist_review",
            label="Parallel specialist review",
            owner="Vendor, Finance, Security, Legal",
            status="complete" if len(workflow.artifacts) >= 4 else "active",
            summary=f"{len(workflow.artifacts)} structured handoff artifacts returned to Evidence Clerk.",
            evidence_refs=[artifact.agent_name for artifact in workflow.artifacts],
        ),
        TaskStateItem(
            task_id="context_packet",
            label="Build shared context packet",
            owner="Evidence Clerk Agent",
            status="complete" if workflow.context_packet else "queued",
            summary=(
                f"Packet {workflow.context_packet.packet_id} readiness {workflow.context_packet.readiness_score}/100."
                if workflow.context_packet
                else "Context packet has not been created."
            ),
            evidence_refs=["context_packet", "shared_state"],
        ),
        TaskStateItem(
            task_id="red_team",
            label="Challenge before decision",
            owner="Red Team Auditor Agent",
            status="complete" if workflow.challenge_review else "queued",
            summary=(
                f"Challenge level {workflow.challenge_review.veto_level}; cleared={workflow.challenge_review.cleared_to_decide}."
                if workflow.challenge_review
                else "Challenge review has not run."
            ),
            evidence_refs=["challenge_review", "mitigation loop"],
        ),
        TaskStateItem(
            task_id="decision",
            label="Synthesize decision memo",
            owner="Approval Manager Agent",
            status="complete" if workflow.decision else "queued",
            summary=(
                f"Decision {workflow.decision.decision} with score {workflow.decision.score}/100."
                if workflow.decision
                else "Decision memo has not been created."
            ),
            evidence_refs=["decision", "risk_register"],
        ),
        TaskStateItem(
            task_id="human_gate",
            label="Route human approval gate",
            owner="Human Procurement Lead",
            status=human_status,
            summary=(
                f"Gate status {workflow.human_gate.gate_status}; signoffs: {', '.join(workflow.human_gate.required_signoffs)}."
                if workflow.human_gate
                else "Human approval gate has not been reached."
            ),
            evidence_refs=["human_gate", "approval_packet"],
        ),
    ]


def build_business_impact(workflow: WorkflowRun) -> list[BusinessImpactMetric]:
    spend = workflow.case.requested_amount_usd
    avg_risk = round(sum(artifact.risk_score for artifact in workflow.artifacts) / len(workflow.artifacts)) if workflow.artifacts else 0
    blocker_count = sum(len(artifact.blockers) for artifact in workflow.artifacts)
    readiness = workflow.context_packet.readiness_score if workflow.context_packet else 0
    decision_label = workflow.decision.decision.replace("_", " ") if workflow.decision else "pending"
    gate_label = workflow.human_gate.gate_status.replace("_", " ") if workflow.human_gate else "pending"
    potential_exposure = min(spend, round(spend * max(avg_risk, 1) / 100))
    return [
        BusinessImpactMetric(
            label="Approval cycle compression",
            value="Same-session packet",
            baseline="Separate procurement, finance, security, and legal queues",
            impact="Parallel agent review turns fragmented review into one synchronized decision room.",
            owner="Intake Coordinator",
        ),
        BusinessImpactMetric(
            label="Spend exposure under review",
            value=f"${potential_exposure:,.0f}",
            baseline=f"${spend:,.0f} request with {avg_risk}/100 average specialist risk",
            impact="Finance and approval controls keep exposed spend visible before purchase order.",
            owner="Finance ROI Agent",
        ),
        BusinessImpactMetric(
            label="Decision readiness",
            value=f"{readiness}/100",
            baseline="Manual evidence gathering with unclear missing items",
            impact=f"Evidence Clerk exposes {blocker_count} blocker(s) and the final decision is {decision_label}.",
            owner="Evidence Clerk Agent",
        ),
        BusinessImpactMetric(
            label="Governance outcome",
            value=gate_label,
            baseline="Approvals often proceed without a single auditable gate",
            impact="Human gate records required signoffs and prevents unsafe auto-approval.",
            owner="Human Procurement Lead",
        ),
    ]


def build_governance_controls(workflow: WorkflowRun) -> list[GovernanceControl]:
    challenge = workflow.challenge_review
    gate = workflow.human_gate
    decision = workflow.decision
    packet = workflow.context_packet
    high_risk = any(artifact.risk_score >= 65 for artifact in workflow.artifacts)
    has_data_access = bool(workflow.case.data_access)
    blocked_gate = gate and gate.gate_status == "blocked"
    return [
        GovernanceControl(
            control_id="CTRL-001",
            area="Security evidence",
            owner="Security Compliance Agent",
            status="blocked" if high_risk or blocked_gate else "conditional",
            evidence="Security artifact, red-team objections, and SOC 2/DPA conditions are attached to the run.",
            next_action="Attach SOC 2, SSO, logging, deletion, and scoped-role evidence before production access.",
        ),
        GovernanceControl(
            control_id="CTRL-002",
            area="Legal/privacy review",
            owner="Legal Policy Agent",
            status="blocked" if has_data_access or blocked_gate else "conditional",
            evidence="Legal artifact and challenge loop record DPA, subprocessors, retention, and audit-right gaps.",
            next_action="Complete DPA and subprocessor review before purchase order.",
        ),
        GovernanceControl(
            control_id="CTRL-003",
            area="Commercial approval",
            owner="Finance ROI Agent",
            status="conditional" if decision and decision.decision in {"conditional_approve", "escalate"} else "human_review",
            evidence=f"Spend request ${workflow.case.requested_amount_usd:,.0f}, ROI review, decision score, and pilot conditions are preserved.",
            next_action="Approve only with pilot caps, success metrics, renewal guardrails, and exit criteria.",
        ),
        GovernanceControl(
            control_id="CTRL-004",
            area="Adversarial challenge",
            owner="Red Team Auditor Agent",
            status="satisfied" if challenge else "blocked",
            evidence=(
                f"Challenge level {challenge.veto_level}; cleared to decide={challenge.cleared_to_decide}."
                if challenge
                else "No red-team challenge recorded."
            ),
            next_action="Keep challenge review mandatory before Approval Manager synthesis.",
        ),
        GovernanceControl(
            control_id="CTRL-005",
            area="Decision auditability",
            owner="Evidence Clerk Agent",
            status="satisfied" if packet and workflow.audit_seal else "conditional",
            evidence="Run JSON, report, task state, recruitment ledger, timeline, and audit seal are bundled.",
            next_action="Attach evidence bundle to the procurement ticket and preserve digest for later review.",
        ),
    ]


def build_collaboration_evidence(workflow: WorkflowRun) -> list[CollaborationEvidence]:
    messages = workflow.messages
    agent_names = {agent.name for agent in AGENTS}
    active_agents = {message.sender for message in messages if message.sender in agent_names}
    mentioned_agents = {
        mention
        for message in messages
        for mention in message.mentions
        if mention in agent_names or mention in workflow.human_participants
    }
    handoffs = [message for message in messages if message.message_type == "handoff"]
    context_messages = [message for message in messages if message.message_type == "context"]
    gate_messages = [message for message in messages if message.message_type == "approval_gate"]
    challenge_messages = [message for message in messages if message.message_type == "challenge"]
    audit_messages = [message for message in messages if message.message_type == "audit"]
    recruitment_messages = [message for message in messages if message.message_type == "recruitment"]
    completed_tasks = [task for task in workflow.task_state if task.status in {"complete", "blocked", "human_review"}]
    impact_metrics = workflow.business_impact
    controls = workflow.governance_controls
    structured_payloads = [message for message in messages if message.payload]
    framework_profiles = {profile.framework_profile for profile in workflow.agent_profiles}
    return [
        CollaborationEvidence(
            label="Minimum 3 agents",
            status="met" if len(active_agents) >= 3 else "missing",
            detail=f"{len(active_agents)} agents actively sent messages in the room.",
        ),
        CollaborationEvidence(
            label="Band-style @mention routing",
            status="met" if len(mentioned_agents) >= 3 else "partial",
            detail=f"{len(mentioned_agents)} participants were explicitly routed through @mentions.",
        ),
        CollaborationEvidence(
            label="Agent-to-agent handoffs",
            status="met" if len(handoffs) >= 3 else "partial",
            detail=f"{len(handoffs)} specialist handoff messages were posted before the decision.",
        ),
        CollaborationEvidence(
            label="Shared structured context",
            status="met" if workflow.context_packet and context_messages else "missing",
            detail="Evidence Clerk created a shared packet from specialist artifacts before manager synthesis.",
        ),
        CollaborationEvidence(
            label="Task state coordination",
            status="met" if len(completed_tasks) >= 6 else "partial",
            detail=f"{len(completed_tasks)} task-state records show owners, status, and evidence references.",
        ),
        CollaborationEvidence(
            label="Peer recruitment path",
            status="met" if len(workflow.peer_recruitment) >= 6 and recruitment_messages else "partial",
            detail=f"{len(workflow.peer_recruitment)} peer recruitment/routing records document how agents were brought into the room.",
        ),
        CollaborationEvidence(
            label="Adversarial review loop",
            status="met" if workflow.challenge_review and len(challenge_messages) >= 2 else "partial",
            detail=(
                f"Red Team Auditor issued {workflow.challenge_review.veto_level if workflow.challenge_review else 'no'} "
                "challenge review before approval."
            ),
        ),
        CollaborationEvidence(
            label="Decision uses prior artifacts",
            status="met" if workflow.decision and workflow.artifacts else "missing",
            detail=f"Approval Manager used {len(workflow.artifacts)} artifacts plus the shared context packet.",
        ),
        CollaborationEvidence(
            label="Human enterprise gate",
            status="met" if workflow.human_gate and gate_messages else "partial",
            detail="The final recommendation is routed to a human procurement lead with required signoffs.",
        ),
        CollaborationEvidence(
            label="Business impact model",
            status="met" if len(impact_metrics) >= 4 else "partial",
            detail=f"{len(impact_metrics)} business impact metrics connect the collaboration to cycle time, spend, readiness, and governance.",
        ),
        CollaborationEvidence(
            label="Governance control matrix",
            status="met" if len(controls) >= 5 else "partial",
            detail=f"{len(controls)} controls map security, legal, commercial, challenge, and audit readiness.",
        ),
        CollaborationEvidence(
            label="Unified audit trail",
            status="met" if len(messages) >= 8 and len(structured_payloads) >= 5 else "partial",
            detail=f"{len(messages)} messages and {len(structured_payloads)} structured payloads are preserved.",
        ),
        CollaborationEvidence(
            label="Cross-framework profile",
            status="met" if len(framework_profiles) >= 5 else "partial",
            detail=f"{len(framework_profiles)} framework/runtime profiles are documented for Band live deployment.",
        ),
        CollaborationEvidence(
            label="Tamper-evident audit seal",
            status="met" if workflow.audit_seal or audit_messages else "partial",
            detail=(
                f"SHA-256 seal {workflow.audit_seal.digest[:16]}... anchors the packet."
                if workflow.audit_seal
                else "Audit seal message not found."
            ),
        ),
    ]


def score_collaboration(evidence: list[CollaborationEvidence]) -> int:
    if not evidence:
        return 0
    values = {"met": 100, "partial": 55, "missing": 0}
    return round(sum(values[item.status] for item in evidence) / len(evidence))


def build_audit_seal(workflow: WorkflowRun) -> AuditSeal:
    payload = {
        "case": workflow.case.model_dump(mode="json"),
        "artifacts": [artifact.model_dump(mode="json") for artifact in workflow.artifacts],
        "context_packet": workflow.context_packet.model_dump(mode="json") if workflow.context_packet else None,
        "challenge_review": workflow.challenge_review.model_dump(mode="json") if workflow.challenge_review else None,
        "decision": workflow.decision.model_dump(mode="json") if workflow.decision else None,
        "human_gate": workflow.human_gate.model_dump(mode="json") if workflow.human_gate else None,
        "task_state": [task.model_dump(mode="json") for task in workflow.task_state],
        "peer_recruitment": [record.model_dump(mode="json") for record in workflow.peer_recruitment],
        "business_impact": [metric.model_dump(mode="json") for metric in workflow.business_impact],
        "governance_controls": [control.model_dump(mode="json") for control in workflow.governance_controls],
        "messages": [message.model_dump(mode="json") for message in workflow.messages],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return AuditSeal(
        digest=hashlib.sha256(encoded).hexdigest(),
        sealed_scope="case+artifacts+context+challenge+decision+human_gate+task_state+peer_recruitment+business_impact+governance_controls+timeline",
        record_count=(
            len(workflow.messages)
            + len(workflow.artifacts)
            + len(workflow.task_state)
            + len(workflow.peer_recruitment)
            + len(workflow.business_impact)
            + len(workflow.governance_controls)
            + 4
        ),
    )
