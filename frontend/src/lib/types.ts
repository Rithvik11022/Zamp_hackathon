export type StageStatus = "pending" | "running" | "pass" | "warn" | "fail";

export type Decision = "approved" | "pending" | "rejected";

export interface DocumentInfo {
  filename: string;
  document_type: string;
  content_summary: string;
}

export interface VendorSubmission {
  company_name: string;
  trading_name: string;
  country: string;
  address: string;
  tax_id: string;
  contact_name: string;
  contact_email: string;
  bank_account_holder: string;
  iban: string;
  swift_bic: string;
  documents: DocumentInfo[];
}

export interface StageResult {
  stage_key: string;
  stage_number: number;
  label: string;
  status: StageStatus;
  reasoning: string;
  details: Record<string, unknown>;
  duration_ms: number;
}

export interface PipelineRun {
  run_id: string;
  vendor_name: string;
  country: string;
  submitted_at: string;
  completed_at: string | null;
  decision: Decision | null;
  decision_reasoning: string;
  stages: StageResult[];
  notification: string;
  duration_ms: number | null;
}

export interface DashboardStats {
  total: number;
  approved: number;
  pending: number;
  rejected: number;
}

export interface SampleCase {
  key: string;
  label: string;
  description: string;
  data: VendorSubmission;
}
