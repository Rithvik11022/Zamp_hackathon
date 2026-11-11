from __future__ import annotations

import json
import os

from services.fuzzy import token_sort_ratio as _token_sort_ratio

from models import StageResult, StageStatus, VendorSubmission

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def _normalize_name(name: str) -> str:
    replacements = {
        "pvt": "private",
        "ltd": "limited",
        "llc": "",
        "inc": "",
        "incorporated": "",
        "corp": "corporation",
        "gmbh": "",
        "ag": "",
        "s.a.": "",
        "sa": "",
        "bv": "",
        "b.v.": "",
        "co.": "company",
        "& co": "",
        "technologies": "tech",
        "solutions": "",
        "services": "",
    }
    lower = name.lower().strip()
    for abbr, full in replacements.items():
        lower = lower.replace(abbr, full)
    return " ".join(lower.split())


def _load_existing_vendors() -> list[dict]:
    path = os.path.join(DATA_DIR, "existing_vendors.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run(submission: VendorSubmission) -> StageResult:
    existing = _load_existing_vendors()
    if not existing:
        return StageResult(
            stage_key="duplicate_detection",
            stage_number=4,
            label="Duplicate Detection",
            status=StageStatus.PASS,
            reasoning="No existing vendors in the system. No duplicates possible.",
            details={"existing_vendor_count": 0},
        )

    sub_name = _normalize_name(submission.company_name)
    sub_tax = submission.tax_id.strip().upper()
    sub_iban = submission.iban.replace(" ", "").upper()

    matches: list[dict] = []

    for vendor in existing:
        v_name = _normalize_name(vendor.get("company_name", ""))
        v_tax = vendor.get("tax_id", "").strip().upper()
        v_iban = vendor.get("iban", "").replace(" ", "").upper()

        name_score = _token_sort_ratio(sub_name, v_name) / 100.0
        tax_match = sub_tax == v_tax and sub_tax != ""
        iban_match = sub_iban == v_iban and sub_iban != ""

        if name_score >= 0.75 or tax_match or iban_match:
            match_reasons = []
            if name_score >= 0.75:
                match_reasons.append(f"name similarity {name_score:.0%}")
            if tax_match:
                match_reasons.append("identical tax ID")
            if iban_match:
                match_reasons.append("identical bank account")

            matches.append({
                "existing_vendor": vendor.get("company_name", "Unknown"),
                "existing_vendor_id": vendor.get("vendor_id", "N/A"),
                "name_similarity": round(name_score, 2),
                "tax_id_match": tax_match,
                "iban_match": iban_match,
                "match_reasons": match_reasons,
            })

    if not matches:
        return StageResult(
            stage_key="duplicate_detection",
            stage_number=4,
            label="Duplicate Detection",
            status=StageStatus.PASS,
            reasoning=f"Checked against {len(existing)} existing vendors. No duplicates found.",
            details={"existing_vendor_count": len(existing), "matches": []},
        )

    best = max(matches, key=lambda m: m["name_similarity"])
    has_exact_key_match = any(m["tax_id_match"] or m["iban_match"] for m in matches)

    if has_exact_key_match:
        return StageResult(
            stage_key="duplicate_detection",
            stage_number=4,
            label="Duplicate Detection",
            status=StageStatus.WARN,
            reasoning=(
                f"Possible duplicate of existing vendor '{best['existing_vendor']}' "
                f"({', '.join(best['match_reasons'])}). "
                "Requires human review to determine if this is the same entity."
            ),
            details={"matches": matches, "existing_vendor_count": len(existing)},
        )

    if best["name_similarity"] >= 0.85:
        return StageResult(
            stage_key="duplicate_detection",
            stage_number=4,
            label="Duplicate Detection",
            status=StageStatus.WARN,
            reasoning=(
                f"High similarity to existing vendor '{best['existing_vendor']}' "
                f"(name match: {best['name_similarity']:.0%}). "
                "Review needed to confirm this is a distinct entity."
            ),
            details={"matches": matches, "existing_vendor_count": len(existing)},
        )

    return StageResult(
        stage_key="duplicate_detection",
        stage_number=4,
        label="Duplicate Detection",
        status=StageStatus.PASS,
        reasoning=(
            f"Checked against {len(existing)} existing vendors. "
            f"Closest match: '{best['existing_vendor']}' "
            f"(similarity: {best['name_similarity']:.0%}) — below duplicate threshold."
        ),
        details={"matches": matches, "existing_vendor_count": len(existing)},
    )
