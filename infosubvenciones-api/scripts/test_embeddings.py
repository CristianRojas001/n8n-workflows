#!/usr/bin/env python
"""
Manual test harness for the embeddings and vector search workflow (Day 11-12).

Run: `python scripts/test_embeddings.py`
This script performs the scenarios described in the sprint instructions:
1. Generate a single embedding from Spanish sample text.
2. Generate an embedding for a PDF extraction pending processing.
3. Queue a batch of embedding tasks.
4. Print embedding statistics.
5. Run a semantic vector search (requires embeddings + HNSW index).
6. Find similar convocatorias using the stored embeddings.
"""

from __future__ import annotations

import sys
import time
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List

# Ensure the Ingestion package is on sys.path so we can import the internal modules.
REPO_ROOT = Path(__file__).resolve().parents[1]
INGESTION_DIR = REPO_ROOT / "Ingestion"
if not INGESTION_DIR.exists():
    raise RuntimeError(
        "Cannot find the 'Ingestion' directory. Please run this script from the "
        "repository root."
    )
if str(INGESTION_DIR) not in sys.path:
    sys.path.insert(0, str(INGESTION_DIR))

from services.embedding_generator import EmbeddingGenerator
from tasks.embedder import (  # type: ignore
    generate_embedding as celery_generate_embedding,
    generate_batch_embeddings as celery_generate_batch_embeddings,
    get_embedding_stats as fetch_embedding_stats,
)
from services.vector_search import VectorSearcher
from config.database import get_db_session
from models.pdf_extraction import PDFExtraction
from models.embedding import Embedding
from sqlalchemy.orm import Session


class TestSkipped(Exception):
    """Raised when a test cannot run because required data is missing."""


class EmbeddingTestRunner:
    """Runs the Day 11-12 embedding & vector search validation flow."""

    SAMPLE_TEXT = (
        "Esta es una convocatoria de subvención para proyectos culturales en la "
        "Comunidad de Madrid"
    )

    def __init__(self) -> None:
        self.results: List[Dict[str, str]] = []
        self.rate_limit_seconds = 4
        self.last_search_results: List[Dict[str, Any]] = []
        self.search_stats: Dict[str, Any] = {}

    def run(self) -> None:
        """Execute all scenarios sequentially."""
        self.run_test("Test 1: Single Embedding Generation", self.test_single_embedding)
        self.pause_for_rate_limit("Before generating embedding for extraction")

        self.run_test(
            "Test 2: Generate Embedding for PDF Extraction",
            self.test_generate_embedding_for_extraction,
        )
        self.run_test(
            "Test 3: Batch Embedding Generation",
            self.test_batch_embedding_generation,
        )
        self.run_test(
            "Test 4: Embedding Statistics",
            self.test_embedding_statistics,
        )

        self.pause_for_rate_limit("Before running semantic search query embedding")
        self.run_test("Test 5: Vector Search", self.test_vector_search)
        self.run_test("Test 6: Find Similar Grants", self.test_find_similar_grants)

        self.print_summary()

    def run_test(self, name: str, func) -> None:
        """Wrapper to run a test function and capture the outcome."""
        print("\n" + "=" * 80)
        print(name)
        print("=" * 80)

        try:
            func()
        except TestSkipped as skipped:
            logging.warning("Skipped %s: %s", name, skipped)
            self.results.append({"name": name, "status": "skipped"})
            print(f"[SKIPPED] {skipped}")
        except Exception as exc:  # pylint: disable=broad-except
            logging.exception("Test failed: %s", name)
            self.results.append({"name": name, "status": "failed"})
            print(f"[FAILED] {exc}")
        else:
            self.results.append({"name": name, "status": "success"})
            print(f"[OK] {name}")

    def pause_for_rate_limit(self, reason: str) -> None:
        """Enforce Gemini API quota recommendations."""
        print(f"\nWaiting {self.rate_limit_seconds}s ({reason})...")
        time.sleep(self.rate_limit_seconds)

    @contextmanager
    def db_session(self) -> Session:
        """Provide a SQLAlchemy session scope."""
        session = get_db_session()
        try:
            yield session
        finally:
            session.close()

    @contextmanager
    def vector_searcher(self):
        """Context manager that yields a VectorSearcher with a managed session."""
        session = get_db_session()
        try:
            searcher = VectorSearcher(db_session=session)
            yield searcher
        finally:
            session.close()

    # ------------------------------------------------------------------
    # Individual test implementations
    # ------------------------------------------------------------------
    def test_single_embedding(self) -> None:
        generator = EmbeddingGenerator()
        print("Generating embedding for sample Spanish text...")
        embedding = generator.generate_embedding(self.SAMPLE_TEXT)

        dimension_count = len(embedding)
        all_floats = all(isinstance(value, float) for value in embedding)

        print(f"- Returned vector length: {dimension_count}")
        print(f"- Expected dimensions: {generator.dimensions}")
        print(f"- Preview (first 8 values): {embedding[:8]}")

        if dimension_count != generator.dimensions:
            raise AssertionError(
                f"Expected {generator.dimensions} dimensions, got {dimension_count}"
            )
        if not all_floats:
            raise AssertionError("Embedding vector contains non-float values")

    def test_generate_embedding_for_extraction(self) -> None:
        if not hasattr(PDFExtraction, "extracted_text"):
            raise RuntimeError(
                "PDFExtraction.extracted_text column is required for this test."
            )
        if not hasattr(Embedding, "extraction_id"):
            raise RuntimeError(
                "Embedding.extraction_id column is required for this test."
            )

        with self.db_session() as session:
            extraction = (
                session.query(PDFExtraction)
                .outerjoin(Embedding, Embedding.extraction_id == PDFExtraction.id)
                .filter(
                    PDFExtraction.extracted_text.isnot(None),
                    PDFExtraction.extracted_text != "",
                    Embedding.id.is_(None),
                )
                .order_by(PDFExtraction.created_at.desc())
                .first()
            )

            if not extraction:
                raise TestSkipped(
                    "No PDF extractions with extracted_text and missing embeddings were found."
                )

            extraction_id = extraction.id
            print(f"Selected extraction_id={extraction_id} for embedding test.")

        result = celery_generate_embedding.run(extraction_id=extraction_id)
        print(f"Task response: {result}")

        if result.get("status") != "success":
            raise AssertionError(f"Embedding task failed: {result}")

        embedding_id = result.get("embedding_id")
        if not embedding_id:
            raise AssertionError("Embedding task did not return embedding_id")

        with self.db_session() as session:
            db_embedding = (
                session.query(Embedding).filter(Embedding.id == embedding_id).first()
            )

            if not db_embedding:
                raise AssertionError("Embedding record not found in database.")

            if db_embedding.extraction_id != extraction_id:
                raise AssertionError(
                    f"Embedding extraction_id mismatch "
                    f"(expected {extraction_id}, got {db_embedding.extraction_id})"
                )

            expected_dims = result.get("dimensions")
            if expected_dims and db_embedding.embedding_dimensions != expected_dims:
                raise AssertionError(
                    f"Embedding dimensions mismatch "
                    f"(expected {expected_dims}, got {db_embedding.embedding_dimensions})"
                )

        print(
            f"Embedding {embedding_id} created for extraction {extraction_id} "
            f"with {result.get('dimensions')} dimensions."
        )

    def test_batch_embedding_generation(self, limit: int = 5) -> None:
        print(f"Queueing up to {limit} embedding tasks...")
        response = celery_generate_batch_embeddings.run(limit=limit)
        print(f"Batch response: {response}")

        if response.get("status") != "success":
            raise AssertionError(f"Batch embedding task failed: {response}")

        queued = int(response.get("queued", 0))
        if queued == 0:
            raise TestSkipped("No extractions pending embeddings; nothing was queued.")

        if queued != limit:
            print(
                f"Warning: Requested {limit} embeddings but only queued {queued}. "
                "This likely means there were fewer pending extractions."
            )

    def test_embedding_statistics(self) -> None:
        stats = fetch_embedding_stats()
        print("Embedding stats:")
        for key, value in stats.items():
            print(f"- {key}: {value}")

        required_keys = {
            "total_extractions",
            "total_embeddings",
            "without_embeddings",
            "completion_rate",
            "avg_dimensions",
            "models_used",
        }
        missing = [key for key in required_keys if key not in stats]
        if missing:
            raise AssertionError(f"Missing stats keys: {missing}")

    def test_vector_search(self) -> None:
        with self.vector_searcher() as searcher:
            stats = searcher.get_search_stats()
            self.search_stats = stats or {}

            print("Vector search stats:")
            for key, value in stats.items():
                print(f"- {key}: {value}")

            if stats.get("total_embeddings", 0) == 0:
                raise TestSkipped("No embeddings present; vector search cannot run.")
            if not stats.get("hnsw_index_exists"):
                raise TestSkipped("HNSW index not found; run init_db.py to create it.")
            if not stats.get("search_ready"):
                raise TestSkipped("Vector search is not ready (missing index or embeddings).")

            query = "subvenciones para cultura en Madrid"
            print(f"Executing semantic search for: '{query}' (limit=3)")
            results = searcher.search(query, limit=3)

            if not results:
                raise AssertionError("Vector search returned no results.")

            for idx, result in enumerate(results, start=1):
                similarity = result.get("similarity")
                titulo = result.get("titulo")
                organismo = result.get("organismo")
                summary = result.get("summary")

                if similarity is None or not (0 <= similarity <= 1):
                    raise AssertionError(f"Invalid similarity score: {similarity}")

                print(
                    f"{idx}. {titulo or 'Sin título'} | "
                    f"Organismo: {organismo or 'N/A'} | "
                    f"Similarity: {similarity} | "
                    f"Resumen: {(summary or '')[:120]}"
                )

            self.last_search_results = results

    def test_find_similar_grants(self) -> None:
        if not self.search_stats:
            raise TestSkipped("Search stats unavailable. Run Test 5 first.")

        if self.search_stats.get("total_embeddings", 0) < 2:
            raise TestSkipped("At least two embeddings are required for similarity search.")

        if not self.last_search_results:
            raise TestSkipped("No prior vector search results available for reference.")

        referencia = next(
            (item for item in self.last_search_results if item.get("convocatoria_id")),
            None,
        )

        if not referencia:
            raise TestSkipped("Unable to determine convocatoria_id from search results.")

        convocatoria_id = referencia["convocatoria_id"]
        print(f"Finding grants similar to convocatoria_id={convocatoria_id}")

        with self.vector_searcher() as searcher:
            results = searcher.find_similar(convocatoria_id, limit=3)

            if not results:
                raise AssertionError("No similar grants were returned.")

            for idx, result in enumerate(results, start=1):
                similarity = result.get("similarity")
                if similarity is None or not (0 <= similarity <= 1):
                    raise AssertionError(f"Invalid similarity score: {similarity}")

                print(
                    f"{idx}. Convocatoria {result.get('convocatoria_id')} | "
                    f"{result.get('titulo') or 'Sin título'} | "
                    f"Similarity: {similarity}"
                )

    def print_summary(self) -> None:
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        for entry in self.results:
            print(f"{entry['status'].upper():>7} - {entry['name']}")
        print("=" * 80)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    runner = EmbeddingTestRunner()
    runner.run()


if __name__ == "__main__":
    main()
