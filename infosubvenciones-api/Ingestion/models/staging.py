"""Staging table for tracking ingestion progress."""
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from config.database import Base


class ProcessingStatus(str, enum.Enum):
    """Processing status for staging items."""
    PENDING = "pending"  # Fetched from API, not yet processed
    PROCESSING = "processing"  # Currently being processed
    COMPLETED = "completed"  # Successfully processed (PDF + embedding)
    FAILED = "failed"  # Failed after max retries
    SKIPPED = "skipped"  # Skipped (duplicate or no PDF)


class StagingItem(Base):
    """
    Staging table to track progress of each convocatoria through the pipeline.

    Pipeline flow:
    1. Fetcher task: Insert with status='pending'
    2. Processor task: Update to 'processing', then 'completed' or 'failed'
    3. Embedder task: Runs after processor completes
    4. Retry handler: Re-processes 'failed' items
    """
    __tablename__ = 'staging_items'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Reference to convocatoria (numero_convocatoria from API)
    numero_convocatoria = Column(String(50), unique=True, nullable=False, index=True)

    # Foreign key to convocatorias table (optional - set after convocatoria is created)
    convocatoria_id = Column(
        Integer,
        ForeignKey('convocatorias.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )

    # Relationship to convocatoria
    convocatoria = relationship("Convocatoria", backref="staging_item")

    # Processing status
    status = Column(
        SQLEnum(ProcessingStatus),
        default=ProcessingStatus.PENDING,
        nullable=False,
        index=True
    )

    # Processing metadata
    batch_id = Column(String(100), nullable=True, index=True)  # Group items by batch
    retry_count = Column(Integer, default=0, nullable=False)  # Number of retry attempts
    error_message = Column(Text, nullable=True)  # Last error message

    # PDF metadata (cached from convocatoria for faster querying)
    pdf_url = Column(Text, nullable=True)  # URL to PDF document
    pdf_hash = Column(String(64), nullable=True, index=True)  # SHA256 hash of PDF URL

    # Stage tracking (which pipeline stage last processed this item)
    last_stage = Column(String(50), nullable=True)  # 'fetcher', 'processor', 'embedder'

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)  # When fully completed

    def __repr__(self):
        return f"<StagingItem(numero={self.numero_convocatoria}, status={self.status.value})>"

    def mark_processing(self, stage: str):
        """Mark item as currently being processed."""
        self.status = ProcessingStatus.PROCESSING
        self.last_stage = stage
        self.updated_at = datetime.utcnow()

    def mark_completed(self):
        """Mark item as successfully completed."""
        self.status = ProcessingStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.error_message = None

    def mark_failed(self, error: str):
        """Mark item as failed with error message."""
        self.status = ProcessingStatus.FAILED
        self.error_message = error
        self.retry_count += 1

    def mark_skipped(self, reason: str):
        """Mark item as skipped."""
        self.status = ProcessingStatus.SKIPPED
        self.error_message = reason
