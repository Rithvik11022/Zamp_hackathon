from __future__ import annotations

import re

from models import StageResult, StageStatus, VendorSubmission

TAX_FORMATS: dict[str, tuple[str, str]] = {
    "US": (r"^\d{2}-\d{7}$", "XX-XXXXXXX (EIN)"),
    "IN": (r"^\d{2}[A-Z]{5}\d{4}[A-Z]\d[A-Z][A-Z\d]$", "15-character GSTIN (e.g. 22AAAAA0000A1Z5)"),
    "DE": (r"^DE\d{9}$", "DE followed by 9 digits (e.g. DE123456789)"),
    "GB": (r"^GB\d{9}$", "GB followed by 9 digits (e.g. GB123456789)"),
    "FR": (r"^FR[A-Z0-9]{2}\d{9}$", "FR + 2 chars + 9 digits (e.g. FRXX123456789)"),
    "IT": (r"^IT\d{11}$", "IT followed by 11 digits"),
    "ES": (r"^ES[A-Z0-9]\d{7}[A-Z0-9]$", "ES + alphanumeric + 7 digits + alphanumeric"),
    "NL": (r"^NL\d{9}B\d{2}$", "NL + 9 digits + B + 2 digits"),
    "SG": (r"^\d{9}[A-Z]$", "9 digits + letter (UEN)"),
    "AE": (r"^\d{15}$", "15-digit TRN"),
}

IBAN_LENGTHS: dict[str, int] = {
    "DE": 22, "GB": 22, "FR": 27, "IT": 27, "ES": 24, "NL": 18,
    "BE": 16, "AT": 20, "CH": 21, "SE": 24, "NO": 15, "DK": 18,
    "FI": 18, "PT": 25, "IE": 22, "LU": 20, "AE": 23, "SA": 24,
    "IN": 0, "US": 0, "SG": 0,
}


def _validate_tax_id(tax_id: str, country: str) -> tuple[bool, str]:
    if country not in TAX_FORMATS:
        return True, f"No specific format rule for country '{country}'. Tax ID accepted as-is."

    pattern, expected_format = TAX_FORMATS[country]
    if re.match(pattern, tax_id.strip()):
        return True, f"Tax ID '{tax_id}' matches expected format for {country} ({expected_format})."
    return False, (
        f"Tax ID '{tax_id}' does not match expected format for {country}. "
        f"Expected: {expected_format}."
    )


def _validate_iban(iban: str, country: str) -> tuple[bool, str]:
    cleaned = iban.replace(" ", "").upper()

    if country in ("US", "IN", "SG"):
        if len(cleaned) > 0:
            return True, f"Account number accepted (IBAN not standard for {country})."
        return False, "Bank account number is empty."

    if len(cleaned) < 4:
        return False, f"IBAN '{iban}' is too short."

    iban_country = cleaned[:2]
    expected_len = IBAN_LENGTHS.get(iban_country)
    if expected_len and len(cleaned) != expected_len:
        return False, (
            f"IBAN '{iban}' has {len(cleaned)} characters but "
            f"{iban_country} IBANs should have {expected_len}."
        )

    if iban_country != country:
        return False, (
            f"IBAN country prefix '{iban_country}' does not match "
            f"vendor's stated country '{country}'."
        )

    return True, f"IBAN structure valid ({len(cleaned)} characters, prefix matches country)."


def _validate_email(email: str) -> tuple[bool, str]:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if re.match(pattern, email.strip()):
        return True, f"Email '{email}' format is valid."
    return False, f"Email '{email}' has an invalid format."


def run(submission: VendorSubmission) -> StageResult:
    issues: list[str] = []
    warnings: list[str] = []
    checks_passed: list[str] = []

    tax_ok, tax_msg = _validate_tax_id(submission.tax_id, submission.country)
    if tax_ok:
        checks_passed.append(tax_msg)
    else:
        issues.append(tax_msg)

    iban_ok, iban_msg = _validate_iban(submission.iban, submission.country)
    if iban_ok:
        checks_passed.append(iban_msg)
    else:
        issues.append(iban_msg)

    email_ok, email_msg = _validate_email(submission.contact_email)
    if email_ok:
        checks_passed.append(email_msg)
    else:
        issues.append(email_msg)

    if issues:
        return StageResult(
            stage_key="format_validation",
            stage_number=2,
            label="Format Validation",
            status=StageStatus.FAIL,
            reasoning=" | ".join(issues),
            details={"issues": issues, "passed": checks_passed},
        )

    if warnings:
        return StageResult(
            stage_key="format_validation",
            stage_number=2,
            label="Format Validation",
            status=StageStatus.WARN,
            reasoning=" | ".join(warnings),
            details={"warnings": warnings, "passed": checks_passed},
        )

    return StageResult(
        stage_key="format_validation",
        stage_number=2,
        label="Format Validation",
        status=StageStatus.PASS,
        reasoning=f"All format checks passed. {' '.join(checks_passed)}",
        details={"passed": checks_passed},
    )
