"""Tasks package for InfoSubvenciones ingestion pipeline."""

from .fetcher import fetch_convocatorias, fetch_batch

__all__ = ['fetch_convocatorias', 'fetch_batch']
