from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./vendor_db.sqlite"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class RunRecord(Base):
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, unique=True, index=True, nullable=False)
    vendor_name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    submission_json = Column(Text, nullable=False)
    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    decision = Column(String, nullable=True)
    decision_reasoning = Column(Text, default="")
    stages_json = Column(Text, default="[]")
    notification = Column(Text, default="")


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_run(db: Session, run_id: str, submission: dict) -> RunRecord:
    record = RunRecord(
        run_id=run_id,
        vendor_name=submission["company_name"],
        country=submission["country"],
        submission_json=json.dumps(submission),
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_run_stages(db: Session, run_id: str, stages: list[dict]):
    record = db.query(RunRecord).filter(RunRecord.run_id == run_id).first()
    if record:
        record.stages_json = json.dumps(stages)
        db.commit()


def complete_run(
    db: Session,
    run_id: str,
    decision: str,
    reasoning: str,
    notification: str,
    stages: list[dict],
):
    record = db.query(RunRecord).filter(RunRecord.run_id == run_id).first()
    if record:
        record.completed_at = datetime.now(timezone.utc)
        record.decision = decision
        record.decision_reasoning = reasoning
        record.notification = notification
        record.stages_json = json.dumps(stages)
        db.commit()


def get_run(db: Session, run_id: str) -> RunRecord | None:
    return db.query(RunRecord).filter(RunRecord.run_id == run_id).first()


def get_all_runs(db: Session) -> list[RunRecord]:
    return db.query(RunRecord).order_by(RunRecord.submitted_at.desc()).all()


def get_stats(db: Session) -> dict:
    runs = db.query(RunRecord).all()
    total = len(runs)
    approved = sum(1 for r in runs if r.decision == "approved")
    pending = sum(1 for r in runs if r.decision == "pending")
    rejected = sum(1 for r in runs if r.decision == "rejected")
    return {"total": total, "approved": approved, "pending": pending, "rejected": rejected}
