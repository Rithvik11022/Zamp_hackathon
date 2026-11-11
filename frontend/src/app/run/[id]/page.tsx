"use client";

import { Suspense, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { usePipelineStream } from "@/hooks/use-pipeline-stream";
import { getRun } from "@/lib/api";
import type { StageResult, PipelineRun, Decision } from "@/lib/types";

const STAGE_LABELS: Record<string, string> = {
  completeness: "Completeness Check",
  format_validation: "Format Validation",
  cross_reference: "Cross-Reference Check",
  duplicate_detection: "Duplicate Detection",
  sanctions_screening: "Sanctions Screening",
  ai_document_analysis: "AI Document Analysis",
};

const ALL_STAGES = [
  "completeness",
  "format_validation",
  "cross_reference",
  "duplicate_detection",
  "sanctions_screening",
  "ai_document_analysis",
];

function StatusIcon({ status }: { status: string }) {
  if (status === "pass")
    return (
      <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
        <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" strokeWidth={3} viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      </div>
    );
  if (status === "warn")
    return (
      <div className="w-8 h-8 rounded-full bg-yellow-100 flex items-center justify-center">
        <svg className="w-4 h-4 text-yellow-600" fill="none" stroke="currentColor" strokeWidth={3} viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M12 3l9.5 16.5H2.5L12 3z" />
        </svg>
      </div>
    );
  if (status === "fail")
    return (
      <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center">
        <svg className="w-4 h-4 text-red-600" fill="none" stroke="currentColor" strokeWidth={3} viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </div>
    );
  if (status === "running")
    return (
      <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
        <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  return (
    <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
      <div className="w-3 h-3 rounded-full bg-muted-foreground/30" />
    </div>
  );
}

function StageCard({ stage, isRunning }: { stage: StageResult | null; isRunning: boolean }) {
  if (!stage) return null;
  return (
    <div className="ml-4 mt-1 text-sm text-muted-foreground animate-in fade-in slide-in-from-top-1 duration-300">
      <p>{stage.reasoning}</p>
      {stage.duration_ms > 0 && (
        <p className="text-xs mt-1 text-muted-foreground/70">{(stage.duration_ms / 1000).toFixed(1)}s</p>
      )}
    </div>
  );
}

function DecisionBanner({ decision, reasoning }: { decision: Decision; reasoning: string }) {
  const config = {
    approved: { bg: "bg-green-50 border-green-200", text: "text-green-800", label: "APPROVED" },
    pending: { bg: "bg-yellow-50 border-yellow-200", text: "text-yellow-800", label: "PENDING — HUMAN REVIEW REQUIRED" },
    rejected: { bg: "bg-red-50 border-red-200", text: "text-red-800", label: "REJECTED" },
  };
  const c = config[decision];
  return (
    <div className={`rounded-lg border-2 p-6 ${c.bg} animate-in fade-in duration-500`}>
      <h3 className={`text-lg font-bold ${c.text}`}>{c.label}</h3>
      <p className={`mt-2 text-sm ${c.text}/80`}>{reasoning}</p>
    </div>
  );
}

export default function RunPage() {
  return (
    <Suspense fallback={<div className="text-muted-foreground p-8 text-center">Loading run...</div>}>
      <RunPageInner />
    </Suspense>
  );
}

function RunPageInner() {
  const params = useParams();
  const runId = params.id as string;
  const stream = usePipelineStream();
  const [existingRun, setExistingRun] = useState<PipelineRun | null>(null);
  const [started, setStarted] = useState(false);

  useEffect(() => {
    getRun(runId).then((data) => {
      if (data.decision) {
        setExistingRun(data);
      } else {
        stream.startStream(runId);
        setStarted(true);
      }
    }).catch(() => {
      stream.startStream(runId);
      setStarted(true);
    });
  }, [runId]);

  const completedStages = existingRun ? existingRun.stages : stream.stages;
  const currentStageKey = stream.currentStage?.stage_key;
  const decision = existingRun?.decision || stream.decision;
  const reasoning = existingRun?.decision_reasoning || stream.reasoning;
  const notification = existingRun?.notification || stream.notification;
  const isRunning = stream.isRunning;

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">
            Verification Run
            <span className="text-muted-foreground font-mono text-base ml-2">#{runId}</span>
          </h2>
          <p className="text-muted-foreground">
            {existingRun ? existingRun.vendor_name : "Processing vendor submission..."}
          </p>
        </div>
        <Link href="/">
          <Button variant="outline" size="sm">Back to Dashboard</Button>
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            Validation Pipeline
            {isRunning && <Badge variant="outline" className="animate-pulse">Live</Badge>}
            {decision && !isRunning && <Badge variant="secondary">Complete</Badge>}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {ALL_STAGES.map((stageKey, i) => {
            const completed = completedStages.find((s) => s.stage_key === stageKey);
            const isCurrent = currentStageKey === stageKey;
            const isPending = !completed && !isCurrent;

            let status = "pending";
            if (completed) status = completed.status;
            else if (isCurrent) status = "running";

            return (
              <div key={stageKey} className="flex gap-3">
                <div className="flex flex-col items-center">
                  <StatusIcon status={status} />
                  {i < ALL_STAGES.length - 1 && (
                    <div className={`w-0.5 flex-1 mt-1 ${completed ? "bg-border" : "bg-muted"}`} />
                  )}
                </div>
                <div className="flex-1 pb-4">
                  <div className="flex items-center gap-2">
                    <span className={`text-sm font-medium ${isPending ? "text-muted-foreground" : ""}`}>
                      {STAGE_LABELS[stageKey] || stageKey}
                    </span>
                    <span className="text-xs text-muted-foreground">Stage {i + 1}/6</span>
                  </div>
                  {completed && <StageCard stage={completed} isRunning={false} />}
                  {isCurrent && (
                    <div className="ml-4 mt-1 text-sm text-blue-600 animate-pulse">
                      Analyzing...
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </CardContent>
      </Card>

      {decision && reasoning && (
        <DecisionBanner decision={decision as Decision} reasoning={reasoning} />
      )}

      {notification && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Generated Notification</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-sm whitespace-pre-wrap font-mono bg-muted p-4 rounded-md">{notification}</pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
