from __future__ import annotations

import enum
from datetime import datetime
from pydantic import BaseModel, Field


class StageStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class Decision(str, enum.Enum):
    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"


class DocumentInfo(BaseModel):
    filename: str
    document_type: str = ""
    content_summary: str = ""


class VendorSubmission(BaseModel):
    company_name: str
    trading_name: str = ""
    country: str
    address: str
    tax_id: str
    contact_name: str
    contact_email: str
    bank_account_holder: str
    iban: str
    swift_bic: str = ""
    documents: list[DocumentInfo] = Field(default_factory=list)


class StageResult(BaseModel):
    stage_key: str
    stage_number: int
    label: str
    status: StageStatus
    reasoning: str
    details: dict = Field(default_factory=dict)
    duration_ms: int = 0


class PipelineRun(BaseModel):
    run_id: str
    vendor_name: str
    country: str
    submitted_at: datetime
    completed_at: datetime | None = None
    decision: Decision | None = None
    decision_reasoning: str = ""
    stages: list[StageResult] = Field(default_factory=list)
    notification: str = ""


class SSEEvent(BaseModel):
    event: str
    data: dict


class RunSummary(BaseModel):
    run_id: str
    vendor_name: str
    country: str
    submitted_at: datetime
    completed_at: datetime | None = None
    decision: Decision | None = None
    duration_ms: int | None = None


class DashboardStats(BaseModel):
    total: int = 0
    approved: int = 0
    pending: int = 0
    rejected: int = 0
