"""Dataset model for tracking uploaded datasets."""
from sqlalchemy import Column, String, Integer, Float, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class DatasetStatus(str, enum.Enum):
    """Dataset processing status."""
    UPLOADED = "uploaded"
    VALIDATING = "validating"
    CLEANING = "cleaning"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class Dataset(BaseModel):
    """Model for tracking datasets through the pipeline."""

    __tablename__ = "datasets"

    name = Column(String, nullable=False)
    source_type = Column(String, nullable=False)  # csv, sql, api
    file_path = Column(String, nullable=True)
    status = Column(SQLEnum(DatasetStatus), default=DatasetStatus.UPLOADED, nullable=False)

    # Metrics
    total_rows = Column(Integer, default=0)
    valid_rows = Column(Integer, default=0)
    invalid_rows = Column(Integer, default=0)
    cleaned_rows = Column(Integer, default=0)
    anomaly_count = Column(Integer, default=0)

    # Quality Score
    quality_score = Column(Float, default=0.0)

    # Processing info
    processing_time_seconds = Column(Float, nullable=True)
    error_message = Column(String, nullable=True)

    # Configuration used
    pipeline_config = Column(JSON, nullable=True)

    # Relationships
    transactions = relationship("Transaction", back_populates="dataset", cascade="all, delete-orphan")
    pipeline_runs = relationship("PipelineRun", back_populates="dataset", cascade="all, delete-orphan")
    anomalies = relationship("Anomaly", back_populates="dataset", cascade="all, delete-orphan")
    metadata = relationship("DatasetMetadata", back_populates="dataset", uselist=False, cascade="all, delete-orphan")
