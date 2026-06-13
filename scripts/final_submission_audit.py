from __future__ import annotations

import json
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT_DIR / "output" / "submission"
PACKAGE_PATH = OUTPUT_DIR / "procureguard-public-submission-package.zip"
MANIFEST_PATH = OUTPUT_DIR / "procureguard-public-submission-manifest.json"
LATEST_REPORT_PATH = OUTPUT_DIR / "procureguard-latest-report.md"
LATEST_BUNDLE_PATH = OUTPUT_DIR / "procureguard-evidence-bundle-latest.zip"
DEMO_VIDEO_PATH = OUTPUT_DIR / "procureguard-demo.webm"
PUBLIC_REPOSITORY_URL = "https://github.com/theihtisham/procureguard-ai-band-agents"


@dataclass
class AuditItem:
    category: str
    requirement: str
    status: str
    evidence: str


def file_ok(path: Path, *, min_bytes: int = 1) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size >= min_bytes


def text_contains(path: Path, terms: list[str]) -> bool:
    if not file_ok(path):
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    return all(term in text for term in terms)


def zip_contains(path: Path, names: list[str]) -> bool:
    if not file_ok(path):
        return False
    with zipfile.ZipFile(path) as archive:
        existing = set(archive.namelist())
    return all(name in existing for name in names)


def load_manifest() -> dict:
    if not file_ok(MANIFEST_PATH):
        return {}
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def item(category: str, requirement: str, passed: bool, evidence: str) -> AuditItem:
    return AuditItem(category, requirement, "PASS" if passed else "FAIL", evidence)


def main() -> None:
    manifest = load_manifest()
    proof_points = set(manifest.get("proof_points", []))
    external_steps = manifest.get("external_steps_remaining", [])
    package_names = [
        "README.md",
        "app/workflow.py",
        "static/index.html",
        "docs/submission.md",
        "docs/demo_script.md",
        "output/submission/procureguard-latest-report.md",
        "output/submission/procureguard-evidence-bundle-latest.zip",
        "output/submission/procureguard-demo.webm",
        "output/playwright/procureguard-impact-controls-final.png",
    ]

    checks = [
        item("Basic Information", "Project title and descriptions are drafted", text_contains(ROOT_DIR / "docs" / "submission.md", ["ProcureGuard AI", "Short Description", "Long Description"]), "docs/submission.md"),
        item("Tags", "Technology/category tags are listed", text_contains(ROOT_DIR / "docs" / "submission_checklist.md", ["Band", "AI/ML API", "Multi-Agent", "Human-in-the-loop"]), "docs/submission_checklist.md"),
        item("Core Challenge", "At least 3 agents collaborate", "8 AI agents plus human approval gate" in proof_points, "manifest proof_points"),
        item("Core Challenge", "Band-style collaboration is central", "Coordination Handoff Map generated from @mention edges" in proof_points, "manifest proof_points"),
        item("Core Challenge", "Task state and handoffs are visible", "Task State & Recruitment board with owners, status, and evidence refs" in proof_points, "manifest proof_points"),
        item("Judging", "Business value proof exists", "Business Impact & Controls matrix for enterprise value proof" in proof_points, "manifest proof_points"),
        item("Judging", "Report includes governance sections", text_contains(LATEST_REPORT_PATH, ["Business Impact", "Governance Control Matrix", "Task State Board", "Peer Recruitment Ledger"]), "output/submission/procureguard-latest-report.md"),
        item("Artifacts", "Cover image exists", file_ok(OUTPUT_DIR / "procureguard-cover.png", min_bytes=10_000), "output/submission/procureguard-cover.png"),
        item("Artifacts", "Slides preview exists", file_ok(OUTPUT_DIR / "procureguard-slides-preview.png", min_bytes=10_000), "output/submission/procureguard-slides-preview.png"),
        item("Artifacts", "Evidence bundle exists", file_ok(LATEST_BUNDLE_PATH, min_bytes=1_000), "output/submission/procureguard-evidence-bundle-latest.zip"),
        item("Artifacts", "Evidence bundle has run/report/manifest", zip_contains(LATEST_BUNDLE_PATH, ["run.json", "report.md", "audit-manifest.json"]), "evidence bundle contents"),
        item("Artifacts", "Demo video exists", file_ok(DEMO_VIDEO_PATH, min_bytes=1_000_000), "output/submission/procureguard-demo.webm"),
        item("Code Repository", "Public-safe source package exists", file_ok(PACKAGE_PATH, min_bytes=1_000_000), "output/submission/procureguard-public-submission-package.zip"),
        item("Code Repository", "Public package includes source and proof artifacts", zip_contains(PACKAGE_PATH, package_names), "public package contents"),
        item("Code Repository", "Public GitHub Repository URL is documented", text_contains(ROOT_DIR / "docs" / "lablab_submission_form.md", [PUBLIC_REPOSITORY_URL]), "docs/lablab_submission_form.md"),
        item("Safety", "Secret files are excluded by manifest", set(manifest.get("excluded_secret_files", [])) == {".env", ".env.local", "agent_config.yaml"}, "manifest excluded_secret_files"),
        item("Deploy", "Render config exists", file_ok(ROOT_DIR / "render.yaml"), "render.yaml"),
        item("Deploy", "Docker config exists", file_ok(ROOT_DIR / "Dockerfile"), "Dockerfile"),
    ]

    external = [
        AuditItem("External Submission", "Hosted demo Application URL", "EXTERNAL", "Deploy with render.yaml or Docker."),
        AuditItem("External Submission", "Real Band Remote Agent room recording", "EXTERNAL", "Follow docs/band_live_setup.md."),
    ]
    if external_steps:
        external.append(AuditItem("Manifest", "External steps are tracked", "EXTERNAL", "; ".join(external_steps)))

    all_items = checks + external
    failed = [entry for entry in checks if entry.status == "FAIL"]
    result = {
        "local_ready": not failed,
        "final_submission_ready": not failed and not external,
        "pass_count": sum(1 for entry in checks if entry.status == "PASS"),
        "fail_count": len(failed),
        "external_count": len(external),
        "items": [entry.__dict__ for entry in all_items],
    }
    print(json.dumps(result, indent=2))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
