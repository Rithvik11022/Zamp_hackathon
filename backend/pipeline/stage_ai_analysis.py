from __future__ import annotations

import json

from models import StageResult, StageStatus, VendorSubmission
from services.ai_client import analyze_documents


EXPECTED_DOCUMENTS = {
    "certificate_of_incorporation": "A legal document proving the company is registered and incorporated. Contains company name, registration number, date of incorporation, and jurisdiction.",
    "tax_registration": "A tax registration certificate or tax compliance document. Contains tax identification number, registered tax authority, and validity period.",
    "w9": "IRS Form W-9 (Request for Taxpayer Identification Number). For US vendors only.",
    "w8": "IRS Form W-8 (Certificate of Foreign Status). For non-US vendors doing business with US companies.",
    "bank_letter": "A bank confirmation letter verifying account details. Contains bank name, account holder, and account number.",
}


async def run(submission: VendorSubmission) -> StageResult:
    if not submission.documents:
        return StageResult(
            stage_key="ai_document_analysis",
            stage_number=6,
            label="AI Document Analysis",
            status=StageStatus.FAIL,
            reasoning="No documents submitted for analysis.",
            details={},
        )

    try:
        analysis = await analyze_documents(submission)
    except Exception as e:
        return StageResult(
            stage_key="ai_document_analysis",
            stage_number=6,
            label="AI Document Analysis",
            status=StageStatus.WARN,
            reasoning=f"AI analysis could not be completed: {str(e)}. Manual document review required.",
            details={"error": str(e)},
        )

    issues = analysis.get("issues", [])
    warnings = analysis.get("warnings", [])
    findings = analysis.get("findings", [])

    if issues:
        return StageResult(
            stage_key="ai_document_analysis",
            stage_number=6,
            label="AI Document Analysis",
            status=StageStatus.FAIL,
            reasoning=" | ".join(issues),
            details={
                "issues": issues,
                "warnings": warnings,
                "findings": findings,
                "documents_analyzed": len(submission.documents),
            },
        )

    if warnings:
        return StageResult(
            stage_key="ai_document_analysis",
            stage_number=6,
            label="AI Document Analysis",
            status=StageStatus.WARN,
            reasoning=" | ".join(warnings),
            details={
                "warnings": warnings,
                "findings": findings,
                "documents_analyzed": len(submission.documents),
            },
        )

    return StageResult(
        stage_key="ai_document_analysis",
        stage_number=6,
        label="AI Document Analysis",
        status=StageStatus.PASS,
        reasoning=f"All {len(submission.documents)} document(s) analyzed. {' '.join(findings)}",
        details={
            "findings": findings,
            "documents_analyzed": len(submission.documents),
        },
    )
