"""Embedding model - stores vector embeddings for semantic search."""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

from config.database import Base
from config.settings import get_settings

settings = get_settings()


class Embedding(Base):
    """
    Stores vector embeddings generated from PDF extraction text.

    Uses pgvector extension for efficient similarity search.
    Embeddings are 768-dimensional vectors from Gemini text-embedding-004.

    Each PDF extraction has one embedding generated from its summary + full text.
    """
    __tablename__ = 'embeddings'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to pdf_extractions
    extraction_id = Column(
        Integer,
        ForeignKey('pdf_extractions.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,  # One embedding per extraction
        index=True
    )

    # Relationship to pdf_extraction
    pdf_extraction = relationship("PDFExtraction", backref="embedding")

    # === VECTOR EMBEDDING ===
    # pgvector column - stores 768-dimensional vector from Gemini
    # Will be indexed with HNSW for fast similarity search
    embedding_vector = Column(Vector(768), nullable=False)

    # === EMBEDDING METADATA ===
    model_name = Column(String(100), default='text-embedding-004', nullable=False)  # Gemini embedding model
    embedding_dimensions = Column(Integer, default=768, nullable=False)  # Vector dimensions
    text_length = Column(Integer, nullable=True)  # Length of text that was embedded

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    def __repr__(self):
        return f"<Embedding(extraction_id={self.extraction_id}, model={self.model_name}, dims={self.embedding_dimensions})>"
