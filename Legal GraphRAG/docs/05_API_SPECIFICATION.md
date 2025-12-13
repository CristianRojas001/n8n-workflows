# Legal GraphRAG System - API Specification

## Document Information
- **Version**: 1.0 (MVP)
- **Last Updated**: 2025-12-11
- **Status**: Planning Phase
- **Related**: [01_ARCHITECTURE.md](./01_ARCHITECTURE.md) | [04_RETRIEVAL_GUIDE.md](./04_RETRIEVAL_GUIDE.md)

---

## 1. API Overview

### Base URL

```
Development: http://localhost:8000/api/v1/legal-graphrag/
Production:  https://api.artisting.es/api/v1/legal-graphrag/
```

### Authentication

**MVP**: Anonymous queries allowed (no authentication required)

**Post-MVP**: JWT authentication (shared with existing auth system)

```http
Authorization: Bearer <jwt_token>
```

### Rate Limiting

- **Anonymous**: 100 requests/day per IP
- **Authenticated (Future)**:
  - Free: 10 queries/day
  - Basic: 100 queries/day
  - Plus: 500 queries/day

### Response Format

All responses return JSON with this structure:

```json
{
  "success": true | false,
  "data": {...},
  "error": null | {"code": "...", "message": "..."},
  "metadata": {...}
}
```

---

## 2. Endpoints

### 2.1 POST /chat

**Purpose**: Main conversational Q&A endpoint

**Request**:

```http
POST /api/v1/legal-graphrag/chat/
Content-Type: application/json

{
  "query": "¿Puedo deducir gastos de mi home studio como artista?",
  "session_id": "optional-uuid",
  "filters": {
    "area_principal": "Fiscal"  // optional
  }
}
```

**Response** (Success):

```json
{
  "success": true,
  "data": {
    "answer": "## Resumen\n\nSí, puedes deducir gastos de home studio...",
    "sources": [
      {
        "id": "uuid",
        "category": "normativa",
        "label": "Artículo 30.2",
        "text": "Son gastos deducibles aquellos que...",
        "full_text": "...",
        "doc_title": "Ley 35/2006 del IRPF",
        "doc_id_oficial": "BOE-A-2006-20764",
        "url": "https://www.boe.es/eli/es/l/2006/11/28/35/con",
        "tipo": "Ley",
        "nivel_autoridad": "Ley",
        "naturaleza": "Normativa",
        "similarity": 0.87,
        "reference_label": "N1"
      }
    ],
    "session_id": "uuid",
    "metadata": {
      "area_principal": "Fiscal",
      "model": "gemini-2.5-flash",
      "normativa_count": 5,
      "doctrina_count": 3,
      "jurisprudencia_count": 0,
      "response_time_ms": 3200
    }
  },
  "error": null
}
```

**Response** (Error):

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "QUERY_TOO_SHORT",
    "message": "Query must be at least 10 characters"
  }
}
```

**Error Codes**:
- `QUERY_TOO_SHORT`: Query < 10 chars
- `QUERY_TOO_LONG`: Query > 500 chars
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Server error

---

### 2.2 POST /search

**Purpose**: Search legal documents (no LLM answer generation)

**Request**:

```http
POST /api/v1/legal-graphrag/search/
Content-Type: application/json

{
  "query": "deducción gastos autónomos",
  "filters": {
    "naturaleza": "Normativa",
    "prioridad": "P1",
    "area_principal": "Fiscal"
  },
  "limit": 10
}
```

**Response**:

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "uuid",
        "chunk_label": "Artículo 30",
        "chunk_text": "Son gastos deducibles...",
        "doc_title": "Ley IRPF",
        "doc_id_oficial": "BOE-A-2006-20764",
        "url": "https://www.boe.es/...",
        "metadata": {
          "naturaleza": "Normativa",
          "prioridad": "P1",
          "nivel_autoridad": "Ley"
        },
        "similarity": 0.89
      }
    ],
    "total": 42,
    "page": 1,
    "per_page": 10
  }
}
```

---

### 2.3 GET /documents/{doc_id}

**Purpose**: Get full legal document with all chunks

**Request**:

```http
GET /api/v1/legal-graphrag/documents/BOE-A-2006-20764/
```

**Response**:

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "doc_title": "Ley 35/2006, de 28 de noviembre, del Impuesto sobre la Renta de las Personas Físicas",
    "doc_id_oficial": "BOE-A-2006-20764",
    "url": "https://www.boe.es/eli/es/l/2006/11/28/35/con",
    "metadata": {
      "fecha_publicacion": "2006-11-29",
      "naturaleza": "Normativa",
      "tipo": "Ley",
      "nivel_autoridad": "Ley",
      "area_principal": "Fiscal"
    },
    "chunks": [
      {
        "id": "uuid",
        "chunk_type": "article",
        "chunk_label": "Artículo 1",
        "chunk_text": "...",
        "position": 1
      }
    ],
    "created_at": "2025-12-11T10:00:00Z"
  }
}
```

---

### 2.4 GET /sources

**Purpose**: List corpus sources (catalog)

**Request**:

```http
GET /api/v1/legal-graphrag/sources/?prioridad=P1&area_principal=Fiscal
```

**Query Parameters**:
- `prioridad`: P1, P2, P3
- `naturaleza`: Normativa, Doctrina administrativa, Jurisprudencia
- `area_principal`: Fiscal, Laboral, etc.
- `estado`: pending, ingested, failed
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)

**Response**:

```json
{
  "success": true,
  "data": {
    "sources": [
      {
        "id": 1,
        "titulo": "Constitución española",
        "id_oficial": "BOE-A-1978-31229",
        "url_oficial": "https://www.boe.es/...",
        "prioridad": "P1",
        "naturaleza": "Normativa",
        "area_principal": "Marco general",
        "tipo": "Constitución",
        "nivel_autoridad": "Constitución",
        "estado": "ingested",
        "last_ingested_at": "2025-12-11T12:00:00Z"
      }
    ],
    "total": 70,
    "page": 1,
    "per_page": 20
  }
}
```

---

### 2.5 GET /sources/{source_id}

**Purpose**: Get source details with ingestion status

**Request**:

```http
GET /api/v1/legal-graphrag/sources/1/
```

**Response**:

```json
{
  "success": true,
  "data": {
    "id": 1,
    "titulo": "Constitución española",
    "id_oficial": "BOE-A-1978-31229",
    "url_oficial": "https://www.boe.es/...",
    "prioridad": "P1",
    "naturaleza": "Normativa",
    "area_principal": "Marco general",
    "tipo": "Constitución",
    "ambito": "España",
    "nivel_autoridad": "Constitución",
    "vigencia": "Vigente",
    "estado": "ingested",
    "last_ingested_at": "2025-12-11T12:00:00Z",
    "ingestion_error": null,
    "documento": {
      "id": "uuid",
      "chunks_count": 169,
      "created_at": "2025-12-11T12:00:00Z"
    }
  }
}
```

---

### 2.6 POST /feedback

**Purpose**: Submit feedback on answer quality (thumbs up/down)

**Request**:

```http
POST /api/v1/legal-graphrag/feedback/
Content-Type: application/json

{
  "message_id": "uuid",
  "rating": 5,  // 1 (bad) or 5 (good)
  "comment": "Very helpful!"  // optional
}
```

**Response**:

```json
{
  "success": true,
  "data": {
    "message": "Feedback recorded. Thank you!"
  }
}
```

---

### 2.7 GET /chat/sessions/{session_id}

**Purpose**: Get chat history for a session

**Request**:

```http
GET /api/v1/legal-graphrag/chat/sessions/{session_id}/
```

**Response**:

```json
{
  "success": true,
  "data": {
    "session_id": "uuid",
    "created_at": "2025-12-11T10:00:00Z",
    "messages": [
      {
        "id": "uuid",
        "role": "user",
        "content": "¿Puedo deducir gastos de home studio?",
        "created_at": "2025-12-11T10:00:00Z"
      },
      {
        "id": "uuid",
        "role": "assistant",
        "content": "## Resumen\n\nSí, puedes...",
        "sources": [...],
        "created_at": "2025-12-11T10:00:05Z"
      }
    ]
  }
}
```

---

## 3. Django REST Framework Implementation

### 3.1 Serializers

```python
# apps/legal_graphrag/serializers.py

from rest_framework import serializers
from .models import CorpusSource, LegalDocument, ChatMessage

class ChatQuerySerializer(serializers.Serializer):
    """Serializer for chat query request"""
    query = serializers.CharField(min_length=10, max_length=500)
    session_id = serializers.UUIDField(required=False, allow_null=True)
    filters = serializers.DictField(required=False, allow_null=True)

class SourceSerializer(serializers.Serializer):
    """Serializer for legal source in response"""
    id = serializers.UUIDField()
    category = serializers.CharField()
    label = serializers.CharField()
    text = serializers.CharField()
    full_text = serializers.CharField()
    doc_title = serializers.CharField()
    doc_id_oficial = serializers.CharField()
    url = serializers.URLField()
    tipo = serializers.CharField()
    nivel_autoridad = serializers.CharField()
    naturaleza = serializers.CharField()
    similarity = serializers.FloatField()
    reference_label = serializers.CharField()

class ChatResponseSerializer(serializers.Serializer):
    """Serializer for chat response"""
    answer = serializers.CharField()
    sources = SourceSerializer(many=True)
    session_id = serializers.UUIDField()
    metadata = serializers.DictField()

class CorpusSourceSerializer(serializers.ModelSerializer):
    """Serializer for CorpusSource model"""
    class Meta:
        model = CorpusSource
        fields = [
            'id', 'titulo', 'id_oficial', 'url_oficial',
            'prioridad', 'naturaleza', 'area_principal',
            'tipo', 'ambito', 'nivel_autoridad', 'vigencia',
            'estado', 'last_ingested_at', 'created_at'
        ]
```

### 3.2 Views

```python
# apps/legal_graphrag/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.core.cache import cache
import logging

logger = logging.getLogger('apps.legal_graphrag.api')

class LegalChatView(APIView):
    """
    POST /api/v1/legal-graphrag/chat/
    Main conversational Q&A endpoint
    """
    permission_classes = [AllowAny]  # MVP: no auth

    def post(self, request):
        from .serializers import ChatQuerySerializer, ChatResponseSerializer
        from .services.legal_rag_engine import LegalRAGEngine
        from .models import ChatSession, ChatMessage
        import uuid
        import time

        # Validate request
        serializer = ChatQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'data': None,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': str(serializer.errors)
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        query = serializer.validated_data['query']
        session_id = serializer.validated_data.get('session_id')
        filters = serializer.validated_data.get('filters', {})

        # Rate limiting (simple IP-based for MVP)
        ip = request.META.get('REMOTE_ADDR')
        rate_key = f"rate_limit:{ip}"
        current_count = cache.get(rate_key, 0)

        if current_count >= 100:
            return Response({
                'success': False,
                'data': None,
                'error': {
                    'code': 'RATE_LIMIT_EXCEEDED',
                    'message': 'You have exceeded 100 requests/day. Try again tomorrow.'
                }
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # Increment rate limit counter
        cache.set(rate_key, current_count + 1, timeout=60*60*24)  # 24 hours

        # Get or create session
        if not session_id:
            session = ChatSession.objects.create(
                user=request.user if request.user.is_authenticated else None,
                ip_address=ip,
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            session_id = session.id
        else:
            session = ChatSession.objects.get(id=session_id)

        # Save user message
        user_message = ChatMessage.objects.create(
            session=session,
            role='user',
            content=query
        )

        # Process query
        start_time = time.time()
        try:
            rag_engine = LegalRAGEngine()
            result = rag_engine.answer_query(query)

            response_time_ms = int((time.time() - start_time) * 1000)
            result['metadata']['response_time_ms'] = response_time_ms

            # Save assistant message
            assistant_message = ChatMessage.objects.create(
                session=session,
                role='assistant',
                content=result['answer'],
                sources=result['sources'],
                metadata=result['metadata']
            )

            # Format response
            response_data = {
                'answer': result['answer'],
                'sources': result['sources'],
                'session_id': str(session_id),
                'metadata': result['metadata']
            }

            logger.info(f"Query processed: {query[:50]}... ({response_time_ms}ms)")

            return Response({
                'success': True,
                'data': response_data,
                'error': None
            })

        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            return Response({
                'success': False,
                'data': None,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'An error occurred processing your query. Please try again.'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LegalSearchView(APIView):
    """
    POST /api/v1/legal-graphrag/search/
    Search endpoint (no LLM)
    """
    permission_classes = [AllowAny]

    def post(self, request):
        from .services.legal_search_engine import LegalSearchEngine

        query = request.data.get('query')
        filters = request.data.get('filters', {})
        limit = request.data.get('limit', 10)

        if not query or len(query) < 3:
            return Response({
                'success': False,
                'error': {'code': 'QUERY_TOO_SHORT', 'message': 'Query too short'}
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            search_engine = LegalSearchEngine()
            results = search_engine.hybrid_search(query, filters, limit)

            return Response({
                'success': True,
                'data': {
                    'results': results,
                    'total': len(results),
                    'page': 1,
                    'per_page': limit
                }
            })

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return Response({
                'success': False,
                'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CorpusSourceListView(APIView):
    """
    GET /api/v1/legal-graphrag/sources/
    List corpus sources
    """
    permission_classes = [AllowAny]

    def get(self, request):
        from .models import CorpusSource
        from .serializers import CorpusSourceSerializer

        # Filters
        queryset = CorpusSource.objects.all()

        if 'prioridad' in request.query_params:
            queryset = queryset.filter(prioridad=request.query_params['prioridad'])

        if 'naturaleza' in request.query_params:
            queryset = queryset.filter(naturaleza=request.query_params['naturaleza'])

        if 'area_principal' in request.query_params:
            queryset = queryset.filter(area_principal=request.query_params['area_principal'])

        if 'estado' in request.query_params:
            queryset = queryset.filter(estado=request.query_params['estado'])

        # Pagination
        page = int(request.query_params.get('page', 1))
        per_page = min(int(request.query_params.get('per_page', 20)), 100)

        total = queryset.count()
        start = (page - 1) * per_page
        end = start + per_page

        sources = queryset[start:end]
        serializer = CorpusSourceSerializer(sources, many=True)

        return Response({
            'success': True,
            'data': {
                'sources': serializer.data,
                'total': total,
                'page': page,
                'per_page': per_page
            }
        })
```

### 3.3 URL Configuration

```python
# apps/legal_graphrag/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.LegalChatView.as_view(), name='legal-chat'),
    path('search/', views.LegalSearchView.as_view(), name='legal-search'),
    path('sources/', views.CorpusSourceListView.as_view(), name='corpus-sources'),
    path('sources/<int:source_id>/', views.CorpusSourceDetailView.as_view(), name='corpus-source-detail'),
    path('documents/<str:doc_id_oficial>/', views.LegalDocumentDetailView.as_view(), name='document-detail'),
]
```

---

## 4. Frontend Integration (Next.js)

### 4.1 API Client Service

```typescript
// lib/services/legal-chat.service.ts

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ChatQuery {
  query: string;
  session_id?: string;
  filters?: {
    area_principal?: string;
  };
}

export interface ChatResponse {
  success: boolean;
  data: {
    answer: string;
    sources: Source[];
    session_id: string;
    metadata: {
      area_principal?: string;
      model: string;
      normativa_count: number;
      doctrina_count: number;
      response_time_ms: number;
    };
  };
  error?: {
    code: string;
    message: string;
  };
}

export interface Source {
  id: string;
  category: string;
  label: string;
  text: string;
  full_text: string;
  doc_title: string;
  doc_id_oficial: string;
  url: string;
  tipo: string;
  nivel_autoridad: string;
  similarity: number;
  reference_label: string;
}

export class LegalChatService {
  async chat(query: ChatQuery): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE}/api/v1/legal-graphrag/chat/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(query),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
  }

  async search(query: string, filters?: any, limit = 10) {
    const response = await fetch(`${API_BASE}/api/v1/legal-graphrag/search/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query, filters, limit }),
    });

    return response.json();
  }

  async getSources(filters?: any) {
    const params = new URLSearchParams(filters);
    const response = await fetch(`${API_BASE}/api/v1/legal-graphrag/sources/?${params}`);
    return response.json();
  }
}
```

### 4.2 React Component Example

```typescript
// components/legal/LegalChatInterface.tsx

'use client';

import { useState } from 'react';
import { LegalChatService, ChatResponse } from '@/lib/services/legal-chat.service';

export default function LegalChatInterface() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const chatService = new LegalChatService();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!query.trim()) return;

    setLoading(true);
    try {
      const result = await chatService.chat({ query });
      setResponse(result);
    } catch (error) {
      console.error('Chat error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-4">
      <form onSubmit={handleSubmit} className="mb-8">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Pregunta algo sobre normativa legal para artistas..."
          className="w-full p-4 border rounded-lg"
          rows={3}
        />
        <button
          type="submit"
          disabled={loading}
          className="mt-2 px-6 py-2 bg-blue-600 text-white rounded-lg"
        >
          {loading ? 'Procesando...' : 'Preguntar'}
        </button>
      </form>

      {response?.success && response.data && (
        <div className="space-y-6">
          {/* Answer */}
          <div className="prose max-w-none">
            <div dangerouslySetInnerHTML={{ __html: response.data.answer }} />
          </div>

          {/* Sources */}
          <div className="border-t pt-6">
            <h3 className="text-lg font-semibold mb-4">Fuentes citadas</h3>
            <div className="space-y-4">
              {response.data.sources.map((source) => (
                <div key={source.id} className="border rounded-lg p-4">
                  <div className="font-semibold">{source.reference_label}: {source.label}</div>
                  <div className="text-sm text-gray-600">{source.doc_title}</div>
                  <div className="mt-2 text-sm">{source.text}</div>
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 text-sm mt-2 inline-block"
                  >
                    Ver en BOE →
                  </a>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## 5. Error Handling Best Practices

### 5.1 Standard Error Response

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}  // optional
  }
}
```

### 5.2 HTTP Status Codes

| Status | Use Case |
|--------|----------|
| 200 | Successful request |
| 400 | Bad request (validation error) |
| 401 | Unauthorized (missing/invalid JWT) |
| 403 | Forbidden (authenticated but no permission) |
| 404 | Resource not found |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

---

**Document End** | Next: [06_DEPLOYMENT_GUIDE.md](./06_DEPLOYMENT_GUIDE.md)
