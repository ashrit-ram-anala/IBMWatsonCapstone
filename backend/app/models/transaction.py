"""Transaction model for banking transaction data."""
from sqlalchemy import Column, String, Numeric, DateTime, Boolean, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from decimal import Decimal

from app.models.base import BaseModel


class Transaction(BaseModel):
    """Model for individual banking transactions."""

    __tablename__ = "transactions"

    # Foreign key to dataset
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)

    # Core transaction fields
    transaction_id = Column(String, unique=True, index=True, nullable=False)
    customer_id = Column(String, index=True, nullable=False)
    account_number = Column(String, nullable=True)

    # Financial details
    amount = Column(Numeric(precision=15, scale=2), nullable=False)
    balance = Column(Numeric(precision=15, scale=2), nullable=True)
    currency = Column(String(3), default="USD", nullable=False)

    # Transaction metadata
    transaction_date = Column(DateTime, nullable=False)
    transaction_type = Column(String, nullable=True)  # deposit, withdrawal, transfer, payment
    status = Column(String, nullable=False)  # completed, pending, failed, cancelled
    description = Column(String, nullable=True)
    merchant = Column(String, nullable=True)
    category = Column(String, nullable=True)

    # Validation flags
    is_valid = Column(Boolean, default=True, nullable=False)
    is_anomaly = Column(Boolean, default=False, nullable=False)
    was_cleaned = Column(Boolean, default=False, nullable=False)

    # Cleaning metadata
    original_values = Column(JSON, nullable=True)  # Store original values before cleaning
    cleaning_actions = Column(JSON, nullable=True)  # List of cleaning actions applied
    validation_errors = Column(JSON, nullable=True)  # Validation errors found

    # Geographic info
    location = Column(String, nullable=True)
    country_code = Column(String(2), nullable=True)

    # Relationships
    dataset = relationship("Dataset", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction(id={self.transaction_id}, customer={self.customer_id}, amount={self.amount})>"
