from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT_DIR / "output" / "submission"
PACKAGE_PATH = OUTPUT_DIR / "procureguard-public-submission-package.zip"
MANIFEST_PATH = OUTPUT_DIR / "procureguard-public-submission-manifest.json"
LATEST_REPORT_PATH = OUTPUT_DIR / "procureguard-latest-report.md"
LATEST_BUNDLE_PATH = OUTPUT_DIR / "procureguard-evidence-bundle-latest.zip"
sys.path.insert(0, str(ROOT_DIR))

INCLUDE_FILES = [
    "README.md",
    ".env.example",
    "agent_config.example.yaml",
    "pyproject.toml",
    "uv.lock",
    "Dockerfile",
    "Procfile",
    "render.yaml",
    "docs/band_live_setup.md",
    "docs/competitive_research.md",
    "docs/deep_winning_plan.md",
    "docs/demo_script.md",
    "docs/judging_map.md",
    "docs/lablab_submission_form.md",
    "docs/pitch_deck.md",
    "docs/submission.md",
    "docs/submission_checklist.md",
    "static/cover.html",
    "static/slides.html",
    "static/assets/procureguard-cover.png",
    "static/assets/procureguard-dashboard-final.png",
    "output/submission/procureguard-cover.png",
    "output/submission/procureguard-slides-preview.png",
    "output/submission/procureguard-demo.webm",
    "output/submission/procureguard-latest-report.md",
    "output/submission/procureguard-evidence-bundle-latest.zip",
    "output/playwright/procureguard-dashboard-final.png",
    "output/playwright/procureguard-mobile-final.png",
    "output/playwright/procureguard-custom-final.png",
    "output/playwright/procureguard-handoff-map-final.png",
    "output/playwright/procureguard-fast-demo-mode-final.png",
    "output/playwright/procureguard-task-state-final.png",
    "output/playwright/procureguard-impact-controls-final.png",
]

INCLUDE_GLOBS = [
    "app/**/*.py",
    "data/**/*",
    "scripts/*.py",
    "static/index.html",
    "static/app.js",
    "static/styles.css",
    "static/favicon.svg",
]

FORBIDDEN_NAMES = {
    ".env",
    ".env.local",
    "agent_config.yaml",
}

TEXT_SUFFIXES = {".css", ".html", ".js", ".json", ".md", ".py", ".toml", ".txt", ".yaml", ".yml"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scan_text_file(path: Path) -> list[str]:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    findings = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if re.search(r"(AIMLAPI_API_KEY|OPENAI_API_KEY)\s*=\s*\S+", line) and not line.rstrip().endswith("="):
            if "your-key" not in line and "..." not in line:
                findings.append(f"{path.relative_to(ROOT_DIR)}:{line_number} contains a non-placeholder API key assignment")
        if re.search(r"(api_key|password|secret)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}", line, re.IGNORECASE):
            if "(" not in line and "<" not in line and "example" not in line.lower():
                findings.append(f"{path.relative_to(ROOT_DIR)}:{line_number} may contain a secret-like value")
    return findings


def iter_package_files() -> list[str]:
    files = list(INCLUDE_FILES)
    for pattern in INCLUDE_GLOBS:
        for path in ROOT_DIR.glob(pattern):
            if path.is_file():
                files.append(path.relative_to(ROOT_DIR).as_posix())
    return sorted(dict.fromkeys(files))


async def generate_latest_artifacts() -> None:
    os.environ["ENABLE_LIVE_LLM"] = "0"

    from app.report import workflow_markdown_report
    from app.sample_cases import SAMPLE_CASES
    from app.workflow import ProcureGuardWorkflow

    workflow = ProcureGuardWorkflow(force_heuristic=True)
    run = await workflow.run(SAMPLE_CASES[0])
    report = workflow_markdown_report(run)
    LATEST_REPORT_PATH.write_text(report, encoding="utf-8")

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
        "task_state_count": len(run.task_state),
        "peer_recruitment_count": len(run.peer_recruitment),
        "business_impact_count": len(run.business_impact),
        "governance_control_count": len(run.governance_controls),
        "participants": run.participants,
        "task_state": [item.model_dump(mode="json") for item in run.task_state],
        "peer_recruitment": [item.model_dump(mode="json") for item in run.peer_recruitment],
        "business_impact": [item.model_dump(mode="json") for item in run.business_impact],
        "governance_controls": [item.model_dump(mode="json") for item in run.governance_controls],
        "challenge": run.challenge_review.model_dump(mode="json") if run.challenge_review else None,
        "decision": run.decision.decision if run.decision else None,
        "human_gate": run.human_gate.gate_status if run.human_gate else None,
        "audit_seal": run.audit_seal.model_dump(mode="json") if run.audit_seal else None,
        "requirements_proof": [item.model_dump(mode="json") for item in run.collaboration_evidence],
    }
    readme = (
        "# ProcureGuard Evidence Bundle\n\n"
        "This bundle contains the full run record, human-readable report, and audit manifest for one "
        "Band-style multi-agent workflow run.\n\n"
        "- `run.json`: full structured run output.\n"
        "- `report.md`: readable enterprise approval report.\n"
        "- `audit-manifest.json`: summary of collaboration score, task state, recruitment ledger, "
        "business impact, governance controls, challenge review, decision, human gate, and audit seal.\n"
    )
    with ZipFile(LATEST_BUNDLE_PATH, "w", ZIP_DEFLATED) as archive:
        archive.writestr("README.md", readme)
        archive.writestr("run.json", json.dumps(run_json, indent=2))
        archive.writestr("report.md", report)
        archive.writestr("audit-manifest.json", json.dumps(audit_manifest, indent=2))


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    asyncio.run(generate_latest_artifacts())
    missing = []
    records = []
    secret_findings = []

    for relative in iter_package_files():
        path = ROOT_DIR / relative
        if not path.exists():
            missing.append(relative)
            continue
        if any(part in FORBIDDEN_NAMES for part in path.parts):
            raise RuntimeError(f"Forbidden file selected for package: {relative}")
        secret_findings.extend(scan_text_file(path))
        records.append(
            {
                "path": relative.replace("\\", "/"),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )

    if missing:
        raise RuntimeError("Missing required package files: " + ", ".join(missing))
    if secret_findings:
        raise RuntimeError("Secret scan failed:\n" + "\n".join(secret_findings))

    manifest = {
        "package_name": "ProcureGuard AI public submission package",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": {
            "title": "ProcureGuard AI",
            "track": "Internal Enterprise Workflows",
            "hackathon": "Band of Agents Hackathon",
        },
        "contents": records,
        "proof_points": [
            "8 AI agents plus human approval gate",
            "17-message Band-style room timeline",
            "Coordination Handoff Map generated from @mention edges",
            "Task State & Recruitment board with owners, status, and evidence refs",
            "Business Impact & Controls matrix for enterprise value proof",
            "Shared Context Packet from Evidence Clerk",
            "Red Team Challenge with escalation guardrail",
            "SHA-256 audit seal",
            "Evidence bundle ZIP export",
            "Custom vendor case runner",
            "Fast demo mode for reliable recordings without spending credits",
            "Pitch deck, cover image, screenshots, and report artifacts",
            "Recorded dashboard demo video artifact",
            "Render and Docker deployment configuration",
            "Final submission audit and copy-paste lablab form packet",
            "Band Human API remote-agent registration helper",
        ],
        "external_steps_remaining": [
            "Deploy app and add final demo URL to lablab submission.",
            "Record or append real Band Remote Agent room using docs/band_live_setup.md.",
        ],
        "excluded_secret_files": sorted(FORBIDDEN_NAMES),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    with ZipFile(PACKAGE_PATH, "w", ZIP_DEFLATED) as archive:
        archive.writestr("procureguard-public-submission-manifest.json", json.dumps(manifest, indent=2))
        for record in records:
            path = ROOT_DIR / record["path"]
            archive.write(path, arcname=record["path"])

    print(
        json.dumps(
            {
                "package": str(PACKAGE_PATH),
                "manifest": str(MANIFEST_PATH),
                "file_count": len(records) + 1,
                "package_bytes": PACKAGE_PATH.stat().st_size,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise
