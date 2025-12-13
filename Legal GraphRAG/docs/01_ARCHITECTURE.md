# Legal GraphRAG System - Architecture

## Document Information
- **Version**: 1.0 (MVP)
- **Last Updated**: 2025-12-11
- **Status**: Planning Phase
- **Related**: [00_OVERVIEW.md](./00_OVERVIEW.md) | [02_DATA_MODEL.md](./02_DATA_MODEL.md)

---

## 1. System Architecture Overview

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│  Web Browser (Desktop/Mobile)                                   │
│  - legal.artisting.es (initial)                                 │
│  - artisting.es/legal-chat (future integration)                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTPS
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│  Next.js 15 + React 19 + TypeScript                            │
│  - Auth Context (shared with grants)                            │
│  - Legal Chat Interface                                          │
│  - Document Search UI                                            │
│  - Citation Display Components                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓ REST API (JWT)
┌─────────────────────────────────────────────────────────────────┐
│                    API GATEWAY LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│  Django 5 + Django REST Framework                               │
│  - /api/v1/auth/*          (shared - existing)                  │
│  - /api/v1/billing/*       (shared - existing)                  │
│  - /api/v1/legal-graphrag/* (NEW)                               │
│    ├── POST /search        (legal document search)              │
│    ├── POST /chat          (conversational Q&A)                 │
│    ├── GET /{id}           (document details)                   │
│    └── GET /sources        (list corpus sources)                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    SERVICE LAYER                                 │
├─────────────────────────────────────────────────────────────────┤
│  apps/legal_graphrag/services/                                  │
│  ┌──────────────────┐  ┌─────────────────┐  ┌────────────────┐│
│  │ Legal Search     │  │ Legal RAG       │  │ Embedding      ││
│  │ Engine           │  │ Engine          │  │ Service        ││
│  │                  │  │                 │  │                ││
│  │ - Hybrid search  │  │ - Query intent  │  │ - Gemini API   ││
│  │ - Filter by area │  │ - Retrieve docs │  │ - Generate     ││
│  │ - Rerank by      │  │ - LLM prompt    │  │   embeddings   ││
│  │   authority      │  │ - Citation      │  │ - Cache        ││
│  └──────────────────┘  └─────────────────┘  └────────────────┘│
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              INGESTION SERVICES                           │  │
│  │  (Async Celery Tasks)                                    │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ BOE Connector    │ DOUE Connector   │ Citation Extractor│  │
│  │ DGT Connector    │ Normalizer       │ Parser            │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                    │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL (Digital Ocean) + pgvector                          │
│  ┌──────────────────┐  ┌─────────────────┐  ┌────────────────┐│
│  │ Shared Tables    │  │ Legal GraphRAG  │  │ Vector Index   ││
│  │ (Existing)       │  │ Tables (NEW)    │  │ (NEW)          ││
│  │                  │  │                 │  │                ││
│  │ - auth_user      │  │ - legal_corpus_ │  │ - ivfflat on   ││
│  │ - billing_       │  │   sources       │  │   embeddings   ││
│  │   subscription   │  │ - legal_        │  │ - cosine       ││
│  │ - users_         │  │   documents     │  │   similarity   ││
│  │   userprofile    │  │ - legal_        │  │                ││
│  │                  │  │   document_     │  │                ││
│  │                  │  │   chunks        │  │                ││
│  │                  │  │ - legal_chat_   │  │                ││
│  │                  │  │   sessions      │  │                ││
│  └──────────────────┘  └─────────────────┘  └────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                 EXTERNAL SERVICES                                │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ Gemini API   │  │ Celery +     │  │ Stripe API           │ │
│  │ (Google AI)  │  │ Redis        │  │ (Shared)             │ │
│  │              │  │              │  │                      │ │
│  │ - Embeddings │  │ - Async      │  │ - Subscriptions      │ │
│  │ - Chat LLM   │  │   ingestion  │  │ - Credit billing     │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Technology Stack

### 2.1 Frontend

| Component | Technology | Version | Justification |
|-----------|-----------|---------|---------------|
| **Framework** | Next.js | 15.x | App Router, SSR, proven in grants app |
| **UI Library** | React | 19.x | Component-based, TypeScript support |
| **Language** | TypeScript | 5.x | Type safety, better DX |
| **Styling** | Tailwind CSS | 3.x | Utility-first, consistent with grants |
| **Component Kit** | Radix UI | Latest | Accessible, headless components |
| **State Management** | React Context | Built-in | Simple, sufficient for MVP |
| **Forms** | react-hook-form | 7.x | Performant, validation with Zod |
| **HTTP Client** | Fetch API | Native | Built-in, no extra dependencies |
| **Icons** | Lucide React | Latest | Clean, consistent icons |

**Key Files**:
```
frontend-legal/
├── app/
│   ├── layout.tsx                 # Root with AuthProvider
│   ├── chat/page.tsx              # Main chat interface
│   └── search/page.tsx            # Document search
├── components/legal/
│   ├── LegalChatInterface.tsx
│   ├── CitationCard.tsx
│   └── LegalSearchForm.tsx
├── contexts/
│   └── auth-context.tsx           # Shared auth (copy from grants)
└── lib/services/
    ├── legal-chat.service.ts
    └── config.ts
```

### 2.2 Backend

| Component | Technology | Version | Justification |
|-----------|-----------|---------|---------------|
| **Framework** | Django | 5.2 | Existing stack, mature ORM |
| **API Framework** | Django REST Framework | 3.x | Standard, well-documented |
| **Authentication** | djangorestframework-simplejwt | 5.x | Already configured, token-based |
| **Database ORM** | Django ORM | Built-in | Sufficient for relational data |
| **Async Jobs** | Celery | 5.x | Already configured, proven |
| **Task Broker** | Redis | 7.x | Fast, already in use |
| **CORS** | django-cors-headers | 4.x | Already configured |

**Key Files**:
```
backend/apps/legal_graphrag/
├── models.py                      # Django models
├── views.py                       # DRF ViewSets
├── serializers.py                 # Request/response serialization
├── urls.py                        # API routes
├── admin.py                       # Django admin interface
├── router.py                      # Database router
├── tasks.py                       # Celery tasks
└── services/
    ├── legal_search_engine.py
    ├── legal_rag_engine.py
    ├── embedding_service.py
    └── ingestion/
        ├── boe_connector.py
        ├── doue_connector.py
        ├── normalizer.py
        └── parser.py
```

### 2.3 Database & Search

| Component | Technology | Version | Justification |
|-----------|-----------|---------|---------------|
| **Primary Database** | PostgreSQL | 15.x | Existing Digital Ocean instance |
| **Vector Extension** | pgvector | 0.5.x | Native PG extension, simple setup |
| **Full-Text Search** | PostgreSQL FTS | Built-in | GIN indexes, sufficient for MVP |
| **Connection Pooling** | Django DB pool | Built-in | Handles 100+ concurrent queries |

**Why NOT OpenSearch for MVP**:
- ✅ pgvector handles 70 sources easily
- ✅ PostgreSQL FTS sufficient for lexical search
- ✅ Simpler stack = faster MVP
- ⚠️ OpenSearch added later if needed (1000+ sources)

### 2.4 AI & Embeddings

| Component | Technology | Model | Justification |
|-----------|-----------|-------|---------------|
| **Embeddings** | Gemini API | text-embedding-004 | Free, 768-dim, quality |
| **Chat LLM** | Gemini API | gemini-2.5-flash | Free, fast, function calling |
| **Fallback LLM** | Gemini API | gemini-2.0-flash | Stable, proven |

**Why Gemini over OpenAI**:
- ✅ Free tier (1500 requests/day)
- ✅ Already configured in grants system
- ✅ Good Spanish language support
- ✅ Function calling for structured output

**Embedding Specs**:
```yaml
Model: text-embedding-004
Dimensions: 768
Max Input: 2048 tokens (~8000 chars)
Output: Float32 array
API Endpoint: https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent
```

### 2.5 DevOps & Deployment

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Hosting** | Digital Ocean App Platform | Django + Next.js deployment |
| **Database** | Digital Ocean Managed PostgreSQL | Existing instance |
| **SSL/TLS** | Let's Encrypt (auto) | HTTPS |
| **CI/CD** | Digital Ocean Auto-Deploy | Git push → deploy |
| **Monitoring** | Django Prometheus (existing) | Metrics |
| **Logging** | Django logging | Error tracking |

**Environment Variables** (see `.env`):
```bash
# Database (existing)
DATABASES[default] → Digital Ocean PostgreSQL

# AI
GEMINI_API_KEY=AIzaSy...
GEMINI_CHAT_MODEL=gemini-2.5-flash

# Celery & Redis (DB index 1 to avoid conflicts with other projects)
REDIS_URL=redis://localhost:6379/1
CELERY_BROKER_URL=redis://localhost:6379/1

# Auth (shared)
SECRET_KEY=...
SIMPLE_JWT settings (already configured)

# Billing (shared)
STRIPE_SECRET_KEY=...
```

---

## 3. Component Architecture

### 3.1 Django App Structure

**New App**: `apps/legal_graphrag`

```python
# apps/legal_graphrag/apps.py
from django.apps import AppConfig

class LegalGraphragConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.legal_graphrag'
    verbose_name = 'Legal GraphRAG'
```

**Database Router**:
```python
# apps/legal_graphrag/router.py
class LegalGraphRAGRouter:
    """
    Route legal_graphrag models to 'default' database
    (all in same DB for simplicity)
    """
    route_app_labels = {'legal_graphrag'}

    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'legal_graphrag':
            return 'default'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'legal_graphrag':
            return 'default'
        return None
```

**Settings Update**:
```python
# backend/ovra_backend/settings.py

INSTALLED_APPS = [
    # ... existing apps
    'apps.grants',
    'apps.legal_graphrag',  # NEW
]

DATABASE_ROUTERS = [
    'apps.grants.router.GrantsRouter',
    'apps.legal_graphrag.router.LegalGraphRAGRouter',  # NEW
]
```

### 3.2 API Layer (Django REST Framework)

**URL Configuration**:
```python
# backend/ovra_backend/urls.py
from django.urls import path, include

urlpatterns = [
    # Existing routes
    path('api/v1/auth/', include('users.urls')),
    path('api/v1/billing/', include('billing.urls')),
    path('api/v1/grants/', include('apps.grants.urls')),

    # NEW: Legal GraphRAG routes
    path('api/v1/legal-graphrag/', include('apps.legal_graphrag.urls')),
]
```

**Legal GraphRAG URLs**:
```python
# apps/legal_graphrag/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.LegalSearchView.as_view(), name='legal-search'),
    path('chat/', views.LegalChatView.as_view(), name='legal-chat'),
    path('documents/<uuid:doc_id>/', views.LegalDocumentDetailView.as_view()),
    path('sources/', views.CorpusSourceListView.as_view()),
]
```

**View Structure**:
```python
# apps/legal_graphrag/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny  # or IsAuthenticated
from .services.legal_search_engine import LegalSearchEngine
from .services.legal_rag_engine import LegalRAGEngine

class LegalChatView(APIView):
    permission_classes = [AllowAny]  # MVP: no auth required

    def post(self, request):
        """
        POST /api/v1/legal-graphrag/chat/
        Body: {"query": "¿Puedo deducir gastos de home studio?"}
        """
        query = request.data.get('query')

        # Orchestrate: search → retrieve → LLM → format
        rag_engine = LegalRAGEngine()
        result = rag_engine.answer_query(query)

        return Response({
            'answer': result['answer'],
            'sources': result['sources'],
            'metadata': result['metadata']
        })
```

### 3.3 Service Layer Architecture

**Principle**: Service classes handle business logic, views are thin orchestrators.

**Legal Search Engine**:
```python
# apps/legal_graphrag/services/legal_search_engine.py

class LegalSearchEngine:
    def __init__(self):
        self.embedding_service = EmbeddingService()

    def hybrid_search(
        self,
        query: str,
        filters: dict = None,
        limit: int = 5
    ) -> List[dict]:
        """
        Hybrid search: semantic (pgvector) + lexical (PG FTS)
        Returns ranked document chunks
        """
        # 1. Generate query embedding
        query_embedding = self.embedding_service.embed(query)

        # 2. Vector search
        vector_results = self._vector_search(query_embedding, filters, limit * 2)

        # 3. Lexical search (full-text)
        lexical_results = self._lexical_search(query, filters, limit * 2)

        # 4. Merge and rerank (RRF - Reciprocal Rank Fusion)
        merged = self._merge_results(vector_results, lexical_results)

        # 5. Rerank by legal authority
        reranked = self._rerank_by_authority(merged)

        return reranked[:limit]

    def search_by_hierarchy(
        self,
        query: str,
        area_principal: str = None
    ) -> dict:
        """
        Search respecting legal hierarchy:
        1. Normativa P1 first
        2. Doctrina P1 second
        3. Jurisprudencia P1/P2 last
        """
        results = {
            'normativa': [],
            'doctrina': [],
            'jurisprudencia': []
        }

        # Search Normativa
        results['normativa'] = self.hybrid_search(
            query,
            filters={'naturaleza': 'Normativa', 'prioridad': 'P1'},
            limit=5
        )

        # Search Doctrina (if relevant norms found)
        if results['normativa']:
            results['doctrina'] = self.hybrid_search(
                query,
                filters={'naturaleza': 'Doctrina administrativa'},
                limit=3
            )

        # Search Jurisprudencia (optional)
        results['jurisprudencia'] = self.hybrid_search(
            query,
            filters={'naturaleza': 'Jurisprudencia'},
            limit=2
        )

        return results
```

**Legal RAG Engine**:
```python
# apps/legal_graphrag/services/legal_rag_engine.py
import google.generativeai as genai
from django.conf import settings

class LegalRAGEngine:
    def __init__(self):
        self.search_engine = LegalSearchEngine()
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_CHAT_MODEL)

    def answer_query(self, query: str) -> dict:
        """
        End-to-end RAG pipeline:
        1. Classify intent (area_principal)
        2. Retrieve hierarchical sources
        3. Generate answer with LLM
        4. Format with citations
        """
        # 1. Intent classification (simple keyword matching for MVP)
        area = self._classify_area(query)

        # 2. Hierarchical search
        sources = self.search_engine.search_by_hierarchy(query, area)

        # 3. Build LLM prompt
        prompt = self._build_prompt(query, sources)

        # 4. Generate answer
        response = self.model.generate_content(prompt)

        # 5. Format response
        return {
            'answer': response.text,
            'sources': self._format_sources(sources),
            'metadata': {
                'area_principal': area,
                'model': settings.GEMINI_CHAT_MODEL,
                'normativa_count': len(sources['normativa']),
                'doctrina_count': len(sources['doctrina']),
            }
        }

    def _build_prompt(self, query: str, sources: dict) -> str:
        """Build LLM prompt with legal hierarchy"""
        normativa_text = self._format_chunks(sources['normativa'])
        doctrina_text = self._format_chunks(sources['doctrina'])
        juris_text = self._format_chunks(sources['jurisprudencia'])

        return f"""Eres un asistente legal para artistas en España.

**JERARQUÍA DE FUENTES (orden de importancia)**:
1. NORMATIVA (leyes, RD, órdenes) - Máxima autoridad
2. DOCTRINA ADMINISTRATIVA (DGT, AEAT, SS) - Criterios interpretativos
3. JURISPRUDENCIA (TS, AN, TJUE) - Casos relevantes

**REGLAS OBLIGATORIAS**:
- Si hay NORMATIVA aplicable, cítala PRIMERO
- Doctrina solo complementa la normativa, no la contradice
- NUNCA inventes artículos o leyes
- Si no hay información suficiente, di: "No tengo información específica sobre esto"

**FORMATO DE RESPUESTA**:
1. Resumen ejecutivo (1-2 párrafos)
2. Normativa aplicable (citar artículos específicos con [Fuente])
3. Criterios administrativos (DGT, AEAT, etc.)
4. Jurisprudencia relevante (solo si existe)
5. Requisitos y notas (qué necesita hacer el usuario)

---

**Contexto normativo**:
{normativa_text}

**Contexto de doctrina**:
{doctrina_text}

**Contexto jurisprudencial**:
{juris_text}

---

**Pregunta del usuario**: {query}

Responde siguiendo la jerarquía y formato indicados. Siempre incluye la advertencia:
"⚠️ Esta información es orientativa. Consulta con un asesor fiscal o legal para tu caso específico."
"""
```

### 3.4 Ingestion Pipeline (Celery Tasks)

**Celery Task Structure**:
```python
# apps/legal_graphrag/tasks.py
from celery import shared_task
from .services.ingestion.boe_connector import BOEConnector
from .services.ingestion.normalizer import LegalDocumentNormalizer
from .services.embedding_service import EmbeddingService

@shared_task
def ingest_legal_source(source_id: int):
    """
    Celery task: Fetch, parse, embed, store a legal source
    Can run in background, takes 30s - 5min per source
    """
    from .models import CorpusSource, LegalDocument, DocumentChunk

    # 1. Get source metadata
    source = CorpusSource.objects.get(id=source_id)

    try:
        # 2. Fetch raw document
        connector = get_connector(source.tipo)  # BOE, DOUE, DGT
        raw_doc = connector.fetch(source.url_oficial)

        # 3. Normalize to canonical format
        normalizer = LegalDocumentNormalizer()
        normalized = normalizer.normalize(raw_doc, source)

        # 4. Create document record
        doc = LegalDocument.objects.create(
            source=source,
            doc_title=normalized['titulo'],
            doc_id_oficial=source.id_oficial,
            url=source.url_oficial,
            raw_html=raw_doc['html'],
            metadata=normalized['metadata']
        )

        # 5. Extract and embed chunks (articles)
        embedding_service = EmbeddingService()
        for chunk in normalized['chunks']:
            embedding = embedding_service.embed(chunk['text'])

            DocumentChunk.objects.create(
                document=doc,
                chunk_type=chunk['type'],
                chunk_label=chunk['label'],
                chunk_text=chunk['text'],
                embedding=embedding,
                metadata=chunk['metadata']
            )

        # 6. Update status
        source.estado = 'ingested'
        source.last_ingested_at = timezone.now()
        source.save()

        return f"✓ Ingested source {source_id}: {source.titulo}"

    except Exception as e:
        source.estado = 'failed'
        source.save()
        raise

@shared_task
def ingest_all_p1_sources():
    """Batch task: Ingest all P1 priority sources"""
    from .models import CorpusSource
    p1_sources = CorpusSource.objects.filter(
        prioridad='P1',
        estado='pending'
    )

    for source in p1_sources:
        ingest_legal_source.delay(source.id)
```

**BOE Connector Example**:
```python
# apps/legal_graphrag/services/ingestion/boe_connector.py
import requests
from bs4 import BeautifulSoup

class BOEConnector:
    """Fetches and parses BOE documents"""

    def fetch(self, url: str) -> dict:
        """
        Fetch BOE document from official URL
        Returns: {'html': str, 'metadata': dict}
        """
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract metadata
        metadata = self._extract_metadata(soup)

        # Extract full text
        content = self._extract_content(soup)

        return {
            'html': response.text,
            'content': content,
            'metadata': metadata
        }

    def _extract_metadata(self, soup: BeautifulSoup) -> dict:
        """Extract BOE-specific metadata"""
        return {
            'fecha_publicacion': soup.select_one('.fecha-publicacion').text,
            'seccion': soup.select_one('.seccion').text,
            'departamento': soup.select_one('.departamento').text,
        }

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main legal text"""
        content_div = soup.select_one('#textoBOE')
        return content_div.get_text(separator='\n', strip=True)
```

---

## 4. Data Flow Diagrams

### 4.1 Ingestion Flow (Offline, Async)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. TRIGGER INGESTION                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
         Admin runs: python manage.py ingest_source <id>
         OR: Celery scheduled task (weekly)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. FETCH DOCUMENT                                               │
├─────────────────────────────────────────────────────────────────┤
│  Celery Task: ingest_legal_source(source_id)                   │
│  ↓                                                               │
│  Get CorpusSource from DB                                       │
│  ↓                                                               │
│  Route to connector based on source type:                       │
│  - BOEConnector (BOE.es HTML)                                   │
│  - DOUEConnector (EUR-Lex XML)                                  │
│  - DGTConnector (PETETE PDF)                                    │
│  ↓                                                               │
│  HTTP GET to official URL                                       │
│  ↓                                                               │
│  Raw HTML/PDF downloaded                                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. PARSE & NORMALIZE                                            │
├─────────────────────────────────────────────────────────────────┤
│  LegalDocumentNormalizer.normalize(raw_doc, source)            │
│  ↓                                                               │
│  Parse HTML/PDF:                                                │
│  - Extract title, publication date                              │
│  - Identify structure (articles, sections, dispositions)        │
│  - Clean text (remove HTML tags, fix encoding)                  │
│  ↓                                                               │
│  Canonical JSON output:                                         │
│  {                                                              │
│    "titulo": "Ley 35/2006 del IRPF",                           │
│    "chunks": [                                                  │
│      {                                                          │
│        "type": "article",                                       │
│        "label": "Artículo 30",                                  │
│        "text": "Son gastos deducibles...",                     │
│        "metadata": {"seccion": "CapítuloIII"}                  │
│      }                                                          │
│    ]                                                            │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. GENERATE EMBEDDINGS                                          │
├─────────────────────────────────────────────────────────────────┤
│  For each chunk:                                                │
│  ↓                                                               │
│  EmbeddingService.embed(chunk['text'])                         │
│  ↓                                                               │
│  Call Gemini API:                                               │
│  POST https://generativelanguage.googleapis.com/.../           │
│       text-embedding-004:embedContent                           │
│  Body: {"content": {"parts": [{"text": "..."}]}}              │
│  ↓                                                               │
│  Response: {"embedding": {"values": [0.123, -0.456, ...]}}    │
│  ↓                                                               │
│  Convert to pgvector format: [0.123, -0.456, ...]             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. STORE IN DATABASE                                            │
├─────────────────────────────────────────────────────────────────┤
│  Create LegalDocument:                                          │
│  - doc_id, title, url, raw_html, metadata                      │
│  ↓                                                               │
│  For each chunk:                                                │
│  Create DocumentChunk:                                          │
│  - chunk_text, embedding (vector), chunk_label, metadata       │
│  ↓                                                               │
│  PostgreSQL INSERT with pgvector:                               │
│  INSERT INTO legal_document_chunks (                            │
│    embedding,                                                   │
│    chunk_text,                                                  │
│    ...                                                          │
│  ) VALUES (                                                     │
│    '[0.123, -0.456, ...]'::vector(768),                        │
│    'Son gastos deducibles...',                                  │
│    ...                                                          │
│  );                                                             │
│  ↓                                                               │
│  Update CorpusSource.estado = 'ingested'                       │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Query Flow (Realtime, <5s)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USER QUERY                                                   │
└─────────────────────────────────────────────────────────────────┘
   User types: "¿Puedo deducir gastos de home studio?"
                              ↓
   Frontend: POST /api/v1/legal-graphrag/chat/
   Body: {"query": "¿Puedo deducir gastos de home studio?"}
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. API VALIDATION                                               │
├─────────────────────────────────────────────────────────────────┤
│  Django View: LegalChatView.post(request)                      │
│  ↓                                                               │
│  Validate request:                                              │
│  - JWT token (optional for MVP)                                 │
│  - Query not empty                                              │
│  - Rate limit check (100/day per IP)                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. INTENT CLASSIFICATION (Simple)                               │
├─────────────────────────────────────────────────────────────────┤
│  LegalRAGEngine._classify_area(query)                          │
│  ↓                                                               │
│  Keyword matching:                                              │
│  - "deducir", "gastos" → area_principal = "Fiscal"             │
│  - "contrato", "autónomo" → area_principal = "Laboral"         │
│  - "derechos de autor" → area_principal = "Propiedad Intelectual" │
│  ↓                                                               │
│  Output: area_principal = "Fiscal"                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. HIERARCHICAL RETRIEVAL                                       │
├─────────────────────────────────────────────────────────────────┤
│  LegalSearchEngine.search_by_hierarchy(query, area="Fiscal")   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 4a. SEARCH NORMATIVA P1                                  │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ Filters: {naturaleza: "Normativa", prioridad: "P1"}     │  │
│  │ ↓                                                         │  │
│  │ Generate query embedding (Gemini API)                    │  │
│  │ ↓                                                         │  │
│  │ Vector search (pgvector):                                │  │
│  │ SELECT *, 1 - (embedding <=> query_vec) AS similarity   │  │
│  │ FROM legal_document_chunks                               │  │
│  │ WHERE metadata->>'naturaleza' = 'Normativa'             │  │
│  │   AND metadata->>'prioridad' = 'P1'                     │  │
│  │ ORDER BY embedding <=> query_vec                         │  │
│  │ LIMIT 10;                                                │  │
│  │ ↓                                                         │  │
│  │ Lexical search (PostgreSQL FTS):                         │  │
│  │ SELECT *, ts_rank(search_vector, query) AS rank         │  │
│  │ FROM legal_document_chunks                               │  │
│  │ WHERE search_vector @@ to_tsquery('spanish', 'deducir')  │  │
│  │ LIMIT 10;                                                │  │
│  │ ↓                                                         │  │
│  │ Merge results (RRF fusion)                               │  │
│  │ ↓                                                         │  │
│  │ Rerank by legal authority (boost Ley > RD)              │  │
│  │ ↓                                                         │  │
│  │ Top 5 normativa chunks returned                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 4b. SEARCH DOCTRINA P1                                   │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ Filters: {naturaleza: "Doctrina administrativa"}        │  │
│  │ ↓                                                         │  │
│  │ Same hybrid search process                               │  │
│  │ ↓                                                         │  │
│  │ Top 3 doctrina chunks returned                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 4c. SEARCH JURISPRUDENCIA (Optional for MVP)            │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ Filters: {naturaleza: "Jurisprudencia"}                 │  │
│  │ ↓                                                         │  │
│  │ Top 2 juris chunks returned                              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Output: {                                                      │
│    "normativa": [chunk1, chunk2, ...],                         │
│    "doctrina": [chunk1, chunk2, ...],                          │
│    "jurisprudencia": [chunk1, chunk2]                          │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. LLM ANSWER GENERATION                                        │
├─────────────────────────────────────────────────────────────────┤
│  LegalRAGEngine._build_prompt(query, sources)                  │
│  ↓                                                               │
│  Format prompt:                                                 │
│  - System instructions (hierarchy rules)                        │
│  - Normativa context (5 chunks)                                 │
│  - Doctrina context (3 chunks)                                  │
│  - User query                                                   │
│  ↓                                                               │
│  Call Gemini API:                                               │
│  model = genai.GenerativeModel('gemini-2.5-flash')             │
│  response = model.generate_content(prompt)                      │
│  ↓                                                               │
│  LLM generates structured answer:                               │
│  """                                                            │
│  ## Resumen                                                     │
│  Sí, puedes deducir gastos de home studio...                   │
│                                                                  │
│  ## Normativa aplicable                                         │
│  - Ley IRPF, Artículo 30.2: Los gastos necesarios...          │
│                                                                  │
│  ## Criterios administrativos                                   │
│  - DGT V0123-21: Acepta gastos proporcionales...              │
│                                                                  │
│  ⚠️ Consulta con un asesor fiscal para tu caso específico.    │
│  """                                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. FORMAT RESPONSE                                              │
├─────────────────────────────────────────────────────────────────┤
│  Format sources for citation:                                   │
│  sources = [                                                    │
│    {                                                            │
│      "label": "Ley IRPF, Artículo 30.2",                       │
│      "text": "Son gastos deducibles aquellos...",             │
│      "url": "https://www.boe.es/eli/es/l/2006/...",           │
│      "boe_id": "BOE-A-2006-20764",                             │
│      "tipo": "Ley",                                            │
│      "naturaleza": "Normativa"                                  │
│    },                                                           │
│    ...                                                          │
│  ]                                                              │
│  ↓                                                               │
│  Return JSON:                                                   │
│  {                                                              │
│    "answer": "<markdown answer>",                              │
│    "sources": [...],                                           │
│    "metadata": {                                                │
│      "area_principal": "Fiscal",                                │
│      "model": "gemini-2.5-flash",                              │
│      "normativa_count": 5,                                      │
│      "response_time_ms": 3200                                   │
│    }                                                            │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. FRONTEND DISPLAY                                             │
├─────────────────────────────────────────────────────────────────┤
│  React component renders:                                       │
│  - Answer (markdown formatted)                                  │
│  - Source cards (expandable)                                    │
│  - Disclaimer (always visible)                                  │
│  - Related questions (optional)                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Security Architecture

### 5.1 Authentication & Authorization

**Auth Flow**:
```
1. User logs in via existing system (users app)
   ↓
2. JWT access token issued (12-hour lifetime)
   ↓
3. Frontend stores token in localStorage
   ↓
4. Every API call includes: Authorization: Bearer <token>
   ↓
5. Django middleware validates JWT
   ↓
6. If valid → request.user set, proceed
   If invalid → 401 Unauthorized
```

**Permission Classes**:
```python
# MVP: Anonymous queries allowed
permission_classes = [AllowAny]

# Post-MVP: Require authentication
permission_classes = [IsAuthenticated]

# Future: Role-based (admin can trigger ingestion)
permission_classes = [IsAdminUser]
```

### 5.2 Rate Limiting

**Strategy**:
```python
# Use django-ratelimit or custom middleware

from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='100/d', method='POST')
def chat_view(request):
    # Allows 100 queries per day per IP
    pass
```

**Tiers** (Post-MVP with billing integration):
- Free: 10 queries/day
- Basic: 100 queries/day
- Plus: 500 queries/day
- Advanced: Unlimited

### 5.3 Data Privacy (GDPR)

**What We Store**:
- ✅ Query text (for improving system, anonymized)
- ✅ Response (for audit trail)
- ✅ Timestamp, IP (for rate limiting)
- ❌ User identity (unless authenticated)
- ❌ Personal data in queries (must be stripped)

**PII Detection** (Post-MVP):
```python
def anonymize_query(query: str) -> str:
    """Strip potential PII from queries"""
    # Remove emails
    query = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', query)
    # Remove phone numbers
    query = re.sub(r'\b\d{9}\b', '[TELÉFONO]', query)
    # Remove NIE/DNI
    query = re.sub(r'\b\d{8}[A-Z]\b', '[DNI]', query)
    return query
```

**User Rights**:
- Right to access: User can download their query history
- Right to deletion: User can request query deletion
- Right to portability: Export as JSON

### 5.4 API Security

**Checklist**:
- ✅ HTTPS only (enforced by Django SECURE_SSL_REDIRECT)
- ✅ CORS whitelist (only legal.artisting.es)
- ✅ CSRF protection (Django middleware)
- ✅ SQL injection prevention (Django ORM parameterized queries)
- ✅ XSS prevention (React escapes by default, DOMPurify for markdown)
- ✅ Rate limiting (see above)
- ✅ Input validation (DRF serializers)

**Django Settings**:
```python
SECURE_SSL_REDIRECT = True  # Force HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year HSTS

CORS_ALLOWED_ORIGINS = [
    'https://legal.artisting.es',
    'http://localhost:3001',  # Dev only
]

ALLOWED_HOSTS = [
    'api.artisting.es',
    'chat.artisting.es',
    'localhost',
]
```

---

## 6. Scalability Considerations

### 6.1 Current Bottlenecks (MVP)

| Component | Limit | When to Scale |
|-----------|-------|---------------|
| **PostgreSQL** | 100 concurrent connections | > 500 queries/second |
| **pgvector Search** | 10ms for 1000 docs | > 10,000 docs (use HNSW index) |
| **Gemini API** | 1500 requests/day (free) | > 1500 queries/day (pay tier) |
| **Django App** | Single instance | > 1000 concurrent users |

### 6.2 Scaling Strategy (Phase 2+)

**Database**:
```sql
-- MVP: IVFFlat index (good for <10k vectors)
CREATE INDEX ON legal_document_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Phase 2: HNSW index (better for >10k vectors)
CREATE INDEX ON legal_document_chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

**Application**:
- Horizontal scaling: Multiple Django instances behind load balancer
- Caching: Redis cache for frequently asked questions
- CDN: Static frontend assets served via CDN

**Cost Projections**:
```
MVP (100 queries/day):
- Gemini API: Free
- Digital Ocean DB: $15/month (existing)
- Hosting: $12/month (existing App Platform)
Total: $0/month (incremental)

Production (1000 queries/day):
- Gemini API: ~$30/month (paid tier)
- Digital Ocean DB: $50/month (upgrade)
- Hosting: $25/month (2 instances)
Total: ~$105/month
```

---

## 7. Monitoring & Observability

### 7.1 Key Metrics to Track

**Application Metrics**:
- Requests per minute (by endpoint)
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Celery task queue length

**Business Metrics**:
- Queries per day (by area_principal)
- Average sources per answer
- Citation click-through rate
- User satisfaction (thumbs up/down)

**System Metrics**:
- Database CPU/memory
- Celery worker CPU/memory
- Redis memory usage
- Gemini API quota usage

### 7.2 Logging Strategy

**Django Logging**:
```python
# backend/ovra_backend/settings.py

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/legal_graphrag.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'apps.legal_graphrag': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

**Log Events**:
```python
import logging
logger = logging.getLogger('apps.legal_graphrag')

# In views
logger.info(f"Query received: {query[:50]}")
logger.info(f"Area classified: {area_principal}")
logger.info(f"Sources retrieved: {len(sources)}")
logger.info(f"Response time: {response_time}ms")

# In tasks
logger.info(f"Ingestion started: source_id={source_id}")
logger.error(f"Ingestion failed: source_id={source_id}, error={str(e)}")
```

### 7.3 Error Tracking

**Sentry Integration** (Post-MVP):
```python
# pip install sentry-sdk

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="https://...@sentry.io/...",
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,  # 10% of transactions
    send_default_pii=False,  # GDPR compliance
)
```

---

## 8. Deployment Architecture

### 8.1 Development Environment

```
Local Machine (Windows)
├── Backend: python manage.py runserver 0.0.0.0:8000
├── Frontend: npm run dev (port 3001)
├── PostgreSQL: localhost:5432 (or Digital Ocean remote)
├── Redis: localhost:6379
└── Celery: celery -A ovra_backend worker -l info
```

**Development URLs**:
- Backend API: http://localhost:8000/api/v1/
- Frontend: http://localhost:3001/
- Django Admin: http://localhost:8000/admin/

### 8.2 Production Environment (Digital Ocean)

```
┌─────────────────────────────────────────────────────────────┐
│                     Digital Ocean                            │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────┐  │
│  │  App Platform (Backend)                               │  │
│  │  - Django 5 + Gunicorn                                │  │
│  │  - Auto-deploy from Git (main branch)                 │  │
│  │  - URL: api.artisting.es                              │  │
│  │  - Environment variables from .env                    │  │
│  └───────────────────────────────────────────────────────┘  │
│                              ↓                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  App Platform (Frontend)                              │  │
│  │  - Next.js 15 (SSR + Static)                          │  │
│  │  - Auto-deploy from Git (main branch)                 │  │
│  │  - URL: legal.artisting.es                            │  │
│  └───────────────────────────────────────────────────────┘  │
│                              ↓                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Managed PostgreSQL                                   │  │
│  │  - Version: 15                                         │  │
│  │  - Plan: Basic ($15/month existing)                   │  │
│  │  - Extensions: pgvector                                │  │
│  │  - Backups: Daily automatic                           │  │
│  └───────────────────────────────────────────────────────┘  │
│                              ↓                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Managed Redis                                         │  │
│  │  - Celery broker + result backend                     │  │
│  │  - Plan: Basic ($15/month)                            │  │
│  └───────────────────────────────────────────────────────┘  │
│                              ↓                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Worker (Celery)                                       │  │
│  │  - Background ingestion tasks                          │  │
│  │  - Runs on same app as Django                         │  │
│  │  - Command: celery -A ovra_backend worker             │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              External Services                               │
├─────────────────────────────────────────────────────────────┤
│  - Gemini API (Google Cloud)                                │
│  - Stripe API (existing)                                     │
│  - Let's Encrypt (SSL certificates)                         │
└─────────────────────────────────────────────────────────────┘
```

**Deployment Process**:
```bash
# 1. Push to Git
git add .
git commit -m "Add legal graphrag feature"
git push origin main

# 2. Digital Ocean auto-detects push
# 3. Runs build:
#    - Backend: pip install -r requirements.txt
#    - Frontend: npm run build
# 4. Runs migrations: python manage.py migrate
# 5. Collects static: python manage.py collectstatic
# 6. Restarts app servers
# 7. Health check: GET /api/v1/health/
# 8. If healthy → switch traffic to new version
```

---

## 9. Technology Alternatives Considered

### Why NOT these alternatives:

| Alternative | Reason for Rejection |
|-------------|---------------------|
| **Supabase** (for Legal GraphRAG) | Already used for grants (read-only). Need write access for chat history. Simpler to use main PostgreSQL. |
| **OpenSearch** | Overkill for 70 sources. pgvector + PG FTS sufficient. OpenSearch adds complexity, cost, and another service to manage. |
| **FastAPI** | Django already in use for grants. Reusing patterns > learning new framework. DRF sufficient for REST APIs. |
| **Pinecone/Weaviate** | Managed vector DBs are great but add cost ($70+/month). pgvector free, battle-tested, good for <100k docs. |
| **LangChain** | Heavy framework. We only need simple RAG (retrieve + prompt + LLM). Direct Gemini API cleaner and faster. |
| **OpenAI GPT-4** | Expensive ($0.03/1k tokens). Gemini free tier + good Spanish support. Can switch later if needed. |
| **Elasticsearch** | Similar to OpenSearch reasoning. PostgreSQL FTS + pgvector covers MVP needs. |
| **Neo4j** | Graph DB great for citation networks. Deferred to Phase 2 (post-MVP). PostgreSQL recursive CTEs work for simple graphs. |

---

## 10. Future Architecture Evolution

### Phase 2: Enhanced Retrieval (Month 2-3)

- Add graph database (Neo4j or PostgreSQL graph tables)
- Citation network: "Find all cases citing Article X"
- Temporal versioning: "What was the law in 2022?"
- Advanced reranking: Cross-encoder model

### Phase 3: Multi-Modal (Month 4-6)

- OCR for scanned PDFs (Tesseract)
- Table extraction (Camelot/Tabula)
- Image analysis (diagrams in legal docs)

### Phase 4: Proactive Assistance (Month 6+)

- Law change monitoring (daily BOE scraping)
- User alerts: "A law you asked about changed"
- Personalized recommendations based on query history

---

**Document End** | Next: [02_DATA_MODEL.md](./02_DATA_MODEL.md)
