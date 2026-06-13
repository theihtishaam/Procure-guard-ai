from __future__ import annotations

import json
import os
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.config import ROOT_DIR, get_settings
from app.models import VendorCase
from app.report import workflow_markdown_report
from app.sample_cases import SAMPLE_CASES, get_case
from app.storage import store
from app.workflow import ProcureGuardWorkflow


STATIC_DIR = ROOT_DIR / "static"
OUTPUT_DIR = ROOT_DIR / "output"

app = FastAPI(title="ProcureGuard AI", version="0.1.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
if OUTPUT_DIR.exists():
    app.mount("/output", StaticFiles(directory=OUTPUT_DIR), name="output")


class RunRequest(BaseModel):
    case_id: str | None = None
    case: VendorCase | None = None
    force_heuristic: bool = False


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> FileResponse:
    return FileResponse(STATIC_DIR / "favicon.svg", media_type="image/svg+xml")


@app.get("/api/health")
def health() -> dict:
    settings = get_settings()
    return {
        "ok": True,
        "app": settings.app_name,
        "live_llm_configured": bool(settings.enable_live_llm and settings.aimlapi_api_key),
        "band_enabled": settings.band_enabled,
    }


@app.get("/api/sample-cases")
def sample_cases() -> list[dict]:
    return [case.model_dump() for case in SAMPLE_CASES]


@app.post("/api/workflows/run")
async def run_workflow(request: RunRequest) -> dict:
    if request.case is not None:
        case = request.case
    elif request.case_id:
        try:
            case = get_case(request.case_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Unknown case_id") from exc
    else:
        case = SAMPLE_CASES[0]

    workflow = ProcureGuardWorkflow(force_heuristic=request.force_heuristic)
    run = await workflow.run(case)
    store.save(run)
    return run.model_dump(mode="json")


@app.get("/api/workflows/{run_id}")
def get_run(run_id: str) -> dict:
    run = store.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run.model_dump(mode="json")


@app.get("/api/workflows/{run_id}/report.md", response_class=PlainTextResponse)
def get_run_report(run_id: str) -> PlainTextResponse:
    run = store.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    filename = f"procureguard-{run.case.vendor_name.lower().replace(' ', '-')}-{run.run_id}.md"
    return PlainTextResponse(
        workflow_markdown_report(run),
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/workflows/{run_id}/bundle.zip")
def get_run_bundle(run_id: str) -> Response:
    run = store.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    run_json = run.model_dump(mode="json")
    audit_manifest = {
        "app": "ProcureGuard AI",
        "run_id": run.run_id,
        "case_id": run.case.case_id,
        "vendor_name": run.case.vendor_name,
        "provider": run.provider,
        "mode": run.mode,
        "collaboration_score": run.collaboration_score,
        "message_count": len(run.messages),
        "artifact_count": len(run.artifacts),
        "participants": run.participants,
        "challenge": run.challenge_review.model_dump(mode="json") if run.challenge_review else None,
        "decision": run.decision.decision if run.decision else None,
        "human_gate": run.human_gate.gate_status if run.human_gate else None,
        "task_state": [item.model_dump(mode="json") for item in run.task_state],
        "peer_recruitment": [item.model_dump(mode="json") for item in run.peer_recruitment],
        "business_impact": [item.model_dump(mode="json") for item in run.business_impact],
        "governance_controls": [item.model_dump(mode="json") for item in run.governance_controls],
        "audit_seal": run.audit_seal.model_dump(mode="json") if run.audit_seal else None,
        "requirements_proof": [item.model_dump(mode="json") for item in run.collaboration_evidence],
    }
    readme = (
        "# ProcureGuard Evidence Bundle\n\n"
        "This bundle contains the full run record, human-readable report, and audit manifest for one "
        "Band-style multi-agent workflow run.\n\n"
        "- `run.json`: full structured run output.\n"
        "- `report.md`: readable enterprise approval report.\n"
        "- `audit-manifest.json`: summary of collaboration score, task state, recruitment ledger, business impact, controls, challenge review, decision, human gate, and audit seal.\n"
    )

    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("README.md", readme)
        archive.writestr("run.json", json.dumps(run_json, indent=2))
        archive.writestr("report.md", workflow_markdown_report(run))
        archive.writestr("audit-manifest.json", json.dumps(audit_manifest, indent=2))

    filename = f"procureguard-{run.case.vendor_name.lower().replace(' ', '-')}-{run.run_id}-evidence.zip"
    return Response(
        buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


if __name__ == "__main__":
    settings = get_settings()
    port = int(os.getenv("PORT", str(settings.port)))
    host = os.getenv("HOST", settings.host)
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
