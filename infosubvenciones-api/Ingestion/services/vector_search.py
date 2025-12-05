"""
Vector search service using pgvector.

Provides semantic search over grant embeddings with hybrid filtering.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy import func, and_, or_, cast, String, text
from sqlalchemy.orm import Session, joinedload

from config.database import get_db
from models.embedding import Embedding
from models.pdf_extraction import PDFExtraction
from models.convocatoria import Convocatoria
from models.staging import StagingItem
from services.embedding_generator import EmbeddingGenerator

logger = logging.getLogger(__name__)


class VectorSearcher:
    """
    Semantic search over grant embeddings.

    Features:
    - Cosine similarity search with pgvector
    - Hybrid search (semantic + filters)
    - Ranking and relevance scoring
    - Result metadata enrichment
    """

    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize the vector searcher.

        Args:
            db_session: Optional database session (creates new if not provided)
        """
        self.db = db_session or next(get_db())
        self.embedding_generator = EmbeddingGenerator()

        logger.info("Initialized VectorSearcher")

    def search(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        min_similarity: float = 0.5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for grants matching a query.

        Args:
            query: Natural language search query
            limit: Maximum number of results
            offset: Result offset for pagination
            min_similarity: Minimum cosine similarity (0-1)
            filters: Optional filters (organismo, ambito, finalidad, etc.)

        Returns:
            List of search results with relevance scores and metadata

        Example:
            >>> results = searcher.search(
            ...     query="subvenciones para proyectos culturales en Madrid",
            ...     limit=5,
            ...     filters={"ambito": "COMUNIDAD_AUTONOMA", "organismo": "Madrid"}
            ... )
        """
        logger.info(
            f"Searching: query='{query}', limit={limit}, "
            f"offset={offset}, min_similarity={min_similarity}"
        )

        try:
            # 1. Generate query embedding
            query_embedding = self.embedding_generator.generate_query_embedding(query)

            # 2. Build query with cosine similarity
            # pgvector uses <=> operator for cosine distance (1 - cosine similarity)
            # So similarity = 1 - distance
            query_obj = self.db.query(
                Embedding.id.label("embedding_id"),
                Embedding.extraction_id,
                (1 - Embedding.embedding_vector.cosine_distance(query_embedding)).label("similarity"),
                PDFExtraction.extracted_summary,
                PDFExtraction.summary_preview,
                PDFExtraction.titulo,
                PDFExtraction.organismo,
                PDFExtraction.ambito_geografico,
                Convocatoria.id.label("convocatoria_id"),
                Convocatoria.titulo.label("conv_titulo"),
                Convocatoria.organismo.label("conv_organismo"),
                Convocatoria.ambito.label("conv_ambito"),
                Convocatoria.finalidad,
                Convocatoria.bases_reguladoras,
                Convocatoria.fecha_publicacion,
                Convocatoria.fecha_inicio_solicitud,
                Convocatoria.fecha_fin_solicitud,
            ).join(
                PDFExtraction, Embedding.extraction_id == PDFExtraction.id
            ).join(
                StagingItem, PDFExtraction.staging_id == StagingItem.id
            ).outerjoin(
                Convocatoria, StagingItem.convocatoria_id == Convocatoria.id
            )

            # 3. Apply filters
            if filters:
                filter_conditions = []

                # Organismo filter (partial match)
                if "organismo" in filters and filters["organismo"]:
                    organismo = filters["organismo"]
                    filter_conditions.append(
                        or_(
                            Convocatoria.organismo.ilike(f"%{organismo}%"),
                            PDFExtraction.organismo.ilike(f"%{organismo}%")
                        )
                    )

                # Ambito filter (exact match)
                if "ambito" in filters and filters["ambito"]:
                    ambito = filters["ambito"]
                    filter_conditions.append(
                        or_(
                            Convocatoria.ambito == ambito,
                            PDFExtraction.ambito_geografico.ilike(f"%{ambito}%")
                        )
                    )

                # Finalidad filter (exact match)
                if "finalidad" in filters and filters["finalidad"]:
                    finalidad = filters["finalidad"]
                    filter_conditions.append(
                        Convocatoria.finalidad == finalidad
                    )

                # Date range filter
                if "fecha_desde" in filters and filters["fecha_desde"]:
                    filter_conditions.append(
                        Convocatoria.fecha_publicacion >= filters["fecha_desde"]
                    )

                if "fecha_hasta" in filters and filters["fecha_hasta"]:
                    filter_conditions.append(
                        Convocatoria.fecha_publicacion <= filters["fecha_hasta"]
                    )

                # Open/closed status
                if "estado" in filters and filters["estado"]:
                    now = datetime.utcnow().date()
                    estado = filters["estado"]

                    if estado == "abierta":
                        filter_conditions.append(
                            and_(
                                Convocatoria.fecha_inicio_solicitud <= now,
                                Convocatoria.fecha_fin_solicitud >= now
                            )
                        )
                    elif estado == "cerrada":
                        filter_conditions.append(
                            Convocatoria.fecha_fin_solicitud < now
                        )
                    elif estado == "proxima":
                        filter_conditions.append(
                            Convocatoria.fecha_inicio_solicitud > now
                        )

                if filter_conditions:
                    query_obj = query_obj.filter(and_(*filter_conditions))

            # 4. Apply similarity threshold
            query_obj = query_obj.filter(
                (1 - Embedding.embedding_vector.cosine_distance(query_embedding)) >= min_similarity
            )

            # 5. Order by similarity and apply pagination
            results = query_obj.order_by(
                (1 - Embedding.embedding_vector.cosine_distance(query_embedding)).desc()
            ).limit(limit).offset(offset).all()

            # 6. Format results
            formatted_results = []
            for row in results:
                result = {
                    "embedding_id": row.embedding_id,
                    "extraction_id": row.extraction_id,
                    "convocatoria_id": row.convocatoria_id,
                    "similarity": round(float(row.similarity), 4),
                    "titulo": row.titulo or row.conv_titulo,
                    "organismo": row.organismo or row.conv_organismo,
                    "ambito": row.ambito_geografico or row.conv_ambito,
                    "finalidad": row.finalidad,
                    "summary": row.summary_preview or row.extracted_summary,
                    "bases_reguladoras": row.bases_reguladoras,
                    "fecha_publicacion": (
                        row.fecha_publicacion.isoformat()
                        if row.fecha_publicacion else None
                    ),
                    "fecha_inicio": (
                        row.fecha_inicio_solicitud.isoformat()
                        if row.fecha_inicio_solicitud else None
                    ),
                    "fecha_fin": (
                        row.fecha_fin_solicitud.isoformat()
                        if row.fecha_fin_solicitud else None
                    ),
                }
                formatted_results.append(result)

            logger.info(f"Found {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            raise

    def find_similar(
        self,
        convocatoria_id: int,
        limit: int = 5,
        min_similarity: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Find grants similar to a given convocatoria.

        Args:
            convocatoria_id: ID of the reference convocatoria
            limit: Maximum number of similar grants
            min_similarity: Minimum cosine similarity

        Returns:
            List of similar grants with similarity scores
        """
        logger.info(
            f"Finding similar grants: convocatoria_id={convocatoria_id}, "
            f"limit={limit}"
        )

        try:
            # 1. Get the embedding for the reference convocatoria
            ref_embedding = self.db.query(Embedding).join(
                PDFExtraction
            ).join(
                StagingItem
            ).filter(
                StagingItem.convocatoria_id == convocatoria_id
            ).first()

            if not ref_embedding:
                logger.warning(
                    f"No embedding found for convocatoria_id={convocatoria_id}"
                )
                return []

            # 2. Find similar embeddings
            results = self.db.query(
                Embedding.id.label("embedding_id"),
                Embedding.extraction_id,
                (1 - Embedding.embedding_vector.cosine_distance(
                    ref_embedding.embedding_vector
                )).label("similarity"),
                Convocatoria.id.label("convocatoria_id"),
                Convocatoria.titulo,
                Convocatoria.organismo,
                PDFExtraction.summary_preview,
            ).join(
                PDFExtraction, Embedding.extraction_id == PDFExtraction.id
            ).join(
                StagingItem, PDFExtraction.staging_id == StagingItem.id
            ).join(
                Convocatoria, StagingItem.convocatoria_id == Convocatoria.id
            ).filter(
                Convocatoria.id != convocatoria_id,  # Exclude self
                (1 - Embedding.embedding_vector.cosine_distance(
                    ref_embedding.embedding_vector
                )) >= min_similarity
            ).order_by(
                (1 - Embedding.embedding_vector.cosine_distance(
                    ref_embedding.embedding_vector
                )).desc()
            ).limit(limit).all()

            # 3. Format results
            formatted_results = []
            for row in results:
                result = {
                    "convocatoria_id": row.convocatoria_id,
                    "similarity": round(float(row.similarity), 4),
                    "titulo": row.titulo,
                    "organismo": row.organismo,
                    "summary": row.summary_preview,
                }
                formatted_results.append(result)

            logger.info(f"Found {len(formatted_results)} similar grants")
            return formatted_results

        except Exception as e:
            logger.error(f"Failed to find similar grants: {e}", exc_info=True)
            raise

    def get_search_stats(self) -> Dict[str, Any]:
        """
        Get search system statistics.

        Returns:
            Dict with index stats and performance metrics
        """
        try:
            # Total embeddings
            total_embeddings = self.db.query(func.count(Embedding.id)).scalar() or 0

            # Average embedding dimensions
            avg_dimensions = self.db.query(
                func.avg(Embedding.embedding_dimensions)
            ).scalar() or 0

            # Check if HNSW index exists
            index_check = self.db.execute(
                text("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = 'embeddings'
                AND indexname LIKE '%hnsw%'
                """)
            ).fetchone()

            return {
                "total_embeddings": total_embeddings,
                "avg_dimensions": round(avg_dimensions, 0),
                "hnsw_index_exists": bool(index_check),
                "index_name": index_check[0] if index_check else None,
                "search_ready": total_embeddings > 0 and bool(index_check),
            }

        except Exception as e:
            logger.error(f"Failed to get search stats: {e}", exc_info=True)
            return {"error": str(e)}


# Context manager support
class VectorSearcherContext:
    """Context manager for VectorSearcher."""

    def __init__(self):
        self.searcher = None
        self.db = None

    def __enter__(self) -> VectorSearcher:
        self.db = next(get_db())
        self.searcher = VectorSearcher(db_session=self.db)
        return self.searcher

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            self.db.close()


# Convenience functions
def create_searcher(db_session: Optional[Session] = None) -> VectorSearcher:
    """
    Create a VectorSearcher instance.

    Args:
        db_session: Optional database session

    Returns:
        Configured VectorSearcher
    """
    return VectorSearcher(db_session=db_session)


def quick_search(
    query: str,
    limit: int = 10,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Quick search convenience function.

    Args:
        query: Search query
        limit: Max results
        **kwargs: Additional search parameters

    Returns:
        List of search results
    """
    with VectorSearcherContext() as searcher:
        return searcher.search(query, limit=limit, **kwargs)


if __name__ == "__main__":
    # Test the vector searcher
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    try:
        with VectorSearcherContext() as searcher:
            # Get stats
            stats = searcher.get_search_stats()
            print("\n" + "=" * 60)
            print("VECTOR SEARCH STATISTICS")
            print("=" * 60)
            for key, value in stats.items():
                print(f"{key}: {value}")
            print("=" * 60)

            # Test search if embeddings exist
            if stats.get("total_embeddings", 0) > 0:
                print("\nTesting search with query: 'proyectos culturales'")
                results = searcher.search(
                    query="proyectos culturales",
                    limit=3
                )
                print(f"\nFound {len(results)} results:")
                for i, result in enumerate(results, 1):
                    print(f"\n{i}. {result.get('titulo', 'N/A')}")
                    print(f"   Similarity: {result['similarity']}")
                    print(f"   Organismo: {result.get('organismo', 'N/A')}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
