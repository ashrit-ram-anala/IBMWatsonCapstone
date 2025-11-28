"""Dataset metadata model for storing processing statistics."""
from sqlalchemy import Column, String, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class DatasetMetadata(BaseModel):
    """Model for storing dataset metadata and statistics."""

    __tablename__ = "dataset_metadata"

    # Foreign key to dataset (one-to-one relationship)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Schema information
    columns = Column(JSON, nullable=True)  # List of column names and types
    column_count = Column(Integer, default=0)

    # Data quality metrics
    completeness_score = Column(Float, default=0.0)  # % of non-null values
    validity_score = Column(Float, default=0.0)  # % of valid values
    consistency_score = Column(Float, default=0.0)  # % of consistent values
    accuracy_score = Column(Float, default=0.0)  # % of accurate values

    # Null statistics per column
    null_counts = Column(JSON, nullable=True)  # {column: null_count}
    null_percentages = Column(JSON, nullable=True)  # {column: null_percentage}

    # Data type statistics
    data_types = Column(JSON, nullable=True)  # {column: inferred_type}
    type_violations = Column(JSON, nullable=True)  # {column: violation_count}

    # Value distributions
    unique_counts = Column(JSON, nullable=True)  # {column: unique_value_count}
    value_distributions = Column(JSON, nullable=True)  # Top values per column

    # Numeric statistics
    numeric_stats = Column(JSON, nullable=True)  # {column: {min, max, mean, median, std}}

    # Date/time statistics
    date_range = Column(JSON, nullable=True)  # {column: {min_date, max_date}}

    # Cleaning operations performed
    cleaning_summary = Column(JSON, nullable=True)  # List of cleaning operations

    # Transformation log
    transformations = Column(JSON, nullable=True)  # Detailed transformation log

    # File information
    file_size_bytes = Column(Integer, nullable=True)
    file_format = Column(String, nullable=True)
    encoding = Column(String, nullable=True)

    # Relationships
    dataset = relationship("Dataset", back_populates="metadata")

    def __repr__(self):
        return f"<DatasetMetadata(dataset_id={self.dataset_id}, quality_score={self.validity_score})>"
