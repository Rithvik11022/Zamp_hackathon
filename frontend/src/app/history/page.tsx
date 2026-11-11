"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { listRuns } from "@/lib/api";
import type { PipelineRun } from "@/lib/types";

function decisionBadge(decision: string | null) {
  if (!decision) return <Badge variant="outline">Processing</Badge>;
  const map: Record<string, { variant: "default" | "secondary" | "destructive" | "outline"; label: string }> = {
    approved: { variant: "default", label: "Approved" },
    pending: { variant: "secondary", label: "Pending Review" },
    rejected: { variant: "destructive", label: "Rejected" },
  };
  const info = map[decision] || { variant: "outline" as const, label: decision };
  return <Badge variant={info.variant}>{info.label}</Badge>;
}

export default function HistoryPage() {
  const [runs, setRuns] = useState<PipelineRun[]>([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    listRuns().then(setRuns).catch(console.error);
  }, []);

  const filtered = runs.filter(
    (r) =>
      r.vendor_name.toLowerCase().includes(search.toLowerCase()) ||
      r.country.toLowerCase().includes(search.toLowerCase()) ||
      r.run_id.includes(search)
  );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Run History</h2>
        <p className="text-muted-foreground">All vendor verification runs</p>
      </div>

      <div className="flex items-center gap-4">
        <Input
          placeholder="Search by vendor name, country, or run ID..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-sm"
        />
        <span className="text-sm text-muted-foreground">{filtered.length} runs</span>
      </div>

      <Card>
        <CardContent className="p-0">
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left p-3 text-xs font-medium text-muted-foreground">Run ID</th>
                <th className="text-left p-3 text-xs font-medium text-muted-foreground">Vendor</th>
                <th className="text-left p-3 text-xs font-medium text-muted-foreground">Country</th>
                <th className="text-left p-3 text-xs font-medium text-muted-foreground">Submitted</th>
                <th className="text-left p-3 text-xs font-medium text-muted-foreground">Duration</th>
                <th className="text-left p-3 text-xs font-medium text-muted-foreground">Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-sm text-muted-foreground">
                    {runs.length === 0 ? "No runs yet." : "No matching runs."}
                  </td>
                </tr>
              ) : (
                filtered.map((run) => (
                  <tr key={run.run_id} className="border-b last:border-0 hover:bg-accent/50 transition-colors">
                    <td className="p-3">
                      <Link href={`/run/${run.run_id}`} className="font-mono text-sm text-primary hover:underline">
                        #{run.run_id}
                      </Link>
                    </td>
                    <td className="p-3 text-sm font-medium">{run.vendor_name}</td>
                    <td className="p-3 text-sm">{run.country}</td>
                    <td className="p-3 text-sm text-muted-foreground">
                      {new Date(run.submitted_at).toLocaleString()}
                    </td>
                    <td className="p-3 text-sm text-muted-foreground">
                      {run.duration_ms ? `${(run.duration_ms / 1000).toFixed(1)}s` : "—"}
                    </td>
                    <td className="p-3">{decisionBadge(run.decision)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
