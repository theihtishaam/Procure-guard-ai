from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
os.environ["ENABLE_LIVE_LLM"] = "0"

from app.sample_cases import SAMPLE_CASES
from app.workflow import ProcureGuardWorkflow


async def main() -> None:
    workflow = ProcureGuardWorkflow(force_heuristic=True)
    run = await workflow.run(SAMPLE_CASES[0])
    assert len(run.participants) >= 3
    assert len(run.artifacts) >= 4
    assert run.context_packet is not None
    assert run.challenge_review is not None
    assert run.decision is not None
    assert run.human_gate is not None
    assert run.audit_seal is not None
    assert len(run.task_state) >= 7
    assert len(run.peer_recruitment) >= 8
    assert len(run.business_impact) >= 4
    assert len(run.governance_controls) >= 5
    assert run.collaboration_score >= 90
    assert any(message.message_type == "recruitment" for message in run.messages)
    assert any(message.message_type == "handoff" for message in run.messages)
    assert any(message.message_type == "context" for message in run.messages)
    assert any(message.message_type == "challenge" for message in run.messages)
    assert any(message.message_type == "approval_gate" for message in run.messages)
    assert any(message.message_type == "audit" for message in run.messages)
    print(
        {
            "run_id": run.run_id,
            "provider": run.provider,
            "messages": len(run.messages),
            "artifacts": len(run.artifacts),
            "task_state": len(run.task_state),
            "peer_recruitment": len(run.peer_recruitment),
            "business_impact": len(run.business_impact),
            "governance_controls": len(run.governance_controls),
            "collaboration_score": run.collaboration_score,
            "challenge": run.challenge_review.veto_level,
            "audit_seal": run.audit_seal.digest[:16],
            "decision": run.decision.decision,
        }
    )


if __name__ == "__main__":
    asyncio.run(main())
