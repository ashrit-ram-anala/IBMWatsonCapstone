"""Anomaly model for tracking detected anomalies."""
from sqlalchemy import Column, String, Integer, Float, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class AnomalyType(str, enum.Enum):
    """Types of detected anomalies."""
    NEGATIVE_BALANCE = "negative_balance"
    DUPLICATE_TRANSACTION = "duplicate_transaction"
    INVALID_DATE = "invalid_date"
    SUSPICIOUS_AMOUNT = "suspicious_amount"
    STATUS_MISMATCH = "status_mismatch"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_FORMAT = "invalid_format"
    OUTLIER = "outlier"
    SEMANTIC_INCONSISTENCY = "semantic_inconsistency"
    OTHER = "other"


class AnomalySeverity(str, enum.Enum):
    """Severity levels for anomalies."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Anomaly(BaseModel):
    """Model for tracking detected anomalies in datasets."""

    __tablename__ = "anomalies"

    # Foreign keys
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    transaction_id = Column(String, nullable=True)  # Reference to transaction if applicable

    # Anomaly classification
    anomaly_type = Column(SQLEnum(AnomalyType), nullable=False)
    severity = Column(SQLEnum(AnomalySeverity), default=AnomalySeverity.MEDIUM, nullable=False)

    # Detection details
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0
    detected_by = Column(String, nullable=False)  # watsonx, rule-based, ml-model

    # Description and context
    description = Column(String, nullable=False)
    field_name = Column(String, nullable=True)  # Field where anomaly was detected
    original_value = Column(String, nullable=True)
    expected_value = Column(String, nullable=True)

    # Additional context
    context = Column(JSON, nullable=True)  # Additional anomaly-specific data

    # Resolution
    is_resolved = Column(Integer, default=0, nullable=False)  # Boolean as int: 0=false, 1=true
    resolution_action = Column(String, nullable=True)  # corrected, removed, ignored
    resolved_value = Column(String, nullable=True)

    # LLM detection details
    llm_explanation = Column(String, nullable=True)  # Explanation from Watsonx
    llm_model_id = Column(String, nullable=True)

    # Relationships
    dataset = relationship("Dataset", back_populates="anomalies")

    def __repr__(self):
        return f"<Anomaly(type={self.anomaly_type}, severity={self.severity}, confidence={self.confidence_score})>"
