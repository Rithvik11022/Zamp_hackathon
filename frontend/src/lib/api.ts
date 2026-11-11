const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9000";

export async function submitVendor(data: Record<string, unknown>) {
  const res = await fetch(`${API_BASE}/api/vendors/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function getRun(runId: string) {
  const res = await fetch(`${API_BASE}/api/vendors/runs/${runId}`);
  return res.json();
}

export async function listRuns() {
  const res = await fetch(`${API_BASE}/api/vendors/runs`);
  return res.json();
}

export async function getStats() {
  const res = await fetch(`${API_BASE}/api/vendors/stats`);
  return res.json();
}

export async function getSamples() {
  const res = await fetch(`${API_BASE}/api/vendors/samples`);
  return res.json();
}

export function getStreamUrl(runId: string) {
  return `${API_BASE}/api/vendors/runs/${runId}/stream`;
}
