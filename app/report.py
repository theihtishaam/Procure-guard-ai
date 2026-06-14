from __future__ import annotations

from app.models import WorkflowRun


def workflow_markdown_report(run: WorkflowRun) -> str:
    decision = run.decision
    packet = run.context_packet
    gate = run.human_gate
    lines = [
        f"# ProcureGuard Run Report: {run.case.vendor_name}",
        "",
        f"- Run ID: `{run.run_id}`",
        f"- Provider: `{run.provider}`",
        f"- Mode: `{run.mode}`",
        f"- Collaboration score: `{run.collaboration_score}/100`",
        f"- Room: `{run.room_name}`",
        "",
        "## Band Platform Proof",
        "",
    ]
    if run.mode == "band-live":
        real_messages = [m for m in run.messages if m.band_delivery == "message" and m.band_message_id]
        lines.extend(
            [
                f"- Mode: `band-live` (ran on the real Band platform at app.band.ai)",
                f"- Band room ID: `{run.band_room_id}`",
                f"- Band room URL: {run.band_room_url}",
                f"- Real Band messages delivered: `{len(real_messages)}`",
                f"- Real Band task events: `{len(run.band_events)}`",
            ]
        )
        if real_messages:
            lines.append(f"- Example Band message ID: `{real_messages[0].band_message_id}`")
    else:
        lines.append(
            "- Mode: `local-band-sim` (local Band simulator; set BAND_ENABLED=1 with registered "
            "agents in agent_config.yaml to run on the real platform)."
        )
    lines.extend(
        [
            "",
            "## Case",
            "",
            f"- Requester: {run.case.requester}",
            f"- Department: {run.case.department}",
            f"- Product: {run.case.product}",
            f"- Spend: ${run.case.requested_amount_usd:,.0f}",
            f"- Data access: {', '.join(run.case.data_access) or 'None listed'}",
            f"- Integrations: {', '.join(run.case.integrations) or 'None listed'}",
            "",
            "## Collaboration Evidence",
            "",
        ]
    )
    for item in run.collaboration_evidence:
        lines.append(f"- **{item.label}**: {item.status} - {item.detail}")
    lines.extend(["", "## Specialist Artifacts And Cited Evidence", ""])
    for artifact in run.artifacts:
        lines.append(
            f"### {artifact.agent_name} (risk {artifact.risk_score}/100, "
            f"confidence {round(artifact.confidence * 100)}%)"
        )
        lines.append("")
        lines.append(f"{artifact.summary}")
        lines.append("")
        for finding in artifact.findings:
            lines.append(f"- {finding}")
        if artifact.citations:
            lines.extend(["", "**Cited evidence (grounded in case fields):**", ""])
            for citation in artifact.citations:
                lines.append(f"- _{citation.claim}_ -> `{citation.source}`: {citation.evidence}")
        lines.append("")
    lines.extend(["## Task State Board", ""])
    for task in run.task_state:
        refs = ", ".join(task.evidence_refs) if task.evidence_refs else "No refs"
        lines.append(f"- **{task.label}** ({task.status}) - Owner: {task.owner}. {task.summary} Evidence: {refs}.")
    lines.extend(["", "## Peer Recruitment Ledger", ""])
    for record in run.peer_recruitment:
        lines.append(
            f"- **{record.recruiter} -> {record.peer}** ({record.status}) - "
            f"{record.reason} Action: {record.band_action}."
        )
    lines.extend(["", "## Business Impact", ""])
    for metric in run.business_impact:
        lines.append(
            f"- **{metric.label}**: {metric.value}. Baseline: {metric.baseline}. "
            f"Impact: {metric.impact} Owner: {metric.owner}."
        )
    lines.extend(["", "## Governance Control Matrix", ""])
    for control in run.governance_controls:
        lines.append(
            f"- **{control.control_id} {control.area}** ({control.status}) - Owner: {control.owner}. "
            f"Evidence: {control.evidence} Next action: {control.next_action}"
        )
    lines.extend(["", "## Agent And Framework Profile", ""])
    for profile in run.agent_profiles:
        lines.append(
            f"- **{profile.name}** ({profile.role}) - {profile.framework_profile}; "
            f"{profile.coordination_style}; provider: {profile.model_provider}"
        )
    lines.extend(["", "## Shared Context Packet", ""])
    if packet:
        lines.extend(
            [
                f"- Packet ID: `{packet.packet_id}`",
                f"- Readiness: `{packet.readiness_score}/100`",
                f"- Summary: {packet.summary}",
                "",
                "### Consensus",
                "",
            ]
        )
        lines.extend([f"- {item}" for item in packet.consensus_points])
        lines.extend(["", "### Unresolved Questions", ""])
        lines.extend([f"- {item}" for item in packet.unresolved_questions])
    else:
        lines.append("No context packet recorded.")
    lines.extend(["", "## Red Team Challenge", ""])
    if run.challenge_review:
        lines.extend(
            [
                f"- Reviewer: {run.challenge_review.reviewer}",
                f"- Veto level: `{run.challenge_review.veto_level}`",
                f"- Cleared to decide: `{run.challenge_review.cleared_to_decide}`",
                f"- Confidence: `{round(run.challenge_review.confidence * 100)}%`",
                f"- Summary: {run.challenge_review.summary}",
                "",
                "### Objections",
                "",
            ]
        )
        lines.extend([f"- {item}" for item in run.challenge_review.objections])
        lines.extend(["", "### Required Revisions", ""])
        lines.extend([f"- {item}" for item in run.challenge_review.required_revisions])
    else:
        lines.append("No red-team challenge recorded.")
    lines.extend(["", "## Decision", ""])
    if decision:
        lines.extend(
            [
                f"- Decision: `{decision.decision}`",
                f"- Score: `{decision.score}/100`",
                f"- Summary: {decision.executive_summary}",
                "",
                "### Conditions",
                "",
            ]
        )
        lines.extend([f"- {item}" for item in decision.conditions])
        lines.extend(["", "### Risk Register", ""])
        for risk in decision.risk_register:
            lines.append(f"- **{risk.area} ({risk.severity})** - {risk.mitigation} Owner: {risk.owner}")
        lines.extend(["", "### Approval Memo", "", decision.approval_memo])
    else:
        lines.append("No decision recorded.")
    lines.extend(["", "## Human Approval Gate", ""])
    if gate:
        lines.extend(
            [
                f"- Status: `{gate.gate_status}`",
                f"- Approver: {gate.approver}",
                f"- Required signoffs: {', '.join(gate.required_signoffs)}",
                f"- Rationale: {gate.rationale}",
                "",
                "### Approval Packet",
                "",
            ]
        )
        lines.extend([f"- {item}" for item in gate.approval_packet])
    else:
        lines.append("No human approval gate recorded.")
    lines.extend(["", "## Audit Seal", ""])
    if run.audit_seal:
        lines.extend(
            [
                f"- Algorithm: `{run.audit_seal.algorithm}`",
                f"- Digest: `{run.audit_seal.digest}`",
                f"- Scope: {run.audit_seal.sealed_scope}",
                f"- Records sealed: `{run.audit_seal.record_count}`",
                f"- Generated: `{run.audit_seal.generated_at.isoformat()}`",
            ]
        )
    else:
        lines.append("No audit seal recorded.")
    lines.extend(["", "## Room Timeline", ""])
    for message in run.messages:
        routed = f" Routed to: {', '.join(message.mentions)}." if message.mentions else ""
        lines.append(f"- **{message.sender}** [{message.message_type}]: {message.content}{routed}")
    lines.append("")
    return "\n".join(lines)
