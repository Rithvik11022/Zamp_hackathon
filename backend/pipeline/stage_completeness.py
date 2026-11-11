from __future__ import annotations

from models import StageResult, StageStatus, VendorSubmission

REQUIRED_FIELDS = [
    ("company_name", "Company Name"),
    ("country", "Country"),
    ("address", "Address"),
    ("tax_id", "Tax ID"),
    ("contact_name", "Contact Name"),
    ("contact_email", "Contact Email"),
    ("bank_account_holder", "Bank Account Holder Name"),
    ("iban", "IBAN / Account Number"),
]

RECOMMENDED_FIELDS = [
    ("trading_name", "Trading Name"),
    ("swift_bic", "SWIFT/BIC Code"),
]

REQUIRED_DOCUMENTS = [
    "certificate_of_incorporation",
    "tax_registration",
]


def run(submission: VendorSubmission) -> StageResult:
    missing_required: list[str] = []
    missing_recommended: list[str] = []
    doc_issues: list[str] = []

    for field_key, field_label in REQUIRED_FIELDS:
        value = getattr(submission, field_key, "")
        if not value or not value.strip():
            missing_required.append(field_label)

    for field_key, field_label in RECOMMENDED_FIELDS:
        value = getattr(submission, field_key, "")
        if not value or not value.strip():
            missing_recommended.append(field_label)

    submitted_doc_types = {
        d.document_type.lower().replace(" ", "_") for d in submission.documents
    }
    for req_doc in REQUIRED_DOCUMENTS:
        if req_doc not in submitted_doc_types:
            doc_issues.append(req_doc.replace("_", " ").title())

    if missing_required or doc_issues:
        parts = []
        if missing_required:
            parts.append(f"Missing required fields: {', '.join(missing_required)}.")
        if doc_issues:
            parts.append(f"Missing required documents: {', '.join(doc_issues)}.")
        return StageResult(
            stage_key="completeness",
            stage_number=1,
            label="Completeness Check",
            status=StageStatus.FAIL,
            reasoning=" ".join(parts),
            details={
                "missing_required": missing_required,
                "missing_documents": doc_issues,
            },
        )

    if missing_recommended:
        return StageResult(
            stage_key="completeness",
            stage_number=1,
            label="Completeness Check",
            status=StageStatus.WARN,
            reasoning=f"All required fields present. Missing recommended fields: {', '.join(missing_recommended)}. {len(submission.documents)} document(s) attached.",
            details={
                "missing_recommended": missing_recommended,
                "fields_present": len(REQUIRED_FIELDS),
                "documents_attached": len(submission.documents),
            },
        )

    return StageResult(
        stage_key="completeness",
        stage_number=1,
        label="Completeness Check",
        status=StageStatus.PASS,
        reasoning=f"All {len(REQUIRED_FIELDS)} required fields present. {len(submission.documents)} document(s) attached.",
        details={
            "fields_present": len(REQUIRED_FIELDS),
            "documents_attached": len(submission.documents),
        },
    )
