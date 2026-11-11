"use client";

import { useCallback, useRef, useState } from "react";
import type { Decision, StageResult } from "@/lib/types";
import { getStreamUrl } from "@/lib/api";

interface PipelineState {
  stages: StageResult[];
  currentStage: { stage_key: string; label: string; stage_number: number; total_stages: number } | null;
  decision: Decision | null;
  reasoning: string;
  notification: string;
  isRunning: boolean;
  isComplete: boolean;
}

const initialState: PipelineState = {
  stages: [],
  currentStage: null,
  decision: null,
  reasoning: "",
  notification: "",
  isRunning: false,
  isComplete: false,
};

export function usePipelineStream() {
  const [state, setState] = useState<PipelineState>(initialState);
  const sourceRef = useRef<EventSource | null>(null);

  const startStream = useCallback((runId: string) => {
    if (sourceRef.current) {
      sourceRef.current.close();
    }

    setState({ ...initialState, isRunning: true });

    const source = new EventSource(getStreamUrl(runId));
    sourceRef.current = source;

    source.addEventListener("stage_start", (e) => {
      const data = JSON.parse(e.data);
      setState((prev) => ({
        ...prev,
        currentStage: data,
      }));
    });

    source.addEventListener("stage_complete", (e) => {
      const data = JSON.parse(e.data) as StageResult;
      setState((prev) => ({
        ...prev,
        stages: [...prev.stages, data],
        currentStage: null,
      }));
    });

    source.addEventListener("pipeline_complete", (e) => {
      const data = JSON.parse(e.data);
      setState((prev) => ({
        ...prev,
        decision: data.decision,
        reasoning: data.reasoning,
        notification: data.notification || "",
        isRunning: false,
        isComplete: true,
        currentStage: null,
      }));
    });

    source.addEventListener("done", () => {
      source.close();
      sourceRef.current = null;
    });

    source.onerror = () => {
      source.close();
      sourceRef.current = null;
      setState((prev) => ({
        ...prev,
        isRunning: false,
      }));
    };
  }, []);

  const reset = useCallback(() => {
    if (sourceRef.current) {
      sourceRef.current.close();
      sourceRef.current = null;
    }
    setState(initialState);
  }, []);

  return { ...state, startStream, reset };
}
