from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


Decision = Literal["approve", "conditional_approve", "reject", "escalate"]


class VendorCase(BaseModel):
    case_id: str = Field(default_factory=lambda: f"case-{uuid4().hex[:8]}")
    requester: str
    department: str
    vendor_name: str
    product: str
    requested_amount_usd: float
    renewal_or_new: Literal["new", "renewal", "expansion"] = "new"
    business_need: str
    data_access: list[str] = Field(default_factory=list)
    integrations: list[str] = Field(default_factory=list)
    timeline: str = "standard"
    notes: str = ""


class FindingCitation(BaseModel):
    claim: str
    source: str
    evidence: str


class AgentArtifact(BaseModel):
    agent_id: str
    agent_name: str
    summary: str
    findings: list[str] = Field(default_factory=list)
    risk_score: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    blockers: list[str] = Field(default_factory=list)
    recommended_next: str
    structured_context: dict[str, Any] = Field(default_factory=dict)
    citations: list[FindingCitation] = Field(default_factory=list)


class AgentProfile(BaseModel):
    agent_id: str
    name: str
    role: str
    framework_profile: str
    model_provider: str
    coordination_style: str


class RiskRegisterItem(BaseModel):
    area: str
    severity: Literal["low", "medium", "high", "critical"]
    owner: str
    mitigation: str


class ContextPacket(BaseModel):
    packet_id: str = Field(default_factory=lambda: f"packet-{uuid4().hex[:8]}")
    summary: str
    consensus_points: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    shared_state: dict[str, Any] = Field(default_factory=dict)
    readiness_score: int = Field(ge=0, le=100)
    source_artifact_ids: list[str] = Field(default_factory=list)


class ChallengeReview(BaseModel):
    reviewer: str = "Red Team Auditor Agent"
    veto_level: Literal["none", "warning", "veto"]
    summary: str
    objections: list[str] = Field(default_factory=list)
    required_revisions: list[str] = Field(default_factory=list)
    cleared_to_decide: bool
    confidence: float = Field(ge=0, le=1)


class ApprovalDecision(BaseModel):
    decision: Decision
    executive_summary: str
    score: int = Field(ge=0, le=100)
    conditions: list[str] = Field(default_factory=list)
    risk_register: list[RiskRegisterItem] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    approval_memo: str


class HumanApprovalGate(BaseModel):
    gate_status: Literal["ready_for_human", "blocked", "not_required"]
    approver: str
    rationale: str
    required_signoffs: list[str] = Field(default_factory=list)
    approval_packet: list[str] = Field(default_factory=list)


class CollaborationEvidence(BaseModel):
    label: str
    status: Literal["met", "partial", "missing"]
    detail: str


class TaskStateItem(BaseModel):
    task_id: str
    label: str
    owner: str
    status: Literal["queued", "active", "complete", "blocked", "human_review"]
    summary: str
    evidence_refs: list[str] = Field(default_factory=list)


class PeerRecruitmentRecord(BaseModel):
    recruiter: str
    peer: str
    reason: str
    band_action: str
    status: Literal["recruited", "routed", "joined"]


class BusinessImpactMetric(BaseModel):
    label: str
    value: str
    baseline: str
    impact: str
    owner: str


class GovernanceControl(BaseModel):
    control_id: str
    area: str
    owner: str
    status: Literal["satisfied", "conditional", "blocked", "human_review"]
    evidence: str
    next_action: str


class AuditSeal(BaseModel):
    algorithm: str = "sha256"
    digest: str
    sealed_scope: str
    record_count: int
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RoomMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: f"msg-{uuid4().hex[:10]}")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sender: str
    content: str
    mentions: list[str] = Field(default_factory=list)
    visible_to: list[str] = Field(default_factory=list)
    message_type: Literal[
        "chat",
        "event",
        "recruitment",
        "handoff",
        "context",
        "challenge",
        "decision",
        "approval_gate",
        "audit",
    ] = "chat"
    payload: dict[str, Any] = Field(default_factory=dict)
    band_message_id: str | None = None
    band_recipients: list[dict[str, Any]] = Field(default_factory=list)
    band_delivery: Literal["message", "event", "sim"] = "sim"


class BandEventRecord(BaseModel):
    event_id: str | None = None
    sender: str
    event_type: Literal["tool_call", "tool_result", "thought", "error", "task"]
    content: str


class BandMemoryRecord(BaseModel):
    memory_id: str | None = None
    author: str
    subject_id: str
    summary: str
    tags: list[str] = Field(default_factory=list)


class WorkflowRun(BaseModel):
    run_id: str = Field(default_factory=lambda: f"run-{uuid4().hex[:8]}")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    mode: Literal["band-live", "local-band-sim", "band-live-ready"] = "local-band-sim"
    case: VendorCase
    room_name: str
    band_room_id: str | None = None
    band_room_url: str | None = None
    band_events: list[BandEventRecord] = Field(default_factory=list)
    band_memories: list[BandMemoryRecord] = Field(default_factory=list)
    prior_reviews_recalled: int = 0
    participants: list[str]
    agent_profiles: list[AgentProfile] = Field(default_factory=list)
    human_participants: list[str] = Field(default_factory=list)
    messages: list[RoomMessage] = Field(default_factory=list)
    artifacts: list[AgentArtifact] = Field(default_factory=list)
    context_packet: ContextPacket | None = None
    challenge_review: ChallengeReview | None = None
    decision: ApprovalDecision | None = None
    human_gate: HumanApprovalGate | None = None
    audit_seal: AuditSeal | None = None
    collaboration_score: int = Field(default=0, ge=0, le=100)
    collaboration_evidence: list[CollaborationEvidence] = Field(default_factory=list)
    task_state: list[TaskStateItem] = Field(default_factory=list)
    peer_recruitment: list[PeerRecruitmentRecord] = Field(default_factory=list)
    business_impact: list[BusinessImpactMetric] = Field(default_factory=list)
    governance_controls: list[GovernanceControl] = Field(default_factory=list)
    provider: str = "heuristic"
    cost_note: str = "Live token cost is provider-side; this app keeps prompts compact."
