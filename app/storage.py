from __future__ import annotations

import json
from pathlib import Path

from app.config import ROOT_DIR
from app.models import WorkflowRun


RUNS_DIR = ROOT_DIR / "data" / "runs"
RUNS_DIR.mkdir(parents=True, exist_ok=True)


class RunStore:
    def __init__(self) -> None:
        self._runs: dict[str, WorkflowRun] = {}

    def save(self, run: WorkflowRun) -> WorkflowRun:
        self._runs[run.run_id] = run
        path = RUNS_DIR / f"{run.run_id}.json"
        path.write_text(run.model_dump_json(indent=2), encoding="utf-8")
        return run

    def get(self, run_id: str) -> WorkflowRun | None:
        if run_id in self._runs:
            return self._runs[run_id]
        path = RUNS_DIR / f"{run_id}.json"
        if not path.exists():
            return None
        run = WorkflowRun.model_validate(json.loads(path.read_text(encoding="utf-8")))
        self._runs[run_id] = run
        return run


store = RunStore()
