# Legal GraphRAG System - Retrieval Guide

## Document Information
- **Version**: 1.0 (MVP)
- **Last Updated**: 2025-12-11
- **Status**: Planning Phase
- **Related**: [01_ARCHITECTURE.md](./01_ARCHITECTURE.md) | [03_INGESTION_GUIDE.md](./03_INGESTION_GUIDE.md)

---

## 1. Retrieval Architecture Overview

The Legal GraphRAG retrieval system implements **hierarchical hybrid search** that respects Spanish legal authority while providing semantic understanding.

### Key Principles

1. **Legal Hierarchy First**: Constitution > Ley > Real Decreto > Orden > Doctrina > Jurisprudencia
2. **Hybrid Search**: Semantic (pgvector) + Lexical (PostgreSQL FTS)
3. **Priority-Based**: P1 sources before P2 sources before P3
4. **Multi-Stage**: Search Normativa first, then Doctrina, then Jurisprudencia

### Retrieval Pipeline

```
┌──────────────────────────────────────────────────────────┐
│ 1. QUERY ANALYSIS                                        │
│ - Classify area (Fiscal, Laboral, IP, etc.)             │
│ - Extract keywords                                       │
│ - Detect query intent                                    │
└──────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────┐
│ 2. HIERARCHICAL SEARCH                                   │
│                                                          │
│ 2a. Search NORMATIVA (P1)                               │
│     - Vector search (semantic)                           │
│     - Lexical search (keyword)                           │
│     - Merge results (RRF)                                │
│     - Rerank by legal authority                          │
│     → Top 5 normativa chunks                             │
│                                                          │
│ 2b. Search DOCTRINA (P1)                                │
│     - Same process                                       │
│     → Top 3 doctrina chunks                              │
│                                                          │
│ 2c. Search JURISPRUDENCIA (Optional)                    │
│     - Same process                                       │
│     → Top 2 case law chunks                              │
└──────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────┐
│ 3. POST-PROCESSING                                       │
│ - Deduplicate sources                                    │
│ - Format citations                                       │
│ - Enrich with metadata                                   │
└──────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────┐
│ 4. LLM PROMPTING                                         │
│ - Build hierarchical context                             │
│ - Generate structured answer                             │
│ - Extract citations                                      │
└──────────────────────────────────────────────────────────┘
```

---

## 2. Legal Search Engine

### 2.1 Core Implementation

```python
# apps/legal_graphrag/services/legal_search_engine.py

from typing import List, Dict, Optional
from django.db import connection
import logging

logger = logging.getLogger('apps.legal_graphrag.search')

class LegalSearchEngine:
    """
    Implements hierarchical hybrid search for legal documents
    """

    def __init__(self):
        from apps.legal_graphrag.services.embedding_service import EmbeddingService
        self.embedding_service = EmbeddingService()

    def hybrid_search(
        self,
        query: str,
        filters: Optional[Dict] = None,
        limit: int = 5
    ) -> List[Dict]:
        """
        Hybrid search: Vector (semantic) + Lexical (BM25)

        Args:
            query: User query text
            filters: {
                'naturaleza': 'Normativa',
                'prioridad': 'P1',
                'area_principal': 'Fiscal'
            }
            limit: Max results to return

        Returns:
            List of ranked chunks with similarity scores
        """
        filters = filters or {}

        # STEP 1: Generate query embedding
        query_embedding = self.embedding_service.embed(query)

        # STEP 2: Vector search
        vector_results = self._vector_search(
            query_embedding,
            filters,
            limit * 2  # Fetch more for fusion
        )

        # STEP 3: Lexical search
        lexical_results = self._lexical_search(
            query,
            filters,
            limit * 2
        )

        # STEP 4: Reciprocal Rank Fusion (RRF)
        merged_results = self._reciprocal_rank_fusion(
            vector_results,
            lexical_results
        )

        # STEP 5: Rerank by legal authority
        reranked = self._rerank_by_authority(merged_results)

        return reranked[:limit]

    def _vector_search(
        self,
        embedding: List[float],
        filters: Dict,
        limit: int
    ) -> List[Dict]:
        """
        Semantic search using pgvector cosine similarity
        """
        # Build filter conditions
        where_conditions = []
        params = [embedding, limit]

        if filters.get('naturaleza'):
            where_conditions.append("metadata->>'naturaleza' = %s")
            params.insert(-1, filters['naturaleza'])

        if filters.get('prioridad'):
            where_conditions.append("metadata->>'prioridad' = %s")
            params.insert(-1, filters['prioridad'])

        if filters.get('area_principal'):
            where_conditions.append("metadata->>'area_principal' = %s")
            params.insert(-1, filters['area_principal'])

        where_clause = " AND ".join(where_conditions) if where_conditions else "TRUE"

        sql = f"""
            SELECT
                id,
                chunk_label,
                chunk_text,
                metadata,
                1 - (embedding <=> %s::vector(768)) AS similarity
            FROM legal_document_chunks
            WHERE {where_clause}
            ORDER BY embedding <=> %s::vector(768)
            LIMIT %s
        """

        # Execute with embedding twice (for WHERE and ORDER BY)
        params_with_embedding = [embedding] + params[:-2] + [embedding, limit]

        with connection.cursor() as cursor:
            cursor.execute(sql, params_with_embedding)
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        logger.info(f"Vector search found {len(results)} results")
        return results

    def _lexical_search(
        self,
        query: str,
        filters: Dict,
        limit: int
    ) -> List[Dict]:
        """
        Lexical search using PostgreSQL full-text search (Spanish)
        """
        # Prepare query for PostgreSQL FTS (convert to tsquery format)
        # "gastos deducibles" → "gastos & deducibles"
        tsquery = ' & '.join(query.split())

        where_conditions = []
        params = [tsquery]

        if filters.get('naturaleza'):
            where_conditions.append("metadata->>'naturaleza' = %s")
            params.append(filters['naturaleza'])

        if filters.get('prioridad'):
            where_conditions.append("metadata->>'prioridad' = %s")
            params.append(filters['prioridad'])

        if filters.get('area_principal'):
            where_conditions.append("metadata->>'area_principal' = %s")
            params.append(filters['area_principal'])

        where_clause = " AND ".join(where_conditions) if where_conditions else "TRUE"

        sql = f"""
            SELECT
                id,
                chunk_label,
                chunk_text,
                metadata,
                ts_rank(search_vector, to_tsquery('spanish', %s)) AS rank
            FROM legal_document_chunks
            WHERE search_vector @@ to_tsquery('spanish', %s)
              AND {where_clause}
            ORDER BY rank DESC
            LIMIT %s
        """

        params_final = [tsquery, tsquery] + params[1:] + [limit]

        with connection.cursor() as cursor:
            cursor.execute(sql, params_final)
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        logger.info(f"Lexical search found {len(results)} results")
        return results

    def _reciprocal_rank_fusion(
        self,
        vector_results: List[Dict],
        lexical_results: List[Dict],
        k: int = 60
    ) -> List[Dict]:
        """
        Reciprocal Rank Fusion (RRF) to merge vector and lexical results

        RRF formula:
        score(chunk) = Σ 1 / (k + rank_in_list)

        Args:
            vector_results: Results from vector search
            lexical_results: Results from lexical search
            k: RRF constant (typically 60)

        Returns:
            Merged and sorted results
        """
        scores = {}

        # Add vector scores
        for rank, result in enumerate(vector_results, 1):
            chunk_id = str(result['id'])
            scores[chunk_id] = scores.get(chunk_id, 0) + (1 / (k + rank))

        # Add lexical scores
        for rank, result in enumerate(lexical_results, 1):
            chunk_id = str(result['id'])
            scores[chunk_id] = scores.get(chunk_id, 0) + (1 / (k + rank))

        # Build merged results with RRF scores
        all_results = {str(r['id']): r for r in vector_results + lexical_results}

        merged = []
        for chunk_id, rrf_score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            if chunk_id in all_results:
                result = all_results[chunk_id]
                result['rrf_score'] = rrf_score
                merged.append(result)

        logger.info(f"RRF merged {len(merged)} unique results")
        return merged

    def _rerank_by_authority(self, results: List[Dict]) -> List[Dict]:
        """
        Rerank results by legal authority level

        Boost scores based on nivel_autoridad:
        - Constitución: 2.0x
        - Ley: 1.5x
        - Real Decreto: 1.3x
        - Orden: 1.1x
        - Doctrina: 1.0x
        - Jurisprudencia: 0.9x
        """
        authority_multipliers = {
            'Constitución': 2.0,
            'Ley': 1.5,
            'Real Decreto': 1.3,
            'Real Decreto Legislativo': 1.4,
            'Orden': 1.1,
            'Doctrina administrativa': 1.0,
            'Jurisprudencia': 0.9,
        }

        for result in results:
            nivel = result.get('metadata', {}).get('nivel_autoridad', 'Doctrina administrativa')
            multiplier = authority_multipliers.get(nivel, 1.0)

            # Apply multiplier to RRF score
            original_score = result.get('rrf_score', 0)
            result['rrf_score'] = original_score * multiplier
            result['authority_boost'] = multiplier

        # Re-sort by boosted scores
        results.sort(key=lambda x: x.get('rrf_score', 0), reverse=True)

        return results

    def search_by_hierarchy(
        self,
        query: str,
        area_principal: Optional[str] = None
    ) -> Dict:
        """
        Hierarchical search respecting legal authority

        Returns:
            {
                'normativa': [chunk1, chunk2, ...],
                'doctrina': [chunk1, chunk2, ...],
                'jurisprudencia': [chunk1, chunk2]
            }
        """
        results = {
            'normativa': [],
            'doctrina': [],
            'jurisprudencia': []
        }

        # 1. Search Normativa (highest priority)
        normativa_filters = {
            'naturaleza': 'Normativa',
            'prioridad': 'P1'
        }
        if area_principal:
            normativa_filters['area_principal'] = area_principal

        results['normativa'] = self.hybrid_search(
            query,
            filters=normativa_filters,
            limit=5
        )

        logger.info(f"Found {len(results['normativa'])} normativa chunks")

        # 2. Search Doctrina (if normativa found)
        if results['normativa']:
            doctrina_filters = {'naturaleza': 'Doctrina administrativa'}
            if area_principal:
                doctrina_filters['area_principal'] = area_principal

            results['doctrina'] = self.hybrid_search(
                query,
                filters=doctrina_filters,
                limit=3
            )

            logger.info(f"Found {len(results['doctrina'])} doctrina chunks")

        # 3. Search Jurisprudencia (optional for MVP)
        juris_filters = {'naturaleza': 'Jurisprudencia'}
        if area_principal:
            juris_filters['area_principal'] = area_principal

        results['jurisprudencia'] = self.hybrid_search(
            query,
            filters=juris_filters,
            limit=2
        )

        logger.info(f"Found {len(results['jurisprudencia'])} jurisprudencia chunks")

        return results
```

---

## 3. Query Intent Classification

```python
# apps/legal_graphrag/services/intent_classifier.py

from typing import Optional
import re

class IntentClassifier:
    """
    Simple keyword-based intent classifier

    Post-MVP: Replace with ML classifier (fine-tuned BERT)
    """

    # Keywords for each area
    AREA_KEYWORDS = {
        'Fiscal': [
            'iva', 'irpf', 'impuesto', 'tribut', 'fiscal', 'hacienda',
            'deducci', 'retenci', 'declaraci', 'aeat', 'dgt',
            'mecenazgo', 'exenci', 'base imponible', 'tipo impositivo'
        ],
        'Laboral': [
            'contrato', 'laboral', 'empleo', 'trabajad', 'salar',
            'autónom', 'seguridad social', 'cotiza', 'despido',
            'convenio', 'nómin', 'alta', 'baja', 'afilia'
        ],
        'Propiedad Intelectual': [
            'derechos de autor', 'copyright', 'propiedad intelectual',
            'sgae', 'cedro', 'vegap', 'registro', 'licencia',
            'obra', 'plagio', 'moral', 'económic', 'royalt'
        ],
        'Contabilidad': [
            'contab', 'pgc', 'libro', 'asiento', 'balance',
            'cuenta', 'amortiza', 'provisi', 'patrimonio'
        ],
        'Subvenciones': [
            'subvenci', 'ayuda', 'beca', 'grant', 'convocatoria',
            'solicitud', 'elegib', 'ministerio', 'cultura'
        ]
    }

    def classify_area(self, query: str) -> Optional[str]:
        """
        Classify query into legal area

        Args:
            query: User query text

        Returns:
            Area name or None if no clear match
        """
        query_lower = query.lower()

        # Score each area
        scores = {}
        for area, keywords in self.AREA_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > 0:
                scores[area] = score

        if not scores:
            return None

        # Return area with highest score
        return max(scores.items(), key=lambda x: x[1])[0]

    def extract_keywords(self, query: str) -> list:
        """Extract important keywords from query"""
        # Remove common stopwords
        stopwords = [
            'el', 'la', 'los', 'las', 'un', 'una', 'de', 'del', 'en',
            'para', 'por', 'con', 'es', 'son', 'está', 'pueden',
            'cómo', 'qué', 'cuál', 'dónde', 'cuándo', 'puedo', 'debo'
        ]

        words = query.lower().split()
        keywords = [w for w in words if w not in stopwords and len(w) > 3]

        return keywords
```

---

## 4. Legal RAG Engine

```python
# apps/legal_graphrag/services/legal_rag_engine.py

import google.generativeai as genai
from django.conf import settings
from typing import Dict, List
import logging

logger = logging.getLogger('apps.legal_graphrag.rag')

class LegalRAGEngine:
    """
    End-to-end RAG pipeline for legal Q&A
    """

    def __init__(self):
        from apps.legal_graphrag.services.legal_search_engine import LegalSearchEngine
        from apps.legal_graphrag.services.intent_classifier import IntentClassifier

        self.search_engine = LegalSearchEngine()
        self.intent_classifier = IntentClassifier()

        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_CHAT_MODEL)

    def answer_query(self, query: str) -> Dict:
        """
        End-to-end RAG: Retrieve sources + Generate answer

        Args:
            query: User question

        Returns:
            {
                'answer': str (markdown),
                'sources': List[dict],
                'metadata': dict
            }
        """
        logger.info(f"Processing query: {query[:100]}")

        # 1. Classify intent
        area = self.intent_classifier.classify_area(query)
        logger.info(f"Classified area: {area}")

        # 2. Hierarchical retrieval
        sources = self.search_engine.search_by_hierarchy(query, area)

        # 3. Build LLM prompt
        prompt = self._build_prompt(query, sources)

        # 4. Generate answer
        try:
            response = self.model.generate_content(prompt)
            answer = response.text
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            answer = self._fallback_answer(sources)

        # 5. Format sources for display
        formatted_sources = self._format_sources(sources)

        # 6. Return structured response
        return {
            'answer': answer,
            'sources': formatted_sources,
            'metadata': {
                'area_principal': area,
                'model': settings.GEMINI_CHAT_MODEL,
                'normativa_count': len(sources['normativa']),
                'doctrina_count': len(sources['doctrina']),
                'jurisprudencia_count': len(sources['jurisprudencia']),
            }
        }

    def _build_prompt(self, query: str, sources: Dict) -> str:
        """
        Build hierarchical LLM prompt

        Prompt structure:
        1. System instructions (role, rules)
        2. Hierarchical context (Normativa > Doctrina > Juris)
        3. User query
        4. Output format instructions
        """
        # Format source chunks
        normativa_text = self._format_chunks_for_prompt(sources['normativa'], 'NORMATIVA')
        doctrina_text = self._format_chunks_for_prompt(sources['doctrina'], 'DOCTRINA')
        juris_text = self._format_chunks_for_prompt(sources['jurisprudencia'], 'JURISPRUDENCIA')

        prompt = f"""Eres un asistente legal especializado para artistas y profesionales culturales en España.

**JERARQUÍA DE FUENTES (orden de autoridad legal)**:
1. **NORMATIVA** (Constitución, Leyes, Reales Decretos, Órdenes) - MÁXIMA AUTORIDAD
2. **DOCTRINA ADMINISTRATIVA** (DGT, AEAT, Seguridad Social) - Criterios interpretativos oficiales
3. **JURISPRUDENCIA** (Tribunales Supremo, Audiencia Nacional, TJUE) - Casos relevantes

**REGLAS OBLIGATORIAS**:
- SIEMPRE cita normativa aplicable PRIMERO si existe
- Doctrina SOLO complementa normativa, NUNCA la contradice
- NUNCA inventes leyes, artículos o casos que no estén en el contexto
- Si no hay información suficiente, admítelo claramente: "No tengo información específica sobre esto"
- Usa lenguaje claro y ejemplos relevantes para artistas

**FORMATO DE RESPUESTA (markdown)**:

## Resumen
[1-2 párrafos explicando la respuesta de forma clara]

## Normativa aplicable
[Cita leyes y artículos específicos con [Fuente X] al final de cada mención]

## Criterios administrativos
[Si existen, cita DGT/AEAT con [Fuente X]]

## Jurisprudencia relevante
[Solo si existe y es relevante]

## Requisitos y notas
[Qué debe hacer el usuario, documentación necesaria, plazos, etc.]

⚠️ **Advertencia**: Esta información es orientativa. Consulta con un asesor fiscal o legal para tu caso específico.

---

**CONTEXTO NORMATIVA**:
{normativa_text if normativa_text else "[No hay normativa específica en la base de datos]"}

**CONTEXTO DOCTRINA ADMINISTRATIVA**:
{doctrina_text if doctrina_text else "[No hay doctrina administrativa en la base de datos]"}

**CONTEXTO JURISPRUDENCIA**:
{juris_text if juris_text else "[No hay jurisprudencia en la base de datos]"}

---

**PREGUNTA DEL USUARIO**: {query}

Responde siguiendo ESTRICTAMENTE la jerarquía de fuentes y el formato indicado.
"""

        return prompt

    def _format_chunks_for_prompt(self, chunks: List[Dict], category: str) -> str:
        """Format chunks for LLM context"""
        if not chunks:
            return ""

        formatted = []
        for idx, chunk in enumerate(chunks, 1):
            metadata = chunk.get('metadata', {})
            formatted.append(f"""
[Fuente {category[0]}{idx}]
Título: {metadata.get('doc_title', 'N/A')}
Tipo: {metadata.get('nivel_autoridad', metadata.get('tipo', 'N/A'))}
Referencia: {chunk.get('chunk_label', 'N/A')}
Texto:
{chunk.get('chunk_text', '')[:1000]}
---
""")

        return "\n".join(formatted)

    def _format_sources(self, sources: Dict) -> List[Dict]:
        """Format sources for frontend display"""
        formatted = []

        # Normativa
        for idx, chunk in enumerate(sources['normativa'], 1):
            formatted.append(self._format_single_source(chunk, 'normativa', idx))

        # Doctrina
        for idx, chunk in enumerate(sources['doctrina'], 1):
            formatted.append(self._format_single_source(chunk, 'doctrina', idx))

        # Jurisprudencia
        for idx, chunk in enumerate(sources['jurisprudencia'], 1):
            formatted.append(self._format_single_source(chunk, 'jurisprudencia', idx))

        return formatted

    def _format_single_source(self, chunk: Dict, category: str, idx: int) -> Dict:
        """Format a single source for display"""
        metadata = chunk.get('metadata', {})

        return {
            'id': str(chunk['id']),
            'category': category,
            'label': chunk.get('chunk_label', 'Sin etiqueta'),
            'text': chunk.get('chunk_text', '')[:500] + '...',  # Truncate for display
            'full_text': chunk.get('chunk_text', ''),
            'doc_title': metadata.get('doc_title', 'N/A'),
            'doc_id_oficial': metadata.get('doc_id_oficial', 'N/A'),
            'url': metadata.get('url', ''),
            'tipo': metadata.get('tipo', 'N/A'),
            'nivel_autoridad': metadata.get('nivel_autoridad', 'N/A'),
            'naturaleza': metadata.get('naturaleza', 'N/A'),
            'similarity': chunk.get('similarity', chunk.get('rrf_score', 0)),
            'reference_label': f"{category[0].upper()}{idx}"  # N1, D1, J1
        }

    def _fallback_answer(self, sources: Dict) -> str:
        """Generate fallback answer if LLM fails"""
        source_count = (
            len(sources['normativa']) +
            len(sources['doctrina']) +
            len(sources['jurisprudencia'])
        )

        return f"""## Información encontrada

He encontrado {source_count} fuentes relevantes para tu consulta. Sin embargo, no puedo generar una respuesta estructurada en este momento.

Por favor, revisa las fuentes citadas a continuación.

⚠️ **Advertencia**: Consulta con un asesor fiscal o legal para tu caso específico.
"""
```

---

## 5. Prompt Engineering Best Practices

### 5.1 Legal Hierarchy Prompting

**Key Principle**: LLM must respect legal authority order

```python
HIERARCHY_INSTRUCTION = """
**JERARQUÍA DE FUENTES**:
1. Constitución > Ley > Real Decreto > Orden
2. Normativa > Doctrina > Jurisprudencia

Si hay conflicto entre fuentes:
- Constitución prevalece sobre todo
- Ley prevalece sobre Decreto
- Normativa prevalece sobre Doctrina

NUNCA uses doctrina para contradecir normativa.
"""
```

### 5.2 Citation Enforcement

```python
CITATION_INSTRUCTION = """
**REGLAS DE CITACIÓN**:
- Cada afirmación legal DEBE tener [Fuente X]
- Formato: "Según el Artículo 30 de la Ley IRPF [Fuente N1]..."
- Si no hay fuente, di: "No tengo información sobre esto"
"""
```

### 5.3 Hallucination Prevention

```python
ANTI_HALLUCINATION = """
**PROHIBIDO INVENTAR**:
❌ NO inventes leyes que no están en el contexto
❌ NO inventes artículos o números
❌ NO generalices sin fuente

✅ SI no sabes, admítelo
✅ SI la información es parcial, indícalo
✅ SI necesitas contexto adicional, pídelo
"""
```

---

## 6. Testing Retrieval Quality

### 6.1 Test Queries for MVP

```python
# apps/legal_graphrag/tests/test_retrieval.py

import pytest
from apps.legal_graphrag.services.legal_rag_engine import LegalRAGEngine

@pytest.fixture
def rag_engine():
    return LegalRAGEngine()

class TestRetrievalQuality:
    """Test retrieval accuracy for common artist queries"""

    def test_fiscal_query_deducibles(self, rag_engine):
        """Test: Deductible expenses for home studio"""
        query = "¿Puedo deducir gastos de mi home studio como artista?"

        result = rag_engine.answer_query(query)

        # Assertions
        assert result['metadata']['area_principal'] == 'Fiscal'
        assert len(result['sources']) > 0

        # Check that Ley IRPF is retrieved
        source_titles = [s['doc_title'] for s in result['sources']]
        assert any('IRPF' in title for title in source_titles)

        # Check answer contains key terms
        answer_lower = result['answer'].lower()
        assert 'gastos deducibles' in answer_lower or 'deducir' in answer_lower

    def test_laboral_query_autonomo(self, rag_engine):
        """Test: Autónomo registration"""
        query = "¿Cómo me doy de alta como autónomo siendo artista?"

        result = rag_engine.answer_query(query)

        assert result['metadata']['area_principal'] == 'Laboral'
        assert len(result['sources']) > 0

    def test_ip_query_derechos(self, rag_engine):
        """Test: Copyright registration"""
        query = "¿Cómo registro mis derechos de autor en España?"

        result = rag_engine.answer_query(query)

        assert result['metadata']['area_principal'] == 'Propiedad Intelectual'
        assert len(result['sources']) > 0

    def test_empty_result_handling(self, rag_engine):
        """Test: Query with no matching sources"""
        query = "¿Cómo tributan los NFTs de arte digital espacial?"

        result = rag_engine.answer_query(query)

        # Should still return structure, but admit lack of info
        assert 'No tengo información' in result['answer'] or \
               'No he encontrado' in result['answer']
```

### 6.2 Retrieval Metrics

```python
# apps/legal_graphrag/management/commands/evaluate_retrieval.py

from django.core.management.base import BaseCommand
from apps.legal_graphrag.services.legal_rag_engine import LegalRAGEngine

class Command(BaseCommand):
    help = 'Evaluate retrieval quality on test set'

    def handle(self, *args, **options):
        rag_engine = LegalRAGEngine()

        # Test queries with expected sources
        test_cases = [
            {
                'query': '¿Puedo deducir gastos de home studio?',
                'expected_sources': ['BOE-A-2006-20764'],  # Ley IRPF
                'area': 'Fiscal'
            },
            {
                'query': '¿Cómo me doy de alta como autónomo?',
                'expected_sources': ['BOE-A-2015-11724'],  # Ley Autónomos
                'area': 'Laboral'
            },
            # Add more test cases
        ]

        metrics = {
            'total': len(test_cases),
            'correct_area': 0,
            'source_recall': [],
            'avg_sources': 0
        }

        for test in test_cases:
            result = rag_engine.answer_query(test['query'])

            # Check area classification
            if result['metadata']['area_principal'] == test['area']:
                metrics['correct_area'] += 1

            # Check source recall
            retrieved_ids = [s['doc_id_oficial'] for s in result['sources']]
            recall = sum(1 for exp in test['expected_sources'] if exp in retrieved_ids)
            recall_pct = recall / len(test['expected_sources']) if test['expected_sources'] else 0
            metrics['source_recall'].append(recall_pct)

            # Count sources
            metrics['avg_sources'] += len(result['sources'])

            self.stdout.write(f"Query: {test['query'][:50]}...")
            self.stdout.write(f"  Area: {result['metadata']['area_principal']} (expected: {test['area']})")
            self.stdout.write(f"  Recall: {recall_pct:.2%}")
            self.stdout.write("")

        # Summary
        metrics['area_accuracy'] = metrics['correct_area'] / metrics['total']
        metrics['avg_recall'] = sum(metrics['source_recall']) / len(metrics['source_recall'])
        metrics['avg_sources'] /= metrics['total']

        self.stdout.write(self.style.SUCCESS("\n=== RETRIEVAL METRICS ==="))
        self.stdout.write(f"Area Classification Accuracy: {metrics['area_accuracy']:.2%}")
        self.stdout.write(f"Average Source Recall: {metrics['avg_recall']:.2%}")
        self.stdout.write(f"Average Sources Retrieved: {metrics['avg_sources']:.1f}")
```

---

## 7. Advanced Retrieval Techniques (Post-MVP)

### 7.1 Query Expansion

```python
def expand_query(query: str) -> str:
    """
    Expand query with synonyms and related terms

    Example:
    "gastos deducibles" → "gastos deducibles deducción fiscalmente"
    """
    synonyms = {
        'gastos': ['gastos', 'costes', 'costos', 'erogaciones'],
        'deducibles': ['deducibles', 'deducción', 'deducir'],
        'autónomo': ['autónomo', 'trabajador por cuenta propia', 'freelance'],
    }

    # Simple synonym expansion (MVP uses keywords as-is)
    expanded_terms = []
    for word in query.split():
        if word in synonyms:
            expanded_terms.extend(synonyms[word])
        else:
            expanded_terms.append(word)

    return ' '.join(expanded_terms)
```

### 7.2 Cross-Encoder Reranking

```python
# Post-MVP: Use cross-encoder for better reranking

from sentence_transformers import CrossEncoder

class AdvancedReranker:
    def __init__(self):
        # Fine-tuned on legal question-answer pairs
        self.model = CrossEncoder('legal-cross-encoder-es')

    def rerank(self, query: str, results: List[Dict]) -> List[Dict]:
        """Rerank using cross-encoder"""
        pairs = [[query, r['chunk_text']] for r in results]
        scores = self.model.predict(pairs)

        for result, score in zip(results, scores):
            result['cross_encoder_score'] = score

        results.sort(key=lambda x: x['cross_encoder_score'], reverse=True)
        return results
```

### 7.3 Graph-Based Retrieval

```python
# Post-MVP: Citation graph traversal

def retrieve_with_citations(query: str, initial_results: List[Dict]) -> List[Dict]:
    """
    Expand retrieval by following citations

    Example:
    User asks about "mecenazgo"
    → Retrieve Ley 49/2002 (mecenazgo law)
    → Follow citations to Ley IRPF (tax deductions)
    → Follow citations to DGT rulings (interpretations)
    """
    expanded_results = initial_results.copy()

    for result in initial_results:
        # Extract citations from metadata
        citations = result.get('metadata', {}).get('cites', [])

        # Retrieve cited documents
        for citation_id in citations[:3]:  # Limit to 3 citations
            cited_doc = DocumentChunk.objects.filter(
                metadata__doc_id_oficial=citation_id
            ).first()

            if cited_doc:
                expanded_results.append(cited_doc)

    return expanded_results
```

---

## 8. Performance Optimization

### 8.1 Query Caching

```python
from django.core.cache import cache
import hashlib

def cached_search(query: str, filters: Dict) -> List[Dict]:
    """Cache search results for identical queries"""
    cache_key = f"search:{hashlib.md5((query + str(filters)).encode()).hexdigest()}"

    cached = cache.get(cache_key)
    if cached:
        return cached

    results = search_engine.hybrid_search(query, filters)

    # Cache for 1 hour
    cache.set(cache_key, results, timeout=3600)

    return results
```

### 8.2 Batch Embedding

```python
# Embed multiple queries in batch for efficiency
def embed_queries_batch(queries: List[str]) -> List[List[float]]:
    """Batch embed queries (more efficient than one-by-one)"""
    # Gemini API supports batch requests
    results = genai.embed_content(
        model='models/text-embedding-004',
        content=queries
    )

    return [r['embedding'] for r in results['embeddings']]
```

---

**Document End** | Next: [05_API_SPECIFICATION.md](./05_API_SPECIFICATION.md)
