"""
Legal RAG Engine
Orchestrates the entire RAG pipeline: intent classification → hierarchical search → LLM answer generation
"""

import logging
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from django.conf import settings

from apps.legal_graphrag.services.legal_search_engine import LegalSearchEngine
from apps.legal_graphrag.services.intent_classifier import IntentClassifier

logger = logging.getLogger(__name__)


class LegalRAGEngine:
    """
    End-to-end RAG pipeline for legal question answering.

    Pipeline:
    1. Classify user query intent (area_principal)
    2. Retrieve hierarchical sources (normativa → doctrina → jurisprudencia)
    3. Build hierarchical prompt with legal context
    4. Generate answer using Gemini LLM
    5. Format response with citations
    """

    def __init__(self):
        self.search_engine = LegalSearchEngine()
        self.intent_classifier = IntentClassifier()

        # Configure Gemini API
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(
            model_name=getattr(settings, 'GEMINI_CHAT_MODEL', 'gemini-2.5-flash')
        )

    def answer_query(
        self,
        query: str,
        area_principal: Optional[str] = None,
        max_sources: int = 10
    ) -> Dict[str, Any]:
        """
        Generate a complete answer to a legal query.

        Args:
            query: User's legal question
            area_principal: Optional pre-classified area (if None, will auto-classify)
            max_sources: Maximum number of sources to retrieve

        Returns:
            Dictionary with:
            - answer: Markdown-formatted answer
            - sources: List of source citations
            - metadata: Query metadata (area, model, timing, etc.)
        """
        logger.info(f"RAG query: '{query[:100]}'")

        # Step 1: Classify intent
        if area_principal is None:
            area_classification = self.intent_classifier.classify_with_confidence(query)
            area_principal = area_classification.get('area')
            confidence = area_classification.get('confidence', 0.0)
            logger.info(f"Classified as '{area_principal}' (confidence: {confidence:.2f})")
        else:
            logger.info(f"Using pre-classified area: '{area_principal}'")

        # Step 2: Hierarchical search
        sources = self._retrieve_hierarchical_sources(
            query=query,
            area_principal=area_principal,
            max_sources=max_sources
        )

        # Step 3: Build prompt
        prompt = self._build_hierarchical_prompt(
            query=query,
            sources=sources,
            area_principal=area_principal
        )

        # Step 4: Generate answer
        try:
            response = self.model.generate_content(prompt)
            answer_text = response.text
            logger.info(f"LLM response generated ({len(answer_text)} chars)")
        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}")
            answer_text = self._generate_fallback_answer(query, sources)

        # Step 5: Format response
        formatted_sources = self._format_sources(sources)

        return {
            'answer': answer_text,
            'sources': formatted_sources,
            'metadata': {
                'area_principal': area_principal,
                'model': self.model.model_name,
                'normativa_count': len(sources.get('normativa', [])),
                'doctrina_count': len(sources.get('doctrina', [])),
                'jurisprudencia_count': len(sources.get('jurisprudencia', [])),
                'total_sources': len(formatted_sources),
            }
        }

    def _retrieve_hierarchical_sources(
        self,
        query: str,
        area_principal: Optional[str],
        max_sources: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve sources respecting legal hierarchy:
        1. Normativa P1 (laws, decrees)
        2. Doctrina P1 (administrative guidance)
        3. Jurisprudencia P1/P2 (case law)

        OPTIMIZED: Runs ONE hybrid search and filters results by naturaleza,
        instead of running 3 separate searches (6x faster!)
        """
        sources = {
            'normativa': [],
            'doctrina': [],
            'jurisprudencia': []
        }

        # Run ONE hybrid search to get all relevant sources
        # This is 3x faster than running 3 separate hybrid searches
        try:
            all_results = self.search_engine.hybrid_search(
                query=query,
                limit=max_sources * 2  # Get more results to ensure we have enough after filtering
            )

            # Filter results by naturaleza (hierarchical sorting)
            for result in all_results:
                naturaleza = result.get('source_naturaleza', '')

                if naturaleza == 'Normativa' and len(sources['normativa']) < 5:
                    sources['normativa'].append(result)
                elif naturaleza == 'Doctrina administrativa' and len(sources['doctrina']) < 3:
                    sources['doctrina'].append(result)
                elif naturaleza == 'Jurisprudencia' and len(sources['jurisprudencia']) < 2:
                    sources['jurisprudencia'].append(result)

                # Stop if we have enough sources
                total = len(sources['normativa']) + len(sources['doctrina']) + len(sources['jurisprudencia'])
                if total >= max_sources:
                    break

            logger.info(
                f"Retrieved {len(sources['normativa'])} normativa, "
                f"{len(sources['doctrina'])} doctrina, "
                f"{len(sources['jurisprudencia'])} jurisprudencia sources"
            )

        except Exception as e:
            logger.error(f"Hierarchical search failed: {str(e)}")

        return sources

    def _build_hierarchical_prompt(
        self,
        query: str,
        sources: Dict[str, List[Dict[str, Any]]],
        area_principal: Optional[str]
    ) -> str:
        """
        Build a hierarchical prompt that respects legal authority.

        Prompt structure:
        1. System instructions (hierarchy rules)
        2. Context: Normativa (highest authority)
        3. Context: Doctrina administrativa
        4. Context: Jurisprudencia
        5. User query
        6. Response format instructions
        """
        # Format context sections
        normativa_context = self._format_context_section(
            sources.get('normativa', []),
            section_title="NORMATIVA (Leyes, Reales Decretos, Órdenes)"
        )

        doctrina_context = self._format_context_section(
            sources.get('doctrina', []),
            section_title="DOCTRINA ADMINISTRATIVA (DGT, AEAT, Seguridad Social)"
        )

        jurisprudencia_context = self._format_context_section(
            sources.get('jurisprudencia', []),
            section_title="JURISPRUDENCIA (Tribunal Supremo, TJUE, TEDH)"
        )

        # Build full prompt
        prompt = f"""Eres un asistente legal especializado en ayudar a artistas y profesionales culturales en España.

**JERARQUÍA DE FUENTES LEGALES (orden de importancia)**:
1. NORMATIVA (Constitución, Leyes, Reales Decretos, Órdenes) - **MÁXIMA AUTORIDAD**
2. DOCTRINA ADMINISTRATIVA (DGT, AEAT, Seguridad Social) - Criterios interpretativos vinculantes
3. JURISPRUDENCIA (Tribunal Supremo, Audiencia Nacional, TJUE) - Casos relevantes

**REGLAS OBLIGATORIAS**:
- Si hay NORMATIVA aplicable, SIEMPRE cítala PRIMERO en tu respuesta
- La Doctrina administrativa solo COMPLEMENTA la normativa, nunca la contradice
- La Jurisprudencia se usa para casos específicos o lagunas legales
- NUNCA inventes artículos, leyes, o sentencias que no aparezcan en el contexto
- Si no hay información suficiente en el contexto, di: "No tengo información específica sobre esto en las fuentes legales disponibles"
- SIEMPRE incluye citas específicas: [Fuente: Ley X, Artículo Y]

**FORMATO DE RESPUESTA OBLIGATORIO (tono conversacional, sin encabezado de resumen)**:
- **Normativa aplicable**: cita artículos concretos y explica brevemente.
- **Criterios administrativos**: solo si hay DGT/AEAT/Seguridad Social relevantes.
- **Jurisprudencia relevante**: solo si aplica.
- **Requisitos y notas**: pasos concretos o advertencias para el usuario.

---

**CONTEXTO NORMATIVO**:
{normativa_context}

**CONTEXTO DE DOCTRINA ADMINISTRATIVA**:
{doctrina_context}

**CONTEXTO JURISPRUDENCIAL**:
{jurisprudencia_context}

---

**Área legal**: {area_principal or 'No clasificada'}

**Pregunta del usuario**: {query}

---

**Genera tu respuesta siguiendo ESTRICTAMENTE el formato indicado arriba. Al final, incluye esta advertencia**:

⚠️ **Importante**: Esta información es orientativa y basada en fuentes oficiales. Para decisiones específicas sobre tu situación particular, consulta siempre con un asesor fiscal o legal colegiado.
"""

        return prompt

    def _format_context_section(
        self,
        chunks: List[Dict[str, Any]],
        section_title: str
    ) -> str:
        """
        Format a list of chunks into a context section for the prompt.
        """
        if not chunks:
            return f"{section_title}:\n(No se encontraron fuentes relevantes en esta categoría)\n"

        context_lines = [f"{section_title}:"]

        for idx, chunk in enumerate(chunks, 1):
            chunk_label = chunk.get('chunk_label', 'Sin etiqueta')
            chunk_text = chunk.get('chunk_text', '')
            doc_title = chunk.get('document_title', 'Documento sin título')
            doc_id = chunk.get('document_id', 'Sin ID')

            context_lines.append(f"\n[Fuente {idx}]: {doc_title} - {chunk_label} ({doc_id})")
            context_lines.append(f"{chunk_text[:800]}...")  # Limit chunk length

        return '\n'.join(context_lines)

    def _format_sources(
        self,
        sources: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Format sources for API response.
        Maps internal fields to frontend-expected fields:
        - id: document_id
        - title: document_title
        - url: document_url
        - source_type: source_naturaleza
        - relevance_score: similarity/rrf_score
        - excerpt: chunk_text
        """
        formatted = []

        for naturaleza, chunks in sources.items():
            for chunk in chunks:
                formatted.append({
                    # Frontend-expected fields
                    'id': chunk.get('document_id', ''),
                    'title': chunk.get('document_title', ''),
                    'url': chunk.get('document_url', ''),
                    'source_type': chunk.get('source_naturaleza', ''),
                    'relevance_score': chunk.get('similarity', chunk.get('rrf_score', 0)),
                    'excerpt': chunk.get('chunk_text', '')[:300],  # Limit excerpt length

                    # Additional metadata (kept for backward compatibility)
                    'label': chunk.get('chunk_label', chunk.get('chunk_type', 'Sin etiqueta')),
                    'source_title': chunk.get('source_title', ''),
                    'source_priority': chunk.get('source_priority', ''),
                    'chunk_type': chunk.get('chunk_type', ''),
                })

        return formatted

    def _generate_fallback_answer(
        self,
        query: str,
        sources: Dict[str, List[Dict[str, Any]]]
    ) -> str:
        """
        Generate a fallback answer if LLM fails.
        """
        total_sources = sum(len(chunks) for chunks in sources.values())

        if total_sources == 0:
            return f"""**Normativa aplicable**
No he encontrado información específica en las fuentes legales disponibles para responder a tu pregunta: "{query}"

**Requisitos y notas**
- Reformula la pregunta con términos más específicos.
- Consulta con un asesor fiscal o legal colegiado.
- Revisa el BOE o fuentes oficiales directamente.

⚠️ **Importante**: Esta respuesta es limitada. Para decisiones específicas sobre tu situación, consulta siempre con un profesional legal.
"""

        # If we have sources but LLM failed, provide basic source listing
        source_list = []
        for naturaleza, chunks in sources.items():
            for chunk in chunks[:3]:  # Limit to top 3 per category
                doc_title = chunk.get('document_title', '')
                chunk_label = chunk.get('chunk_label', '')
                source_list.append(f"- {doc_title}: {chunk_label}")

        return f"""**Normativa aplicable**
He encontrado fuentes relevantes para tu pregunta: "{query}", pero hubo un error al generar la respuesta completa.

**Fuentes encontradas**

{chr(10).join(source_list)}

**Requisitos y notas**
- Revisa las fuentes citadas arriba.
- Consulta con un asesor fiscal o legal para obtener una respuesta específica a tu caso.

⚠️ **Importante**: Disculpa las molestias. Te recomiendo consultar con un profesional legal para obtener asesoramiento preciso.
"""
