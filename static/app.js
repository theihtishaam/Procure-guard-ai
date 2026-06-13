const state = {
  cases: [],
  activeCase: null,
  lastRun: null,
};

const $ = (id) => document.getElementById(id);

async function api(path, options) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json();
}

function money(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value || 0);
}

function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function init() {
  const [health, cases] = await Promise.all([api("/api/health"), api("/api/sample-cases")]);
  state.cases = cases;
  state.activeCase = cases[0];
  $("health").textContent = health.live_llm_configured
    ? "AI/ML API connected. Band live mode is " + (health.band_enabled ? "enabled." : "ready for credentials.")
    : "Local deterministic mode. Add AIMLAPI_API_KEY for live model calls.";
  renderCasePicker();
  renderCase(state.activeCase);
  renderParticipants([
    "Intake Coordinator",
    "Vendor Research Agent",
    "Finance ROI Agent",
    "Security Compliance Agent",
    "Legal Policy Agent",
    "Evidence Clerk Agent",
    "Red Team Auditor Agent",
    "Approval Manager Agent",
    "Human Procurement Lead",
  ]);
}

function renderCasePicker() {
  $("caseSelect").innerHTML = state.cases
    .map((item) => `<option value="${esc(item.case_id)}">${esc(item.vendor_name)} - ${esc(item.department)}</option>`)
    .join("");
  $("caseSelect").addEventListener("change", (event) => {
    state.activeCase = state.cases.find((item) => item.case_id === event.target.value);
    renderCase(state.activeCase);
  });
  $("runButton").addEventListener("click", runSelectedCase);
  $("customRunButton").addEventListener("click", runCustomCase);
  $("reportButton").addEventListener("click", downloadReport);
  $("bundleButton").addEventListener("click", downloadBundle);
}

function renderCase(item) {
  $("caseTitle").textContent = `${item.vendor_name}: ${item.product}`;
  $("caseStrip").innerHTML = `
    <div class="case-metric"><span>Requester</span><strong>${esc(item.requester)}</strong></div>
    <div class="case-metric"><span>Department</span><strong>${esc(item.department)}</strong></div>
    <div class="case-metric"><span>Spend</span><strong>${money(item.requested_amount_usd)}</strong></div>
    <div class="case-metric"><span>Timeline</span><strong>${esc(item.timeline)}</strong></div>
  `;
  $("evidenceStrip").innerHTML = `
    <div class="case-metric"><span>Collaboration Score</span><strong>Pending</strong></div>
    <div class="case-metric"><span>Shared Context</span><strong>Pending</strong></div>
    <div class="case-metric"><span>Human Gate</span><strong>Pending</strong></div>
    <div class="case-metric"><span>Audit Seal</span><strong>Pending</strong></div>
  `;
}

async function runSelectedCase() {
  await runCase({
    case_id: state.activeCase.case_id,
    force_heuristic: $("fastDemoMode").checked,
  });
}

async function runCustomCase() {
  const customCase = buildCustomCase();
  state.activeCase = customCase;
  renderCase(customCase);
  await runCase({
    case: customCase,
    force_heuristic: $("fastDemoMode").checked,
  });
}

function buildCustomCase() {
  const vendor = $("customVendor").value.trim() || "Custom Vendor";
  const product = $("customProduct").value.trim() || "Enterprise AI tool";
  return {
    case_id: `case-custom-${Date.now()}`,
    requester: $("customRequester").value.trim() || "Procurement requester",
    department: $("customDepartment").value.trim() || "Operations",
    vendor_name: vendor,
    product,
    requested_amount_usd: Number($("customSpend").value || 0),
    renewal_or_new: "new",
    business_need: $("customNeed").value.trim() || `${vendor} is being evaluated for ${product}.`,
    data_access: splitCsv($("customData").value),
    integrations: splitCsv($("customIntegrations").value),
    timeline: $("customTimeline").value.trim() || "standard",
    notes: $("customNotes").value.trim(),
  };
}

function splitCsv(value) {
  return String(value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

async function runCase(payload) {
  const button = $("runButton");
  const customButton = $("customRunButton");
  button.disabled = true;
  customButton.disabled = true;
  $("reportButton").disabled = true;
  $("bundleButton").disabled = true;
  button.textContent = "Agents Reviewing...";
  customButton.textContent = "Agents Reviewing...";
  $("timeline").className = "timeline empty-state";
  $("timeline").textContent = "Review in progress. Specialist agents are preparing handoffs.";
  $("messageCount").textContent = "0 messages";
  $("artifactCount").textContent = "0 artifacts";
  $("contextBadge").textContent = "Pending";
  $("collabBadge").textContent = "0/100";
  $("humanGateBadge").textContent = "Pending";
  $("decisionBadge").textContent = "Pending";
  $("decision").className = "decision empty-state";
  $("decision").textContent = "Approval Manager is waiting for reviewed context.";
  $("artifacts").innerHTML = "";
  $("evidenceStrip").innerHTML = `
    <div class="case-metric"><span>Collaboration Score</span><strong>Pending</strong></div>
    <div class="case-metric"><span>Shared Context</span><strong>Pending</strong></div>
    <div class="case-metric"><span>Human Gate</span><strong>Pending</strong></div>
    <div class="case-metric"><span>Audit Seal</span><strong>Pending</strong></div>
  `;
  $("contextPacket").className = "context-packet empty-state";
  $("contextPacket").textContent = "Evidence Clerk is waiting for specialist handoffs.";
  $("judgingEvidence").className = "judging-list empty-state";
  $("judgingEvidence").textContent = "Collaboration evidence will appear when the room closes.";
  $("humanGate").className = "human-gate empty-state";
  $("humanGate").textContent = "Approval gate pending.";
  $("challengeBadge").textContent = "Pending";
  $("challengeReview").className = "challenge-review empty-state";
  $("challengeReview").textContent = "Red Team Auditor is waiting for the shared context packet.";
  $("auditBadge").textContent = "Pending";
  $("technicalProof").className = "technical-proof empty-state";
  $("technicalProof").textContent = "Framework profiles and audit seal pending.";
  $("handoffBadge").textContent = "Pending";
  $("handoffMap").className = "handoff-map empty-state";
  $("handoffMap").textContent = "Agents are establishing the handoff path.";
  $("taskStateBadge").textContent = "Pending";
  $("taskStateBoard").className = "task-state-board empty-state";
  $("taskStateBoard").textContent = "Task ownership and status will appear after agents coordinate.";
  $("recruitmentLedger").className = "recruitment-ledger empty-state";
  $("recruitmentLedger").textContent = "Peer recruitment records will appear after the room opens.";
  $("controlBadge").textContent = "Pending";
  $("businessImpact").className = "impact-grid empty-state";
  $("businessImpact").textContent = "Business impact metrics will appear after the decision packet is built.";
  $("governanceControls").className = "control-matrix empty-state";
  $("governanceControls").textContent = "Governance controls will appear after the review closes.";
  try {
    const run = await api("/api/workflows/run", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    state.lastRun = run;
    renderRun(run);
    $("reportButton").disabled = false;
    $("bundleButton").disabled = false;
  } catch (error) {
    $("timeline").className = "timeline empty-state";
    $("timeline").textContent = error.message;
  } finally {
    button.disabled = false;
    customButton.disabled = false;
    button.textContent = "Run Agent Review";
    customButton.textContent = "Run Custom Review";
  }
}

function downloadReport() {
  if (!state.lastRun) return;
  window.open(`/api/workflows/${state.lastRun.run_id}/report.md`, "_blank");
}

function downloadBundle() {
  if (!state.lastRun) return;
  window.open(`/api/workflows/${state.lastRun.run_id}/bundle.zip`, "_blank");
}

function renderRun(run) {
  renderParticipants(run.participants);
  $("providerBadge").textContent = `Provider: ${run.provider}`;
  $("modeBadge").textContent = run.mode === "band-live-ready" ? "Band live ready" : "Local Band sim";
  $("messageCount").textContent = `${run.messages.length} messages`;
  $("artifactCount").textContent = `${run.artifacts.length} artifacts`;
  $("contextBadge").textContent = run.context_packet ? `${run.context_packet.readiness_score}/100 readiness` : "Missing";
  $("collabBadge").textContent = `${run.collaboration_score || 0}/100`;
  $("humanGateBadge").textContent = run.human_gate ? run.human_gate.gate_status.replaceAll("_", " ") : "Missing";
  $("challengeBadge").textContent = run.challenge_review ? run.challenge_review.veto_level : "Missing";
  $("auditBadge").textContent = run.audit_seal ? `${run.audit_seal.digest.slice(0, 16)}...` : "Missing";
  renderEvidenceStrip(run);
  renderTimeline(run.messages);
  renderHandoffMap(run.messages);
  renderTaskState(run.task_state || [], run.peer_recruitment || []);
  renderImpactControls(run.business_impact || [], run.governance_controls || []);
  renderArtifacts(run.artifacts);
  renderContextPacket(run.context_packet);
  renderChallengeReview(run.challenge_review);
  renderTechnicalProof(run.agent_profiles || [], run.audit_seal, run.provider);
  renderJudgingEvidence(run.collaboration_evidence || []);
  renderHumanGate(run.human_gate);
  renderDecision(run.decision);
}

function renderImpactControls(metrics, controls) {
  const blocked = controls.filter((item) => item.status === "blocked").length;
  const satisfied = controls.filter((item) => item.status === "satisfied").length;
  $("controlBadge").textContent = `${satisfied}/${controls.length || 0} controls satisfied`;

  if (!metrics.length) {
    $("businessImpact").className = "impact-grid empty-state";
    $("businessImpact").textContent = "No business impact metrics recorded.";
  } else {
    $("businessImpact").className = "impact-grid";
    $("businessImpact").innerHTML = metrics
      .map(
        (metric) => `
        <article class="impact-item">
          <span>${esc(metric.owner)}</span>
          <strong>${esc(metric.value)}</strong>
          <h4>${esc(metric.label)}</h4>
          <p>${esc(metric.impact)}</p>
          <small>${esc(metric.baseline)}</small>
        </article>
      `,
      )
      .join("");
  }

  if (!controls.length) {
    $("governanceControls").className = "control-matrix empty-state";
    $("governanceControls").textContent = "No governance controls recorded.";
    return;
  }
  $("governanceControls").className = "control-matrix";
  $("governanceControls").innerHTML = controls
    .map(
      (control) => `
      <article class="control-item ${esc(control.status)}">
        <div>
          <strong>${esc(control.control_id)} · ${esc(control.area)}</strong>
          <span>${esc(control.owner)}</span>
        </div>
        <mark>${esc(control.status.replaceAll("_", " "))}</mark>
        <p>${esc(control.evidence)}</p>
        <small>${esc(control.next_action)}</small>
      </article>
    `,
    )
    .join("");
  if (blocked > 0) {
    $("controlBadge").textContent = `${blocked} blocked controls`;
  }
}

function renderTaskState(tasks, recruitment) {
  const completeLike = tasks.filter((task) => ["complete", "blocked", "human_review"].includes(task.status)).length;
  $("taskStateBadge").textContent = `${completeLike}/${tasks.length || 0} tasks resolved`;

  if (!tasks.length) {
    $("taskStateBoard").className = "task-state-board empty-state";
    $("taskStateBoard").textContent = "No task state recorded.";
  } else {
    $("taskStateBoard").className = "task-state-board";
    $("taskStateBoard").innerHTML = tasks
      .map(
        (task) => `
        <article class="task-item ${esc(task.status)}">
          <div>
            <strong>${esc(task.label)}</strong>
            <span>${esc(task.owner)}</span>
          </div>
          <mark>${esc(task.status.replaceAll("_", " "))}</mark>
          <p>${esc(task.summary)}</p>
          <small>${esc((task.evidence_refs || []).join(" | "))}</small>
        </article>
      `,
      )
      .join("");
  }

  if (!recruitment.length) {
    $("recruitmentLedger").className = "recruitment-ledger empty-state";
    $("recruitmentLedger").textContent = "No peer recruitment recorded.";
    return;
  }
  $("recruitmentLedger").className = "recruitment-ledger";
  $("recruitmentLedger").innerHTML = recruitment
    .map(
      (record) => `
      <article class="recruitment-item ${esc(record.status)}">
        <strong>${esc(record.recruiter)} -> ${esc(record.peer)}</strong>
        <span>${esc(record.status)}</span>
        <p>${esc(record.reason)}</p>
        <small>${esc(record.band_action)}</small>
      </article>
    `,
    )
    .join("");
}

function renderHandoffMap(messages) {
  const edges = [];
  for (const message of messages || []) {
    for (const target of message.mentions || []) {
      edges.push({
        source: message.sender,
        target,
        type: message.message_type,
      });
    }
  }
  const uniqueEdges = [];
  const seen = new Set();
  for (const edge of edges) {
    const key = `${edge.source}->${edge.target}:${edge.type}`;
    if (!seen.has(key)) {
      seen.add(key);
      uniqueEdges.push(edge);
    }
  }
  $("handoffBadge").textContent = `${uniqueEdges.length} routed edges`;
  if (!uniqueEdges.length) {
    $("handoffMap").className = "handoff-map empty-state";
    $("handoffMap").textContent = "No routed edges recorded.";
    return;
  }
  $("handoffMap").className = "handoff-map";
  $("handoffMap").innerHTML = uniqueEdges
    .map(
      (edge) => `
      <article class="handoff-edge ${esc(edge.type)}">
        <strong>${esc(edge.source)}</strong>
        <span>${esc(edge.type)}</span>
        <strong>${esc(edge.target)}</strong>
      </article>
    `,
    )
    .join("");
}

function renderEvidenceStrip(run) {
  const packet = run.context_packet;
  const gate = run.human_gate;
  $("evidenceStrip").innerHTML = `
    <div class="case-metric"><span>Collaboration Score</span><strong>${run.collaboration_score || 0}/100</strong></div>
    <div class="case-metric"><span>Shared Context</span><strong>${packet ? `${packet.readiness_score}/100 ready` : "Missing"}</strong></div>
    <div class="case-metric"><span>Human Gate</span><strong>${gate ? esc(gate.gate_status.replaceAll("_", " ")) : "Missing"}</strong></div>
    <div class="case-metric"><span>Audit Seal</span><strong>${run.audit_seal ? esc(run.audit_seal.digest.slice(0, 12)) : "Missing"}</strong></div>
  `;
}

function renderParticipants(participants) {
  $("participants").innerHTML = `<div class="participants-list">${participants
    .map((name) => `<div class="participant"><span class="dot"></span><span>${esc(name)}</span></div>`)
    .join("")}</div>`;
}

function renderTimeline(messages) {
  $("timeline").className = "timeline";
  $("timeline").innerHTML = messages
    .map((message) => {
      const mentions = message.mentions?.length
        ? `<div class="mentions">Routed to: ${message.mentions.map(esc).join(", ")}</div>`
        : "";
      return `
        <article class="message ${esc(message.message_type)}">
          <div class="message-meta">
            <span>${esc(message.sender)}</span>
            <span>${esc(message.message_type)}</span>
          </div>
          <p>${esc(message.content)}</p>
          ${mentions}
        </article>
      `;
    })
    .join("");
}

function renderArtifacts(artifacts) {
  $("artifacts").innerHTML = artifacts
    .map(
      (artifact) => `
      <article class="artifact">
        <span>Risk ${artifact.risk_score}/100 - Confidence ${Math.round(artifact.confidence * 100)}%</span>
        <h4>${esc(artifact.agent_name)}</h4>
        <p>${esc(artifact.summary)}</p>
        <ul>
          ${(artifact.findings || []).slice(0, 3).map((item) => `<li>${esc(item)}</li>`).join("")}
        </ul>
      </article>
    `,
    )
    .join("");
}

function renderContextPacket(packet) {
  if (!packet) {
    $("contextPacket").className = "context-packet empty-state";
    $("contextPacket").textContent = "No shared context packet was created.";
    return;
  }
  $("contextPacket").className = "context-packet";
  const consensus = (packet.consensus_points || []).map((item) => `<li>${esc(item)}</li>`).join("");
  const unresolved = (packet.unresolved_questions || []).map((item) => `<li>${esc(item)}</li>`).join("");
  const stateRows = Object.entries(packet.shared_state || {})
    .map(([key, value]) => `<div><span>${esc(key.replaceAll("_", " "))}</span><strong>${esc(value)}</strong></div>`)
    .join("");
  $("contextPacket").innerHTML = `
    <p>${esc(packet.summary)}</p>
    <div class="state-grid">${stateRows}</div>
    <div class="split-list">
      <div>
        <small>Consensus</small>
        <ul>${consensus}</ul>
      </div>
      <div>
        <small>Unresolved questions</small>
        <ul>${unresolved}</ul>
      </div>
    </div>
  `;
}

function renderChallengeReview(review) {
  if (!review) {
    $("challengeReview").className = "challenge-review empty-state";
    $("challengeReview").textContent = "No adversarial review recorded.";
    return;
  }
  $("challengeReview").className = "challenge-review";
  const objections = (review.objections || []).map((item) => `<li>${esc(item)}</li>`).join("");
  const revisions = (review.required_revisions || []).map((item) => `<li>${esc(item)}</li>`).join("");
  $("challengeReview").innerHTML = `
    <div class="challenge-summary ${esc(review.veto_level)}">
      <div><span>Veto level</span><strong>${esc(review.veto_level)}</strong></div>
      <div><span>Cleared</span><strong>${review.cleared_to_decide ? "Yes" : "No"}</strong></div>
      <div><span>Confidence</span><strong>${Math.round((review.confidence || 0) * 100)}%</strong></div>
    </div>
    <p>${esc(review.summary)}</p>
    <div class="split-list">
      <div>
        <small>Objections</small>
        <ul>${objections}</ul>
      </div>
      <div>
        <small>Required revisions</small>
        <ul>${revisions}</ul>
      </div>
    </div>
  `;
}

function renderTechnicalProof(profiles, auditSeal, provider) {
  if (!profiles.length && !auditSeal) {
    $("technicalProof").className = "technical-proof empty-state";
    $("technicalProof").textContent = "No technical proof recorded.";
    return;
  }
  $("technicalProof").className = "technical-proof";
  const profileRows = profiles
    .filter((profile) => profile.name !== "Human Procurement Lead")
    .map(
      (profile) => `
      <article class="profile-item">
        <strong>${esc(profile.name)}</strong>
        <span>${esc(profile.framework_profile)} - ${esc(profile.coordination_style)}</span>
      </article>
    `,
    )
    .join("");
  const seal = auditSeal
    ? `
      <div class="audit-box">
        <span>${esc(auditSeal.algorithm.toUpperCase())} audit seal</span>
        <code>${esc(auditSeal.digest)}</code>
        <small>${esc(auditSeal.sealed_scope)} - ${auditSeal.record_count} records - Provider ${esc(provider)}</small>
      </div>
    `
    : `<div class="audit-box"><span>Audit seal missing</span></div>`;
  $("technicalProof").innerHTML = `
    ${seal}
    <div class="profile-list">${profileRows}</div>
  `;
}

function renderJudgingEvidence(items) {
  if (!items.length) {
    $("judgingEvidence").className = "judging-list empty-state";
    $("judgingEvidence").textContent = "No judging evidence recorded.";
    return;
  }
  $("judgingEvidence").className = "judging-list";
  $("judgingEvidence").innerHTML = items
    .map(
      (item) => `
      <article class="judge-item ${esc(item.status)}">
        <strong>${esc(item.label)}</strong>
        <span>${esc(item.status)}</span>
        <p>${esc(item.detail)}</p>
      </article>
    `,
    )
    .join("");
}

function renderHumanGate(gate) {
  if (!gate) {
    $("humanGate").className = "human-gate empty-state";
    $("humanGate").textContent = "No human gate recorded.";
    return;
  }
  $("humanGate").className = "human-gate";
  $("humanGate").innerHTML = `
    <div class="gate-summary">
      <div><span>Status</span><strong>${esc(gate.gate_status.replaceAll("_", " "))}</strong></div>
      <div><span>Approver</span><strong>${esc(gate.approver)}</strong></div>
      <div><span>Signoffs</span><strong>${esc((gate.required_signoffs || []).join(", "))}</strong></div>
    </div>
    <p>${esc(gate.rationale)}</p>
    <small>Approval packet</small>
    <ul class="conditions">
      ${(gate.approval_packet || []).map((item) => `<li>${esc(item)}</li>`).join("")}
    </ul>
  `;
}

function renderDecision(decision) {
  if (!decision) return;
  const label = decision.decision.replaceAll("_", " ");
  $("decisionBadge").textContent = `${label} - ${decision.score}/100`;
  $("decision").className = "decision";
  $("decision").innerHTML = `
    <h4>${esc(label.toUpperCase())}</h4>
    <p>${esc(decision.executive_summary)}</p>
    <small>Approval memo</small>
    <p>${esc(decision.approval_memo)}</p>
    <small>Conditions</small>
    <ul class="conditions">
      ${(decision.conditions || []).map((item) => `<li>${esc(item)}</li>`).join("")}
    </ul>
    <small>Risk register</small>
    <ul class="risk-list">
      ${(decision.risk_register || [])
        .map(
          (item) =>
            `<li><strong>${esc(item.area)} - ${esc(item.severity)}</strong><br>${esc(item.mitigation)}<br><small>${esc(item.owner)}</small></li>`,
        )
        .join("")}
    </ul>
  `;
}

init().catch((error) => {
  $("health").textContent = error.message;
});
