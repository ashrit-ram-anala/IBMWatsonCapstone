"""Pipeline run model for tracking execution history."""
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.models.base import BaseModel


class PipelineStage(str, enum.Enum):
    """Pipeline execution stages."""
    INGESTION = "ingestion"
    VALIDATION = "validation"
    CLEANING = "cleaning"
    ANOMALY_DETECTION = "anomaly_detection"
    REVIEW = "review"
    PUBLISHING = "publishing"


class PipelineStatus(str, enum.Enum):
    """Pipeline run status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineRun(BaseModel):
    """Model for tracking individual pipeline executions."""

    __tablename__ = "pipeline_runs"

    # Foreign key to dataset
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)

    # Run identification
    run_id = Column(String, unique=True, index=True, nullable=False)
    stage = Column(SQLEnum(PipelineStage), nullable=False)
    status = Column(SQLEnum(PipelineStatus), default=PipelineStatus.PENDING, nullable=False)

    # Timing
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Metrics for this stage
    input_rows = Column(Integer, default=0)
    output_rows = Column(Integer, default=0)
    rows_modified = Column(Integer, default=0)
    rows_removed = Column(Integer, default=0)

    # Stage-specific metrics
    stage_metrics = Column(JSON, nullable=True)

    # Errors and logs
    error_message = Column(String, nullable=True)
    logs = Column(JSON, nullable=True)

    # Watsonx node information
    watsonx_node_id = Column(String, nullable=True)
    watsonx_execution_id = Column(String, nullable=True)

    # Relationships
    dataset = relationship("Dataset", back_populates="pipeline_runs")

    def __repr__(self):
        return f"<PipelineRun(id={self.run_id}, stage={self.stage}, status={self.status})>"
