"""
Embedding generation service using Gemini API.

Generates vector embeddings from text content for semantic search.
Uses Gemini's embedding model (text-embedding-004, 768 dimensions).
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import time

import google.generativeai as genai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmbeddingGenerator:
    """
    Generate embeddings using Gemini API.

    Features:
    - Batch processing support
    - Automatic retry with exponential backoff
    - Rate limiting handling
    - Token/content length validation
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the embedding generator.

        Args:
            api_key: Gemini API key (defaults to settings.GEMINI_API_KEY)
        """
        self.api_key = api_key or settings.gemini_api_key
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required")

        genai.configure(api_key=self.api_key)
        self.model_name = settings.gemini_embedding_model
        self.dimensions = settings.embedding_dimensions

        logger.info(
            f"Initialized EmbeddingGenerator with model={self.model_name}, "
            f"dimensions={self.dimensions}"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )
    def generate_embedding(
        self,
        text: str,
        task_type: str = "SEMANTIC_SIMILARITY",
        title: Optional[str] = None
    ) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text content to embed
            task_type: Task type for embedding (SEMANTIC_SIMILARITY, RETRIEVAL_QUERY, etc.)
            title: Optional title for the content (improves embedding quality)

        Returns:
            List of float values representing the embedding vector

        Raises:
            ValueError: If text is empty or too short
            Exception: If API call fails after retries
        """
        if not text or len(text.strip()) < 10:
            raise ValueError("Text must be at least 10 characters")

        # Truncate text if too long (Gemini has ~30k token limit, use ~10k words = ~15k tokens)
        max_chars = 60000  # ~10k words
        if len(text) > max_chars:
            logger.warning(
                f"Text length {len(text)} exceeds {max_chars}, truncating"
            )
            text = text[:max_chars]

        if title and task_type != "RETRIEVAL_DOCUMENT":
            logger.debug(
                "Title provided; overriding task_type from %s to RETRIEVAL_DOCUMENT",
                task_type,
            )
            task_type = "RETRIEVAL_DOCUMENT"

        try:
            start_time = time.time()

            # Call Gemini embedding API
            result = genai.embed_content(
                model=f"models/{self.model_name}",
                content=text,
                task_type=task_type,
                title=title,
            )

            embedding = result['embedding']
            elapsed = time.time() - start_time

            logger.info(
                f"Generated embedding in {elapsed:.2f}s "
                f"(text_len={len(text)}, dim={len(embedding)})"
            )

            # Validate embedding
            if len(embedding) != self.dimensions:
                raise ValueError(
                    f"Expected {self.dimensions} dimensions, got {len(embedding)}"
                )

            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )
    def generate_batch_embeddings(
        self,
        texts: List[str],
        task_type: str = "SEMANTIC_SIMILARITY",
        titles: Optional[List[str]] = None
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Note: Gemini doesn't have a native batch API, so this processes
        texts sequentially with rate limiting.

        Args:
            texts: List of text contents to embed
            task_type: Task type for embeddings
            titles: Optional list of titles (must match length of texts)

        Returns:
            List of embedding vectors

        Raises:
            ValueError: If inputs are invalid
            Exception: If any API call fails after retries
        """
        if not texts:
            raise ValueError("texts list cannot be empty")

        if titles and len(titles) != len(texts):
            raise ValueError("titles must match length of texts")

        logger.info(f"Generating {len(texts)} embeddings...")

        embeddings = []
        start_time = time.time()

        for i, text in enumerate(texts):
            title = titles[i] if titles else None

            try:
                embedding = self.generate_embedding(
                    text=text,
                    task_type=task_type,
                    title=title
                )
                embeddings.append(embedding)

                # Rate limiting: 15 requests per minute = 4 seconds per request
                if i < len(texts) - 1:  # Don't wait after last item
                    time.sleep(4)

            except Exception as e:
                logger.error(f"Failed to embed text {i}: {e}")
                raise

        elapsed = time.time() - start_time
        logger.info(
            f"Generated {len(embeddings)} embeddings in {elapsed:.2f}s "
            f"({elapsed/len(embeddings):.2f}s per item)"
        )

        return embeddings

    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.

        Uses RETRIEVAL_QUERY task type for better search performance.

        Args:
            query: Search query text

        Returns:
            Embedding vector for the query
        """
        return self.generate_embedding(
            text=query,
            task_type="RETRIEVAL_QUERY"
        )

    def prepare_text_for_embedding(
        self,
        summary: Optional[str],
        full_text: Optional[str],
        metadata: Optional[Dict[str, Any]] = None,
        max_length: int = 60000
    ) -> str:
        """
        Prepare text content for embedding.

        Combines summary, full text, and metadata into a single text.
        Prioritizes summary over full text if length exceeds limit.

        Args:
            summary: Brief summary of content
            full_text: Full text content
            metadata: Additional metadata to include (e.g., titulo, organismo)
            max_length: Maximum character length

        Returns:
            Combined text ready for embedding
        """
        parts = []

        # Add metadata first (if provided)
        if metadata:
            for key, value in metadata.items():
                if value:
                    parts.append(f"{key}: {value}")

        # Add summary (preferred)
        if summary:
            parts.append(f"\nResumen: {summary}")

        # Add full text if space available
        if full_text:
            combined = "\n\n".join(parts)
            remaining = max_length - len(combined)

            if remaining > 1000:  # Only add if meaningful space left
                parts.append(f"\nContenido completo:\n{full_text[:remaining]}")

        text = "\n\n".join(parts)

        # Final truncation
        if len(text) > max_length:
            text = text[:max_length]

        return text.strip()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get embedding generator statistics.

        Returns:
            Dictionary with model info and settings
        """
        return {
            "model": self.model_name,
            "dimensions": self.dimensions,
            "api_configured": bool(self.api_key),
            "max_text_length": 60000,
            "rate_limit": "15 requests per minute",
        }


# Context manager support
class EmbeddingGeneratorContext:
    """Context manager for EmbeddingGenerator."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.generator = None

    def __enter__(self) -> EmbeddingGenerator:
        self.generator = EmbeddingGenerator(api_key=self.api_key)
        return self.generator

    def __exit__(self, exc_type, exc_val, exc_tb):
        # No cleanup needed for Gemini client
        pass


# Convenience function
def create_embedding_generator(api_key: Optional[str] = None) -> EmbeddingGenerator:
    """
    Create an EmbeddingGenerator instance.

    Args:
        api_key: Optional API key override

    Returns:
        Configured EmbeddingGenerator
    """
    return EmbeddingGenerator(api_key=api_key)


if __name__ == "__main__":
    # Quick test
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    try:
        generator = create_embedding_generator()
        print(f"✅ EmbeddingGenerator initialized: {generator.get_stats()}")

        # Test single embedding
        test_text = "Esta es una convocatoria de subvención para proyectos culturales en Madrid."
        embedding = generator.generate_embedding(test_text)
        print(f"✅ Generated embedding with {len(embedding)} dimensions")
        print(f"   First 5 values: {embedding[:5]}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
