"""Anomaly model for tracking detected anomalies."""
from sqlalchemy import Column, String, Integer, Float, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class AnomalyType(str, enum.Enum):
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
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Anomaly(BaseModel):
    __tablename__ = "anomalies"

    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    transaction_id = Column(String, nullable=True)

    anomaly_type = Column(SQLEnum(AnomalyType), nullable=False)
    severity = Column(SQLEnum(AnomalySeverity), default=AnomalySeverity.MEDIUM, nullable=False)

    confidence_score = Column(Float, nullable=False)
    detected_by = Column(String, nullable=False)

    description = Column(String, nullable=False)
    field_name = Column(String, nullable=True)
    original_value = Column(String, nullable=True)
    expected_value = Column(String, nullable=True)

    context = Column(JSON, nullable=True)

    is_resolved = Column(Integer, default=0, nullable=False)
    resolution_action = Column(String, nullable=True)
    resolved_value = Column(String, nullable=True)

    llm_explanation = Column(String, nullable=True)
    llm_model_id = Column(String, nullable=True)

    dataset = relationship("Dataset", back_populates="anomalies")

    def __repr__(self):
        return f"<Anomaly(type={self.anomaly_type}, severity={self.severity}, confidence={self.confidence_score})>"
