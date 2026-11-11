from __future__ import annotations

import asyncio
import time
from typing import AsyncGenerator

from models import Decision, StageResult, StageStatus, VendorSubmission
from pipeline import stage_completeness, stage_format, stage_crossref, stage_duplicate, stage_sanctions, stage_ai_analysis


STAGES = [
    ("completeness", "Completeness Check", stage_completeness),
    ("format_validation", "Format Validation", stage_format),
    ("cross_reference", "Cross-Reference Check", stage_crossref),
    ("duplicate_detection", "Duplicate Detection", stage_duplicate),
    ("sanctions_screening", "Sanctions Screening", stage_sanctions),
    ("ai_document_analysis", "AI Document Analysis", stage_ai_analysis),
]

TOTAL_STAGES = len(STAGES)


def _compute_decision(results: list[StageResult]) -> tuple[Decision, str]:
    has_fail = any(r.status == StageStatus.FAIL for r in results)
    has_warn = any(r.status == StageStatus.WARN for r in results)

    if has_fail:
        fail_stages = [r for r in results if r.status == StageStatus.FAIL]
        reasons = [f"{r.label}: {r.reasoning}" for r in fail_stages]
        return Decision.REJECTED, (
            f"Vendor submission REJECTED. {len(fail_stages)} validation stage(s) failed: "
            + " | ".join(reasons)
        )

    if has_warn:
        warn_stages = [r for r in results if r.status == StageStatus.WARN]
        reasons = [f"{r.label}: {r.reasoning}" for r in warn_stages]
        return Decision.PENDING, (
            f"Vendor submission requires HUMAN REVIEW. {len(warn_stages)} stage(s) flagged warnings: "
            + " | ".join(reasons)
        )

    return Decision.APPROVED, (
        "Vendor submission APPROVED. All validation stages passed successfully."
    )


async def run_pipeline(submission: VendorSubmission) -> AsyncGenerator[dict, None]:
    results: list[StageResult] = []

    for i, (key, label, stage_module) in enumerate(STAGES):
        stage_num = i + 1

        yield {
            "event": "stage_start",
            "data": {
                "stage": key,
                "stage_number": stage_num,
                "label": label,
                "total_stages": TOTAL_STAGES,
            },
        }

        start = time.monotonic()

        if key == "ai_document_analysis":
            result = await stage_module.run(submission)
        else:
            result = await asyncio.to_thread(stage_module.run, submission)

        elapsed_ms = int((time.monotonic() - start) * 1000)
        result.duration_ms = elapsed_ms

        results.append(result)

        yield {
            "event": "stage_complete",
            "data": result.model_dump(),
        }

        await asyncio.sleep(0.4)

    decision, reasoning = _compute_decision(results)

    yield {
        "event": "pipeline_complete",
        "data": {
            "decision": decision.value,
            "reasoning": reasoning,
            "stages": [r.model_dump() for r in results],
        },
    }
