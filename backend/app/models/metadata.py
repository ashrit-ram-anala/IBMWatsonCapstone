"""Dataset metadata model for storing processing statistics."""
from sqlalchemy import Column, String, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class DatasetMetadata(BaseModel):
    __tablename__ = "dataset_metadata"

    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), unique=True, nullable=False)

    columns = Column(JSON, nullable=True)
    column_count = Column(Integer, default=0)

    completeness_score = Column(Float, default=0.0)
    validity_score = Column(Float, default=0.0)
    consistency_score = Column(Float, default=0.0)
    accuracy_score = Column(Float, default=0.0)

    null_counts = Column(JSON, nullable=True)
    null_percentages = Column(JSON, nullable=True)

    data_types = Column(JSON, nullable=True)
    type_violations = Column(JSON, nullable=True)

    unique_counts = Column(JSON, nullable=True)
    value_distributions = Column(JSON, nullable=True)

    numeric_stats = Column(JSON, nullable=True)

    date_range = Column(JSON, nullable=True)

    cleaning_summary = Column(JSON, nullable=True)

    transformations = Column(JSON, nullable=True)

    file_size_bytes = Column(Integer, nullable=True)
    file_format = Column(String, nullable=True)
    encoding = Column(String, nullable=True)

    dataset = relationship("Dataset", back_populates="metadata")

    def __repr__(self):
        return f"<DatasetMetadata(dataset_id={self.dataset_id}, quality_score={self.validity_score})>"
