from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

os.environ["ENABLE_LIVE_LLM"] = "0"

from fastapi.testclient import TestClient

from app.main import app


CUSTOM_CASE = {
    "case_id": "case-verify-custom",
    "requester": "Jordan Lee",
    "department": "IT Operations",
    "vendor_name": "Acme AI Ops",
    "product": "AI incident triage assistant",
    "requested_amount_usd": 68000,
    "renewal_or_new": "new",
    "business_need": "Reduce alert triage time and route incidents to the right owner before reliability review.",
    "data_access": ["support tickets", "incident logs", "employee emails"],
    "integrations": ["ServiceNow", "Slack", "Okta"],
    "timeline": "pilot within 45 days",
    "notes": "Vendor has SOC 2 summary but no DPA review yet.",
}


def assert_run_shape(run: dict) -> None:
    assert len(run["participants"]) >= 9
    assert len(run["artifacts"]) >= 4
    assert run["context_packet"]
    assert run["challenge_review"]
    assert run["decision"]
    assert run["human_gate"]
    assert run["audit_seal"]
    assert len(run["task_state"]) >= 7
    assert len(run["peer_recruitment"]) >= 8
    assert len(run["business_impact"]) >= 4
    assert len(run["governance_controls"]) >= 5
    assert run["collaboration_score"] >= 90
    assert any(message["message_type"] == "handoff" for message in run["messages"])
    assert any(message["message_type"] == "recruitment" for message in run["messages"])
    assert any(message["message_type"] == "challenge" for message in run["messages"])
    assert any(message["message_type"] == "audit" for message in run["messages"])
    assert any(item["label"] == "Task state coordination" and item["status"] == "met" for item in run["collaboration_evidence"])
    assert any(item["label"] == "Peer recruitment path" and item["status"] == "met" for item in run["collaboration_evidence"])
    assert any(item["label"] == "Business impact model" and item["status"] == "met" for item in run["collaboration_evidence"])
    assert any(item["label"] == "Governance control matrix" and item["status"] == "met" for item in run["collaboration_evidence"])
    routed_edges = [
        (message["sender"], mention)
        for message in run["messages"]
        for mention in message["mentions"]
    ]
    assert len(routed_edges) >= 8
    if not run["challenge_review"]["cleared_to_decide"]:
        assert run["decision"]["decision"] == "escalate"


def main() -> None:
    client = TestClient(app)

    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["ok"] is True

    for path in ["/", "/static/cover.html", "/static/slides.html", "/static/assets/procureguard-dashboard-final.png"]:
        response = client.get(path)
        assert response.status_code == 200, path

    sample_response = client.post("/api/workflows/run", json={"case_id": "case-vectorcrm", "force_heuristic": True})
    assert sample_response.status_code == 200, sample_response.text
    sample_run = sample_response.json()
    assert sample_run["provider"] == "heuristic"
    assert_run_shape(sample_run)

    report_response = client.get(f"/api/workflows/{sample_run['run_id']}/report.md")
    assert report_response.status_code == 200
    assert "Red Team Challenge" in report_response.text
    assert "Task State Board" in report_response.text
    assert "Peer Recruitment Ledger" in report_response.text
    assert "Business Impact" in report_response.text
    assert "Governance Control Matrix" in report_response.text
    assert "Audit Seal" in report_response.text

    bundle_response = client.get(f"/api/workflows/{sample_run['run_id']}/bundle.zip")
    assert bundle_response.status_code == 200
    assert bundle_response.headers["content-type"] == "application/zip"
    assert len(bundle_response.content) > 1000

    custom_response = client.post("/api/workflows/run", json={"case": CUSTOM_CASE, "force_heuristic": True})
    assert custom_response.status_code == 200, custom_response.text
    custom_run = custom_response.json()
    assert custom_run["provider"] == "heuristic"
    assert custom_run["case"]["vendor_name"] == "Acme AI Ops"
    assert_run_shape(custom_run)

    print(
        {
            "sample_run": sample_run["run_id"],
            "custom_run": custom_run["run_id"],
            "sample_score": sample_run["collaboration_score"],
            "custom_score": custom_run["collaboration_score"],
            "sample_decision": sample_run["decision"]["decision"],
            "custom_decision": custom_run["decision"]["decision"],
        }
    )


if __name__ == "__main__":
    main()
