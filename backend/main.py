from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from config import settings
from database import (
    SessionLocal, init_db, save_run, update_run_stages,
    complete_run, get_run, get_all_runs, get_stats, RunRecord,
)
from models import VendorSubmission, Decision
from pipeline.runner import run_pipeline
from services.ai_client import generate_notification


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Vendor Onboarding Automation", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/api/vendors/submit")
async def submit_vendor(submission: VendorSubmission, db: Session = Depends(get_db)):
    run_id = str(uuid.uuid4())[:8]
    save_run(db, run_id, submission.model_dump())
    return {"run_id": run_id, "status": "submitted"}


@app.get("/api/vendors/runs/{run_id}/stream")
async def stream_pipeline(run_id: str, db: Session = Depends(get_db)):
    record = get_run(db, run_id)
    if not record:
        return {"error": "Run not found"}

    submission_data = json.loads(record.submission_json)
    submission = VendorSubmission(**submission_data)

    async def event_generator():
        stages_so_far = []

        async for event in run_pipeline(submission):
            event_type = event["event"]
            data = event["data"]

            if event_type == "stage_complete":
                stages_so_far.append(data)
                update_run_stages(db, run_id, stages_so_far)

            if event_type == "pipeline_complete":
                decision = data["decision"]
                reasoning = data["reasoning"]
                stages = data["stages"]

                notification = ""
                if decision != "approved":
                    notification = await generate_notification(
                        vendor_name=submission.company_name,
                        contact_name=submission.contact_name,
                        contact_email=submission.contact_email,
                        decision=decision,
                        stage_results=stages,
                    )

                complete_run(db, run_id, decision, reasoning, notification, stages)
                data["notification"] = notification

            yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/vendors/runs/{run_id}")
async def get_run_details(run_id: str, db: Session = Depends(get_db)):
    record = get_run(db, run_id)
    if not record:
        return {"error": "Run not found"}
    return _format_run(record)


@app.get("/api/vendors/runs")
async def list_runs(db: Session = Depends(get_db)):
    records = get_all_runs(db)
    return [_format_run(r) for r in records]


@app.get("/api/vendors/stats")
async def dashboard_stats(db: Session = Depends(get_db)):
    return get_stats(db)


@app.get("/api/vendors/samples")
async def list_samples():
    import os
    samples_dir = os.path.join(os.path.dirname(__file__), "data", "sample_submissions")
    if not os.path.exists(samples_dir):
        return []
    samples = []
    for f in sorted(os.listdir(samples_dir)):
        if f.endswith(".json"):
            path = os.path.join(samples_dir, f)
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            samples.append({
                "key": f.replace(".json", ""),
                "label": data.get("_label", f.replace(".json", "").replace("_", " ").title()),
                "description": data.get("_description", ""),
                "data": {k: v for k, v in data.items() if not k.startswith("_")},
            })
    return samples


def _format_run(record: RunRecord) -> dict:
    stages = json.loads(record.stages_json) if record.stages_json else []
    duration_ms = None
    if record.completed_at and record.submitted_at:
        delta = record.completed_at - record.submitted_at
        duration_ms = int(delta.total_seconds() * 1000)
    return {
        "run_id": record.run_id,
        "vendor_name": record.vendor_name,
        "country": record.country,
        "submitted_at": record.submitted_at.isoformat() if record.submitted_at else None,
        "completed_at": record.completed_at.isoformat() if record.completed_at else None,
        "decision": record.decision,
        "decision_reasoning": record.decision_reasoning,
        "stages": stages,
        "notification": record.notification,
        "duration_ms": duration_ms,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
