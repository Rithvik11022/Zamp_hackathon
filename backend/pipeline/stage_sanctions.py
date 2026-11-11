from __future__ import annotations

import json
import os

from services.fuzzy import token_sort_ratio as _token_sort_ratio

from models import StageResult, StageStatus, VendorSubmission

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
MATCH_THRESHOLD = 0.85


def _load_sdn_list() -> list[dict]:
    path = os.path.join(DATA_DIR, "sdn_list.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _normalize(name: str) -> str:
    return " ".join(name.lower().strip().split())


def run(submission: VendorSubmission) -> StageResult:
    sdn_entries = _load_sdn_list()
    if not sdn_entries:
        return StageResult(
            stage_key="sanctions_screening",
            stage_number=5,
            label="Sanctions Screening",
            status=StageStatus.PASS,
            reasoning="Sanctions list not available. Screening skipped.",
            details={"sdn_entries_checked": 0},
        )

    sub_name = _normalize(submission.company_name)
    sub_trading = _normalize(submission.trading_name) if submission.trading_name else ""

    names_to_check = [sub_name]
    if sub_trading and sub_trading != sub_name:
        names_to_check.append(sub_trading)

    hits: list[dict] = []

    for entry in sdn_entries:
        entry_name = _normalize(entry.get("name", ""))
        aliases = [_normalize(a) for a in entry.get("aliases", [])]
        all_sdn_names = [entry_name] + aliases

        for check_name in names_to_check:
            for sdn_name in all_sdn_names:
                score = _token_sort_ratio(check_name, sdn_name) / 100.0
                if score >= MATCH_THRESHOLD:
                    hits.append({
                        "sdn_name": entry.get("name", ""),
                        "sdn_id": entry.get("id", ""),
                        "sdn_type": entry.get("type", "Entity"),
                        "sdn_program": entry.get("program", "Unknown"),
                        "matched_against": check_name,
                        "similarity": round(score, 2),
                    })

    if not hits:
        return StageResult(
            stage_key="sanctions_screening",
            stage_number=5,
            label="Sanctions Screening",
            status=StageStatus.PASS,
            reasoning=(
                f"Screened against {len(sdn_entries)} OFAC SDN entries. "
                "No matches found. Entity is clear."
            ),
            details={"sdn_entries_checked": len(sdn_entries), "hits": []},
        )

    best = max(hits, key=lambda h: h["similarity"])
    return StageResult(
        stage_key="sanctions_screening",
        stage_number=5,
        label="Sanctions Screening",
        status=StageStatus.FAIL,
        reasoning=(
            f"SANCTIONS ALERT: Entity name fuzzy-matches OFAC SDN entry "
            f"'{best['sdn_name']}' (similarity: {best['similarity']:.0%}). "
            f"Program: {best['sdn_program']}. "
            "MANDATORY ESCALATION required per compliance policy. "
            "This match cannot be overridden without compliance officer review."
        ),
        details={"sdn_entries_checked": len(sdn_entries), "hits": hits},
    )
