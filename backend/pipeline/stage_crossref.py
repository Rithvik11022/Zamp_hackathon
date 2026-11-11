from __future__ import annotations

from services.fuzzy import token_sort_ratio as _token_sort_ratio

from models import StageResult, StageStatus, VendorSubmission


def _normalize(name: str) -> str:
    replacements = {
        "pvt": "private",
        "ltd": "limited",
        "llc": "",
        "inc": "",
        "corp": "corporation",
        "gmbh": "",
        "ag": "",
        "s.a.": "",
        "sa": "",
        "bv": "",
        "b.v.": "",
        "co.": "company",
        "& co": "",
    }
    lower = name.lower().strip()
    for abbr, full in replacements.items():
        lower = lower.replace(abbr, full)
    return " ".join(lower.split())


def run(submission: VendorSubmission) -> StageResult:
    issues: list[str] = []
    warnings: list[str] = []
    checks_passed: list[str] = []

    company_norm = _normalize(submission.company_name)
    bank_holder_norm = _normalize(submission.bank_account_holder)

    name_similarity = _token_sort_ratio(company_norm, bank_holder_norm) / 100.0

    if name_similarity >= 0.85:
        checks_passed.append(
            f"Bank account holder '{submission.bank_account_holder}' matches "
            f"company name '{submission.company_name}' (similarity: {name_similarity:.0%})."
        )
    elif name_similarity >= 0.60:
        warnings.append(
            f"Bank account holder '{submission.bank_account_holder}' partially matches "
            f"company name '{submission.company_name}' (similarity: {name_similarity:.0%}). "
            "Verify the account belongs to this entity."
        )
    else:
        issues.append(
            f"Bank account holder '{submission.bank_account_holder}' does NOT match "
            f"company name '{submission.company_name}' (similarity: {name_similarity:.0%}). "
            "This is a strong fraud indicator — the account may belong to a different entity."
        )

    iban_clean = submission.iban.replace(" ", "").upper()
    if len(iban_clean) >= 2:
        iban_country = iban_clean[:2]
        if submission.country in ("US", "IN", "SG"):
            checks_passed.append(
                f"IBAN country check skipped (not standard for {submission.country})."
            )
        elif iban_country != submission.country:
            issues.append(
                f"IBAN country prefix '{iban_country}' does not match "
                f"vendor's stated country '{submission.country}'."
            )
        else:
            checks_passed.append(
                f"IBAN country prefix '{iban_country}' matches stated country."
            )

    if submission.country and submission.address:
        country_lower = submission.country.lower()
        address_lower = submission.address.lower()
        country_names = {
            "DE": "germany", "GB": "united kingdom", "FR": "france",
            "US": "united states", "IN": "india", "IT": "italy",
            "ES": "spain", "NL": "netherlands", "SG": "singapore",
            "AE": "emirates",
        }
        expected_name = country_names.get(submission.country, "")
        if expected_name and expected_name not in address_lower and country_lower not in address_lower:
            warnings.append(
                f"Address '{submission.address}' does not appear to reference "
                f"country '{submission.country}' ({expected_name}). Verify address is correct."
            )
        else:
            checks_passed.append("Address is consistent with stated country.")

    if issues:
        return StageResult(
            stage_key="cross_reference",
            stage_number=3,
            label="Cross-Reference Check",
            status=StageStatus.FAIL,
            reasoning=" | ".join(issues),
            details={"issues": issues, "warnings": warnings, "passed": checks_passed},
        )

    if warnings:
        return StageResult(
            stage_key="cross_reference",
            stage_number=3,
            label="Cross-Reference Check",
            status=StageStatus.WARN,
            reasoning=" | ".join(warnings),
            details={"warnings": warnings, "passed": checks_passed},
        )

    return StageResult(
        stage_key="cross_reference",
        stage_number=3,
        label="Cross-Reference Check",
        status=StageStatus.PASS,
        reasoning=f"All cross-reference checks passed. {' '.join(checks_passed)}",
        details={"passed": checks_passed},
    )
