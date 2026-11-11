"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getStats, listRuns } from "@/lib/api";
import type { DashboardStats, PipelineRun } from "@/lib/types";

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

function StatCard({ title, value, color }: { title: string; value: number; color: string }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className={`text-3xl font-bold ${color}`}>{value}</div>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats>({ total: 0, approved: 0, pending: 0, rejected: 0 });
  const [runs, setRuns] = useState<PipelineRun[]>([]);

  useEffect(() => {
    getStats().then(setStats).catch(console.error);
    listRuns().then(setRuns).catch(console.error);
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">Vendor onboarding verification overview</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard title="Total Runs" value={stats.total} color="text-foreground" />
        <StatCard title="Approved" value={stats.approved} color="text-green-600" />
        <StatCard title="Pending Review" value={stats.pending} color="text-yellow-600" />
        <StatCard title="Rejected" value={stats.rejected} color="text-red-600" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Runs</CardTitle>
        </CardHeader>
        <CardContent>
          {runs.length === 0 ? (
            <p className="text-muted-foreground text-sm py-8 text-center">
              No runs yet.{" "}
              <Link href="/submit" className="text-primary underline">
                Submit a vendor
              </Link>{" "}
              to get started.
            </p>
          ) : (
            <div className="space-y-2">
              {runs.slice(0, 10).map((run) => (
                <Link
                  key={run.run_id}
                  href={`/run/${run.run_id}`}
                  className="flex items-center justify-between p-3 rounded-md border hover:bg-accent transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div>
                      <p className="font-medium text-sm">{run.vendor_name}</p>
                      <p className="text-xs text-muted-foreground">
                        {run.country} &middot;{" "}
                        {new Date(run.submitted_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    {run.duration_ms && (
                      <span className="text-xs text-muted-foreground">
                        {(run.duration_ms / 1000).toFixed(1)}s
                      </span>
                    )}
                    {decisionBadge(run.decision)}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
