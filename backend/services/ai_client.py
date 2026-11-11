from __future__ import annotations

import json

from config import settings
from models import VendorSubmission

_anthropic_client = None
_gemini_client = None


def _get_anthropic():
    global _anthropic_client
    if _anthropic_client is None:
        from anthropic import Anthropic
        _anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
    return _anthropic_client


def _get_gemini():
    global _gemini_client
    if _gemini_client is None:
        from google import genai
        _gemini_client = genai.Client(api_key=settings.gemini_api_key)
    return _gemini_client


def _call_llm(prompt: str) -> str:
    provider = settings.ai_provider

    if provider == "gemini":
        client = _get_gemini()
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
        )
        return response.text

    if provider == "anthropic":
        client = _get_anthropic()
        response = client.messages.create(
            model=settings.ai_model_fast,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    raise RuntimeError("no_api_key")


def _parse_json_response(text: str) -> dict | None:
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    return None


async def analyze_documents(submission: VendorSubmission) -> dict:
    if not submission.documents:
        return {"findings": [], "warnings": [], "issues": ["No documents submitted for analysis."]}

    doc_descriptions = []
    for doc in submission.documents:
        desc = f"- Filename: '{doc.filename}'"
        if doc.document_type:
            desc += f", Claimed type: '{doc.document_type}'"
        if doc.content_summary:
            desc += f", Content: '{doc.content_summary}'"
        doc_descriptions.append(desc)

    prompt = f"""You are a vendor compliance analyst reviewing documents submitted as part of a vendor onboarding process.

VENDOR DETAILS:
- Company Name: {submission.company_name}
- Trading Name: {submission.trading_name or 'N/A'}
- Country: {submission.country}
- Tax ID: {submission.tax_id}
- Contact: {submission.contact_name} ({submission.contact_email})

SUBMITTED DOCUMENTS:
{chr(10).join(doc_descriptions)}

ANALYSIS TASKS:
1. For each document, determine if the document type matches what was claimed. For example, if a document is claimed to be a "Certificate of Incorporation" but its content describes an invoice, flag this as a document type mismatch.
2. Check if the documents are consistent with the vendor details (company name on documents should match the submission).
3. Identify any red flags (expired documents, missing signatures, suspicious content).
4. Check if the required documents are present: Certificate of Incorporation and Tax Registration are mandatory.

Respond with a JSON object:
{{
    "findings": ["List of positive observations"],
    "warnings": ["List of non-critical concerns"],
    "issues": ["List of critical problems that should block approval"]
}}

Be specific and cite document filenames in your analysis. If a document type doesn't match its content, that is a CRITICAL issue."""

    try:
        text = _call_llm(prompt)
        parsed = _parse_json_response(text)
        if parsed:
            return parsed
        return {
            "findings": ["AI analysis completed but response format was unexpected."],
            "warnings": ["Manual review recommended."],
            "issues": [],
        }
    except Exception:
        return _fallback_analysis(submission)


def _fallback_analysis(submission: VendorSubmission) -> dict:
    findings = []
    warnings = []
    issues = []

    for doc in submission.documents:
        claimed = doc.document_type.lower()
        content = doc.content_summary.lower()

        if claimed and content:
            mismatch_signals = {
                "certificate_of_incorporation": ["invoice", "receipt", "payment", "quote", "proposal"],
                "tax_registration": ["invoice", "receipt", "payment", "quote", "proposal"],
                "bank_letter": ["invoice", "receipt", "incorporation", "tax"],
            }

            claimed_key = claimed.replace(" ", "_")
            bad_signals = mismatch_signals.get(claimed_key, [])
            for signal in bad_signals:
                if signal in content:
                    issues.append(
                        f"Document '{doc.filename}' is claimed as '{doc.document_type}' "
                        f"but content appears to be a {signal}. "
                        f"Document classification mismatch detected with high confidence."
                    )
                    break
            else:
                findings.append(
                    f"Document '{doc.filename}' ({doc.document_type}) — content consistent with claimed type."
                )
        elif not content:
            warnings.append(
                f"Document '{doc.filename}' has no content summary available for analysis."
            )

    if not issues and not warnings:
        findings.append("All documents appear consistent with vendor submission details.")

    return {"findings": findings, "warnings": warnings, "issues": issues}


async def generate_notification(
    vendor_name: str,
    contact_name: str,
    contact_email: str,
    decision: str,
    stage_results: list[dict],
) -> str:
    issues_summary = []
    for stage in stage_results:
        if stage.get("status") in ("fail", "warn"):
            issues_summary.append(f"- [{stage['label']}]: {stage['reasoning']}")

    if not issues_summary:
        return ""

    prompt = f"""Generate a professional vendor onboarding notification email.

VENDOR: {vendor_name}
CONTACT: {contact_name} ({contact_email})
DECISION: {decision.upper()}

ISSUES FOUND:
{chr(10).join(issues_summary)}

Write a clear, professional email that:
1. States the decision
2. Lists each issue with specific guidance on how to resolve it
3. Provides a deadline (5 business days) for resubmission if applicable
4. Is professional but direct — no filler

Start with "Subject:" line, then the body. Keep it concise."""

    try:
        return _call_llm(prompt)
    except Exception:
        return _fallback_notification(vendor_name, contact_name, decision, issues_summary)


def _fallback_notification(
    vendor_name: str,
    contact_name: str,
    decision: str,
    issues: list[str],
) -> str:
    status_text = "Additional Information Required" if decision == "pending" else "Submission Not Approved"
    lines = [
        f"Subject: Action Required: Vendor Onboarding — {vendor_name}",
        "",
        f"Dear {contact_name},",
        "",
        f"Your vendor registration submission for {vendor_name} has been reviewed.",
        f"Status: {decision.upper()} — {status_text}",
        "",
        "The following items require your attention:",
        "",
    ]
    for issue in issues:
        lines.append(issue)
    lines.extend([
        "",
        "Please resubmit the corrected information within 5 business days.",
        "",
        "Regards,",
        "Vendor Management Team",
    ])
    return "\n".join(lines)
