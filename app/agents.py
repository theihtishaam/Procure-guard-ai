from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from app.llm import AIMLAPIClient, LLMError
from app.models import (
    AgentArtifact,
    ApprovalDecision,
    ChallengeReview,
    ContextPacket,
    HumanApprovalGate,
    RiskRegisterItem,
    VendorCase,
)


@dataclass(frozen=True)
class AgentSpec:
    agent_id: str
    name: str
    title: str
    mission: str
    model_tier: str = "primary"
    framework_profile: str = "Custom Python"
    coordination_style: str = "room participant"


AGENTS: list[AgentSpec] = [
    AgentSpec(
        "coordinator",
        "Intake Coordinator",
        "Workflow owner",
        "Create the case, recruit the right peer agents, preserve shared context, and explain the handoff path.",
        "fast",
        "LangGraph adapter",
        "dynamic recruiter",
    ),
    AgentSpec(
        "vendor_research",
        "Vendor Research Agent",
        "Vendor intelligence analyst",
        "Assess vendor/product fit, market maturity, missing diligence evidence, and operational readiness.",
        "primary",
        "CrewAI-style specialist",
        "parallel specialist handoff",
    ),
    AgentSpec(
        "finance_roi",
        "Finance ROI Agent",
        "Finance and ROI analyst",
        "Evaluate budget fit, expected savings, total cost risk, procurement leverage, and measurable success criteria.",
        "fast",
        "PydanticAI-style structured analyst",
        "parallel specialist handoff",
    ),
    AgentSpec(
        "security_compliance",
        "Security Compliance Agent",
        "Security and compliance reviewer",
        "Assess data exposure, integrations, security controls, privacy posture, and required safeguards.",
        "primary",
        "LangGraph policy agent",
        "parallel specialist handoff",
    ),
    AgentSpec(
        "legal_policy",
        "Legal Policy Agent",
        "Legal and policy reviewer",
        "Review contract, DPA, regulated-data, retention, audit, and escalation concerns.",
        "primary",
        "Custom Agent API",
        "parallel specialist handoff",
    ),
    AgentSpec(
        "evidence_clerk",
        "Evidence Clerk Agent",
        "Shared context steward",
        "Turn specialist handoffs into a single shared context packet with consensus, unresolved questions, and readiness state.",
        "fast",
        "Band Agent API",
        "context steward",
    ),
    AgentSpec(
        "red_team_auditor",
        "Red Team Auditor Agent",
        "Adversarial control reviewer",
        "Challenge the shared context, identify unsafe assumptions, and force revisions or escalation before approval.",
        "primary",
        "Codeband-style reviewer",
        "veto loop reviewer",
    ),
    AgentSpec(
        "approval_manager",
        "Approval Manager Agent",
        "Decision owner",
        "Synthesize all artifacts into a clear approve, conditional approve, reject, or escalate recommendation.",
        "primary",
        "Executive decision agent",
        "decision synthesis",
    ),
]


SPECIALIST_AGENT_IDS = ["vendor_research", "finance_roi", "security_compliance", "legal_policy"]


def agent_by_id(agent_id: str) -> AgentSpec:
    for agent in AGENTS:
        if agent.agent_id == agent_id:
            return agent
    raise KeyError(agent_id)


class AgentRunner:
    def __init__(self, llm: AIMLAPIClient):
        self.llm = llm

    async def run_specialist(self, case: VendorCase, agent: AgentSpec) -> AgentArtifact:
        system = (
            f"You are {agent.name}, a {agent.title}. {agent.mission} "
            "Return only compact JSON. Be enterprise-realistic, specific, and audit-friendly."
        )
        user = json.dumps(
            {
                "task": "Review this procurement case and produce your handoff artifact.",
                "required_schema": {
                    "summary": "one sentence",
                    "findings": ["3-5 concrete findings"],
                    "risk_score": "integer 0-100",
                    "confidence": "number 0-1",
                    "blockers": ["missing evidence or approvals"],
                    "recommended_next": "next handoff or condition",
                    "structured_context": "role-specific key value object",
                },
                "case": case.model_dump(),
            },
            indent=2,
        )
        model = self.llm.settings.aimlapi_model_fast if agent.model_tier == "fast" else self.llm.settings.aimlapi_model_primary
        try:
            raw = await self.llm.complete_json(system=system, user=user, model=model, max_tokens=850)
            return AgentArtifact(
                agent_id=agent.agent_id,
                agent_name=agent.name,
                summary=str(raw.get("summary", ""))[:600],
                findings=_string_list(raw.get("findings")),
                risk_score=_score(raw.get("risk_score"), default=55),
                confidence=_confidence(raw.get("confidence"), default=0.72),
                blockers=_string_list(raw.get("blockers")),
                recommended_next=str(raw.get("recommended_next", "Send to Approval Manager Agent for synthesis."))[:500],
                structured_context=dict(raw.get("structured_context") or {}),
            )
        except Exception:
            return heuristic_specialist(case, agent)

    async def run_context_packet(self, case: VendorCase, artifacts: list[AgentArtifact]) -> ContextPacket:
        system = (
            "You are Evidence Clerk Agent. Create a shared context packet from multiple specialist handoffs. "
            "Return only JSON. Do not make the final approval decision."
        )
        user = json.dumps(
            {
                "task": "Create the shared state packet that the Approval Manager will use.",
                "required_schema": {
                    "summary": "2 sentence packet summary",
                    "consensus_points": ["what agents agree on"],
                    "unresolved_questions": ["open evidence gaps"],
                    "readiness_score": "integer 0-100",
                    "shared_state": {
                        "business_value": "summary",
                        "data_risk": "summary",
                        "commercial_risk": "summary",
                        "legal_risk": "summary",
                        "recommended_gate": "human gate or auto approval gate",
                    },
                },
                "case": case.model_dump(),
                "artifacts": [artifact.model_dump() for artifact in artifacts],
            },
            indent=2,
        )
        try:
            raw = await self.llm.complete_json(
                system=system,
                user=user,
                model=self.llm.settings.aimlapi_model_fast,
                max_tokens=900,
            )
            return context_from_raw(artifacts, raw)
        except Exception:
            return heuristic_context_packet(case, artifacts)

    async def run_challenge_review(
        self,
        case: VendorCase,
        artifacts: list[AgentArtifact],
        context_packet: ContextPacket,
    ) -> ChallengeReview:
        system = (
            "You are Red Team Auditor Agent. Your job is to challenge the shared context before approval. "
            "Return only JSON. Use veto only for truly unsafe or under-evidenced decisions."
        )
        user = json.dumps(
            {
                "task": "Adversarially review the procurement packet before the Approval Manager decides.",
                "required_schema": {
                    "veto_level": "none | warning | veto",
                    "summary": "short review summary",
                    "objections": ["risks, contradictions, unsafe assumptions"],
                    "required_revisions": ["conditions or changes required before approval"],
                    "cleared_to_decide": "boolean",
                    "confidence": "number 0-1",
                },
                "case": case.model_dump(),
                "artifacts": [artifact.model_dump() for artifact in artifacts],
                "shared_context_packet": context_packet.model_dump(),
            },
            indent=2,
        )
        try:
            raw = await self.llm.complete_json(system=system, user=user, max_tokens=850)
            return challenge_from_raw(raw)
        except Exception:
            return heuristic_challenge_review(case, artifacts, context_packet)

    async def run_approval(
        self,
        case: VendorCase,
        artifacts: list[AgentArtifact],
        context_packet: ContextPacket | None = None,
        challenge_review: ChallengeReview | None = None,
    ) -> ApprovalDecision:
        system = (
            "You are Approval Manager Agent. Make a decision using the full multi-agent audit record. "
            "Return only JSON. Prefer conditional approval when the business case is strong but controls are missing."
        )
        user = json.dumps(
            {
                "task": "Synthesize artifacts into an enterprise approval decision.",
                "allowed_decisions": ["approve", "conditional_approve", "reject", "escalate"],
                "required_schema": {
                    "decision": "approve | conditional_approve | reject | escalate",
                    "executive_summary": "2-3 sentences",
                    "score": "integer 0-100",
                    "conditions": ["approval conditions"],
                    "risk_register": [
                        {
                            "area": "risk area",
                            "severity": "low | medium | high | critical",
                            "owner": "owner role",
                            "mitigation": "mitigation",
                        }
                    ],
                    "next_actions": ["sequenced actions"],
                    "approval_memo": "polished memo for leadership",
                },
                "case": case.model_dump(),
                "artifacts": [artifact.model_dump() for artifact in artifacts],
                "shared_context_packet": context_packet.model_dump() if context_packet else None,
                "red_team_challenge": challenge_review.model_dump() if challenge_review else None,
            },
            indent=2,
        )
        try:
            raw = await self.llm.complete_json(system=system, user=user, max_tokens=1200)
            decision = approval_from_raw(case, artifacts, raw)
            return enforce_challenge_guardrails(decision, challenge_review)
        except Exception:
            return heuristic_approval(case, artifacts, context_packet, challenge_review)

    def build_human_gate(
        self,
        case: VendorCase,
        decision: ApprovalDecision,
        context_packet: ContextPacket | None = None,
        challenge_review: ChallengeReview | None = None,
    ) -> HumanApprovalGate:
        required = []
        sensitive = any(
            word in " ".join(case.data_access).lower()
            for word in ["customer", "medical", "bank", "email", "regulated"]
        )
        if decision.conditions:
            required.append("Procurement")
        if sensitive:
            required.extend(["Security", "Legal"])
        if case.requested_amount_usd >= 75000:
            required.append("Finance leadership")
        if challenge_review and challenge_review.veto_level == "veto":
            required.append("Executive sponsor")
        if decision.decision in {"reject", "escalate"}:
            status = "blocked"
        elif decision.decision == "approve" and not decision.conditions:
            status = "not_required"
        else:
            status = "ready_for_human"
        packet = [
            f"Decision: {decision.decision.replace('_', ' ')}",
            f"Decision score: {decision.score}/100",
        ]
        if context_packet:
            packet.append(f"Context packet: {context_packet.packet_id}, readiness {context_packet.readiness_score}/100")
        if challenge_review:
            packet.append(f"Red-team review: {challenge_review.veto_level}")
        packet.extend(decision.conditions[:4])
        return HumanApprovalGate(
            gate_status=status,
            approver="Human Procurement Lead",
            rationale=(
                "Human signoff is required when approval carries unresolved controls, sensitive data access, "
                "large spend, or an escalation recommendation."
            ),
            required_signoffs=sorted(set(required)) or ["Procurement"],
            approval_packet=packet,
        )


def approval_from_raw(case: VendorCase, artifacts: list[AgentArtifact], raw: dict[str, Any]) -> ApprovalDecision:
    decision = raw.get("decision", "conditional_approve")
    if decision not in {"approve", "conditional_approve", "reject", "escalate"}:
        decision = "conditional_approve"
    risk_items = []
    for item in raw.get("risk_register") or []:
        if not isinstance(item, dict):
            continue
        severity = item.get("severity", "medium")
        if severity not in {"low", "medium", "high", "critical"}:
            severity = "medium"
        risk_items.append(
            RiskRegisterItem(
                area=str(item.get("area", "Vendor governance")),
                severity=severity,
                owner=str(item.get("owner", "Procurement")),
                mitigation=str(item.get("mitigation", "Track mitigation before launch.")),
            )
        )
    if not risk_items:
        risk_items = heuristic_risk_register(case, artifacts)
    return ApprovalDecision(
        decision=decision,
        executive_summary=str(raw.get("executive_summary", ""))[:1200],
        score=_score(raw.get("score"), default=72),
        conditions=_string_list(raw.get("conditions")),
        risk_register=risk_items,
        next_actions=_string_list(raw.get("next_actions")),
        approval_memo=str(raw.get("approval_memo", ""))[:2500],
    )


def enforce_challenge_guardrails(
    decision: ApprovalDecision,
    challenge_review: ChallengeReview | None,
) -> ApprovalDecision:
    if not challenge_review:
        return decision
    requires_escalation = challenge_review.veto_level == "veto" or not challenge_review.cleared_to_decide
    if not requires_escalation:
        return decision
    if decision.decision in {"reject", "escalate"}:
        return decision
    existing = _dedupe_strings([*decision.conditions, *challenge_review.required_revisions])
    decision.decision = "escalate"
    decision.score = min(decision.score, 55)
    decision.conditions = existing
    reason = (
        "the Red Team Auditor issued a veto"
        if challenge_review.veto_level == "veto"
        else "the Red Team Auditor did not clear the packet for decision"
    )
    decision.executive_summary = (
        f"Escalation required because {reason}. "
        "The business case may be credible, but procurement cannot proceed until required revisions are cleared."
    )[:1200]
    decision.approval_memo = (
        "Red-team escalation guardrail: this packet must be escalated to the executive sponsor, procurement, legal, "
        "and security before any approval. Required revisions: "
        f"{'; '.join(existing) or challenge_review.summary}"
    )[:2500]
    return decision


def context_from_raw(artifacts: list[AgentArtifact], raw: dict[str, Any]) -> ContextPacket:
    shared_state = raw.get("shared_state")
    if not isinstance(shared_state, dict):
        shared_state = {}
    return ContextPacket(
        summary=str(raw.get("summary", "Shared context packet prepared from specialist handoffs."))[:1000],
        consensus_points=_string_list(raw.get("consensus_points"))[:6],
        unresolved_questions=_string_list(raw.get("unresolved_questions"))[:6],
        shared_state=shared_state,
        readiness_score=_score(raw.get("readiness_score"), default=68),
        source_artifact_ids=[artifact.agent_id for artifact in artifacts],
    )


def challenge_from_raw(raw: dict[str, Any]) -> ChallengeReview:
    veto_level = str(raw.get("veto_level", "warning")).lower()
    if veto_level not in {"none", "warning", "veto"}:
        veto_level = "warning"
    return ChallengeReview(
        veto_level=veto_level,  # type: ignore[arg-type]
        summary=str(raw.get("summary", "Red-team challenge review completed."))[:900],
        objections=_string_list(raw.get("objections"))[:6],
        required_revisions=_string_list(raw.get("required_revisions"))[:6],
        cleared_to_decide=_bool(raw.get("cleared_to_decide"), default=veto_level != "veto"),
        confidence=_confidence(raw.get("confidence"), default=0.74),
    )


def heuristic_specialist(case: VendorCase, agent: AgentSpec) -> AgentArtifact:
    amount = case.requested_amount_usd
    sensitive = any("medical" in item.lower() or "bank" in item.lower() or "customer" in item.lower() for item in case.data_access)
    urgent = "urgent" in case.timeline.lower() or "30-day" in case.timeline.lower()

    if agent.agent_id == "vendor_research":
        risk = 48 + (10 if "not yet" in case.notes.lower() else 0)
        findings = [
            f"{case.vendor_name} maps to the stated need for {case.department}, but diligence evidence must be centralized.",
            f"Requested timeline is {case.timeline}, so procurement should run diligence and pilot scoping in parallel.",
            "Vendor claims should be converted into evidence requests: SOC report, support SLA, roadmap, and references.",
        ]
        blockers = ["SOC 2 report and customer references are not attached."] if "soc" in case.notes.lower() else []
    elif agent.agent_id == "finance_roi":
        risk = 35 + (18 if amount > 75000 else 5)
        findings = [
            f"Request is ${amount:,.0f}; finance should tie approval to measurable cycle-time or productivity gains.",
            "A time-boxed pilot reduces spend exposure while preserving speed.",
            "Renewal terms should include usage caps, opt-out rights, and success metrics before expansion.",
        ]
        blockers = ["No quantified savings target is documented."] if amount > 50000 else []
    elif agent.agent_id == "security_compliance":
        risk = 70 if sensitive else 50
        findings = [
            f"Data access includes {', '.join(case.data_access) or 'limited operational data'}, which defines the control baseline.",
            f"Integrations with {', '.join(case.integrations) or 'no named systems'} require scoped credentials and logging.",
            "Security approval should require SSO, least-privilege roles, incident notice, and data deletion terms.",
        ]
        blockers = ["Privacy/security review required before production data access."] if sensitive else []
    else:
        risk = 68 if sensitive else 52
        findings = [
            "Contract review should cover DPA, audit rights, subprocessors, retention, and termination assistance.",
            "Approval authority should match spend level and data classification.",
            "Human review and exception logging are required for regulated or high-impact decisions.",
        ]
        blockers = ["DPA or regulated-data terms are missing."] if sensitive or "dpa" in case.notes.lower() else []

    if urgent:
        risk += 7
    risk = min(95, risk)
    return AgentArtifact(
        agent_id=agent.agent_id,
        agent_name=agent.name,
        summary=f"{agent.name} recommends controlled progression with risk score {risk}/100.",
        findings=findings,
        risk_score=risk,
        confidence=0.76,
        blockers=blockers,
        recommended_next="Send this artifact to @Approval Manager Agent with conditions and open evidence requests.",
        structured_context={
            "spend": amount,
            "sensitive_data": sensitive,
            "urgency": case.timeline,
            "owner": agent.title,
        },
    )


def heuristic_context_packet(case: VendorCase, artifacts: list[AgentArtifact]) -> ContextPacket:
    avg_risk = sum(artifact.risk_score for artifact in artifacts) / max(len(artifacts), 1)
    blockers = [blocker for artifact in artifacts for blocker in artifact.blockers]
    consensus = [
        f"{case.vendor_name} has a credible business case for {case.department}.",
        "A controlled pilot is preferable to unconditional production approval.",
        "Security, legal, and procurement evidence should be attached before spend is finalized.",
    ]
    unresolved = blockers or [
        "Confirm final commercial terms and renewal cap.",
        "Attach vendor security evidence and DPA review notes.",
    ]
    return ContextPacket(
        summary=(
            f"Evidence Clerk Agent consolidated {len(artifacts)} specialist handoffs. "
            f"Average risk is {avg_risk:.0f}/100 with {len(unresolved)} unresolved item(s)."
        ),
        consensus_points=consensus,
        unresolved_questions=unresolved[:6],
        shared_state={
            "business_value": case.business_need,
            "data_risk": ", ".join(case.data_access) or "No sensitive data listed",
            "commercial_risk": f"Requested spend is ${case.requested_amount_usd:,.0f}",
            "legal_risk": case.notes or "No legal notes attached",
            "recommended_gate": "Human Procurement Lead review before purchase order",
        },
        readiness_score=max(10, min(95, int(100 - avg_risk + (5 if not blockers else -5)))),
        source_artifact_ids=[artifact.agent_id for artifact in artifacts],
    )


def heuristic_challenge_review(
    case: VendorCase,
    artifacts: list[AgentArtifact],
    context_packet: ContextPacket,
) -> ChallengeReview:
    max_risk = max((artifact.risk_score for artifact in artifacts), default=50)
    blockers = [blocker for artifact in artifacts for blocker in artifact.blockers]
    sensitive = any(
        word in " ".join(case.data_access).lower()
        for word in ["customer", "medical", "bank", "regulated", "email"]
    )
    veto_level = "warning"
    if max_risk >= 85 or (sensitive and context_packet.readiness_score < 45):
        veto_level = "veto"
    elif max_risk < 45 and not blockers:
        veto_level = "none"
    objections = blockers[:4] or [
        "DPA and security evidence are not yet fully attached to the approval record.",
        "Pilot controls need explicit data minimization and role-based access boundaries.",
    ]
    return ChallengeReview(
        veto_level=veto_level,  # type: ignore[arg-type]
        summary=(
            f"Red-team review found {veto_level} level concerns. "
            "The case can proceed only if unresolved evidence and control gaps are visible to the human approver."
        ),
        objections=objections,
        required_revisions=[
            "Attach final DPA review result to the approval packet.",
            "Confirm SOC 2 evidence and incident notification terms.",
            "Limit pilot data access until Security signs off.",
        ],
        cleared_to_decide=veto_level != "veto",
        confidence=0.78,
    )


def heuristic_approval(
    case: VendorCase,
    artifacts: list[AgentArtifact],
    context_packet: ContextPacket | None = None,
    challenge_review: ChallengeReview | None = None,
) -> ApprovalDecision:
    max_risk = max((artifact.risk_score for artifact in artifacts), default=50)
    avg_risk = sum(artifact.risk_score for artifact in artifacts) / max(len(artifacts), 1)
    blockers = [blocker for artifact in artifacts for blocker in artifact.blockers]
    readiness = context_packet.readiness_score if context_packet else 65
    veto_level = challenge_review.veto_level if challenge_review else "none"
    if veto_level == "veto" or max_risk >= 82 or len(blockers) >= 4 or readiness < 35:
        decision = "escalate"
    elif veto_level == "warning" or avg_risk >= 55 or blockers:
        decision = "conditional_approve"
    else:
        decision = "approve"
    score = max(10, min(95, int(100 - avg_risk + (8 if case.business_need else 0))))
    conditions = [
        "Complete security and privacy review before production data access.",
        "Attach SOC 2 or equivalent control evidence to the procurement record.",
        "Run a 30-60 day pilot with documented success metrics and exit criteria.",
    ]
    if case.requested_amount_usd > 75000:
        conditions.append("Obtain finance leadership approval for spend level and renewal cap.")
    if any("medical" in item.lower() or "bank" in item.lower() for item in case.data_access):
        conditions.append("Require legal sign-off on regulated-data terms, retention, and subprocessors.")
    if challenge_review and challenge_review.required_revisions:
        conditions.extend(challenge_review.required_revisions[:2])
    memo = (
        f"ProcureGuard recommends {decision.replace('_', ' ')} for {case.vendor_name}. "
        f"The business need is credible for {case.department}, but the approval should be gated by evidence, "
        "security controls, and measurable pilot outcomes. The Band room audit shows specialist review across "
        "vendor diligence, finance, security/compliance, and legal policy before this decision."
    )
    return ApprovalDecision(
        decision=decision,
        executive_summary=(
            f"{case.vendor_name} can move forward only if the team closes the documented diligence gaps. "
            f"Average specialist risk is {avg_risk:.0f}/100 with {len(blockers)} blocker(s)."
        ),
        score=score,
        conditions=conditions,
        risk_register=heuristic_risk_register(case, artifacts),
        next_actions=[
            "Evidence Clerk attaches the shared context packet to the procurement record.",
            "Procurement gathers missing vendor evidence.",
            "Security validates controls and integration scope.",
            "Legal reviews DPA, retention, audit rights, and subprocessors.",
            "Approval Manager records final pilot decision after conditions are met.",
        ],
        approval_memo=memo,
    )


def heuristic_risk_register(case: VendorCase, artifacts: list[AgentArtifact]) -> list[RiskRegisterItem]:
    sensitive = any("medical" in item.lower() or "bank" in item.lower() or "customer" in item.lower() for item in case.data_access)
    return [
        RiskRegisterItem(
            area="Data protection",
            severity="high" if sensitive else "medium",
            owner="Security Compliance Agent",
            mitigation="Limit pilot data, require SSO, document retention, and verify deletion terms.",
        ),
        RiskRegisterItem(
            area="Commercial exposure",
            severity="medium",
            owner="Finance ROI Agent",
            mitigation="Use pilot caps, success metrics, and renewal guardrails before expansion.",
        ),
        RiskRegisterItem(
            area="Contract and policy",
            severity="high" if sensitive else "medium",
            owner="Legal Policy Agent",
            mitigation="Complete DPA, subprocessors, audit rights, and human-review clauses.",
        ),
    ]


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item)[:500] for item in value if str(item).strip()]
    return [str(value)[:500]]


def _score(value: Any, *, default: int) -> int:
    try:
        return max(0, min(100, int(float(value))))
    except (TypeError, ValueError):
        return default


def _confidence(value: Any, *, default: float) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


def _bool(value: Any, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False
    return bool(value)


def _dedupe_strings(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        cleaned = " ".join(str(item).split())[:500]
        normalized = cleaned.lower()
        normalized = normalized.replace("data processing agreement (dpa)", "dpa")
        normalized = normalized.replace("data processing agreement", "dpa")
        normalized = normalized.replace("(dpa)", "")
        key = "".join(character for character in normalized if character.isalnum())
        if cleaned and key not in seen:
            seen.add(key)
            output.append(cleaned)
    return output
