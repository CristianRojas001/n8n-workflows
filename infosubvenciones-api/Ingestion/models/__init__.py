"""Database models for Ingestion pipeline."""
from .staging import StagingItem
from .convocatoria import Convocatoria
from .pdf_extraction import PDFExtraction
from .embedding import Embedding

__all__ = ['StagingItem', 'Convocatoria', 'PDFExtraction', 'Embedding']
