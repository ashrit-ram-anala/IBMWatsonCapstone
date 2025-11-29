"""Pipeline run model for tracking execution history."""
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.models.base import BaseModel


class PipelineStage(str, enum.Enum):
    INGESTION = "ingestion"
    VALIDATION = "validation"
    CLEANING = "cleaning"
    ANOMALY_DETECTION = "anomaly_detection"
    REVIEW = "review"
    PUBLISHING = "publishing"


class PipelineStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineRun(BaseModel):
    __tablename__ = "pipeline_runs"

    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)

    run_id = Column(String, unique=True, index=True, nullable=False)
    stage = Column(SQLEnum(PipelineStage), nullable=False)
    status = Column(SQLEnum(PipelineStatus), default=PipelineStatus.PENDING, nullable=False)

    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    input_rows = Column(Integer, default=0)
    output_rows = Column(Integer, default=0)
    rows_modified = Column(Integer, default=0)
    rows_removed = Column(Integer, default=0)

    stage_metrics = Column(JSON, nullable=True)

    error_message = Column(String, nullable=True)
    logs = Column(JSON, nullable=True)

    watsonx_node_id = Column(String, nullable=True)
    watsonx_execution_id = Column(String, nullable=True)

    dataset = relationship("Dataset", back_populates="pipeline_runs")

    def __repr__(self):
        return f"<PipelineRun(id={self.run_id}, stage={self.stage}, status={self.status})>"
