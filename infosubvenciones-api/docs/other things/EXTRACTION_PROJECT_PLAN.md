# InfoSubvenciones Data Extraction Project Plan

> Purpose: Define the data extraction system (search + chat) architecture for integration with ARTISTING platform.

## 1. Vision & Success Criteria

### Problem Statement
The ingestion system (18+ grants) is complete. Now we need to:
1. **Search Grants**: Find relevant grants using natural language + filters
2. **Chat with Data**: Ask questions and get AI-powered answers with full context
3. **Access Details**: View complete grant info including PDFs

### High-Level Outcome
Build **Grant Search & Chat System integrated with ARTISTING**

**Timeline**: 1 week (7 days)

### Success Metrics (KPIs)
- **Search Performance**: <2s response time for semantic queries
- **Search Quality**: >80% relevant results in top 5
- **Chat Quality**: Accurate answers with proper citations
- **User Experience**: Seamless integration with ARTISTING UI
- **Data Completeness**: All 110+ fields accessible via API
- **PDF Access**: Multi-option display (markdown, iframe, download)

### Non-Negotiables
- **Data Accuracy**: All responses must cite source grants, no hallucinations
- **Performance**: Search results <2s, chat responses <5s
- **Security**: Read-only database access, proper credential management
- **Modularity**: Can switch between DB connection and API layer
- **Model Flexibility**: Easy to switch between Gemini/GPT-4o/Claude
- **Cost Control**: Tiered model selection (cheap for simple, powerful for complex)

## 2. Stakeholders & Roles

- **Product Owner**: You (Cristian) - defines priorities, validates features
- **Tech Lead**: Claude - architecture, implementation, documentation
- **Testing Lead**: Codex - testing scripts, validation, QA
- **Data Provider**: Existing PostgreSQL database (ingestion complete)
- **Infrastructure**: Supabase PostgreSQL + Redis + ARTISTING Django backend

## 3. Timeline & Milestones

### One-Week Delivery Structure

**Target**: Complete functional system in 1 week (7 days)

| Day | Focus | Definition of Done |
|-----|-------|-------------------|
| **Day 1** | Documentation + Planning | All docs created, architecture clear |
| **Day 2-3** | Backend (Django grants app) | Search + Chat endpoints working |
| **Day 4-5** | Frontend (Next.js components) | UI integrated with ARTISTING |
| **Day 6** | Testing + Polish | All scenarios tested, bugs fixed |
| **Day 7** | Deployment Prep | Ready for production deployment |

## 4. Scope Breakdown

### 1. Backend - Django Grants App
**Purpose**: Expose grants data via REST API, integrate RAG chat

**Components**:
```
ARTISTING-main/backend/apps/grants/
├── models.py              # Proxy models to infosubvenciones DB
├── serializers.py         # API serialization
├── views.py               # API endpoints
├── urls.py                # Route definitions
├── services/
│   ├── grant_client.py    # Abstraction (DB or API)
│   ├── search_engine.py   # Hybrid search (filter + semantic)
│   ├── rag_engine.py      # Chat RAG system
│   ├── model_selector.py  # LLM model selection (Gemini/GPT-4o)
│   └── intent_classifier.py # Query intent detection
└── tests/
    └── test_search.py
```

**API Endpoints**:
- `POST /api/v1/grants/search` - Hybrid search (semantic + filters)
- `POST /api/v1/grants/chat` - RAG chat interface
- `GET /api/v1/grants/{id}` - Grant summary
- `GET /api/v1/grants/{id}/details` - Full grant details (lazy load)

**Dependencies**:
- Supabase PostgreSQL (read-only user)
- Redis for session/cache
- Gemini 2.0 Flash + GPT-4o API keys

**Constraints**:
- Must use existing database schema (no migrations)
- Read-only access (no writes to grants data)
- Must handle 110+ fields from Convocatoria + PDFExtraction

### 2. Frontend - Next.js Components
**Purpose**: User interface for searching and chatting with grants

**Components**:
```
ARTISTING-main/frontend/
├── app/
│   ├── grants/
│   │   └── page.tsx       # Search page (NEW)
│   └── chat/
│       └── page.tsx       # Modify for grants mode
├── components/
│   ├── grants/
│   │   ├── GrantCard.tsx          # Grant list item
│   │   ├── GrantDetailModal.tsx   # Full grant view
│   │   ├── GrantSearchForm.tsx    # Filter form
│   │   └── PDFViewer.tsx          # Multi-tab PDF display
│   └── chat/
│       └── ChatInterface.tsx      # Modify to show grants
```

**Features**:
- Search form with filters (region, sector, budget, dates)
- Results grid with pagination
- Chat panel alongside results
- Grant detail modal (tabs: summary, full doc, PDF, download)
- Mobile responsive

**Dependencies**:
- Existing ARTISTING design system (shadcn/ui, Tailwind)
- react-markdown (already installed)
- Existing auth context

### 3. Search Engine
**Purpose**: Hybrid search combining semantic similarity and filters

**Implementation**:
- Vector search using pgvector (cosine similarity)
- Filter search using Django ORM (SQL WHERE clauses)
- Reciprocal Rank Fusion (RRF) for combining results
- Pagination with session management

**Filters**:
- organismo (partial match)
- ambito (exact: ESTATAL, COMUNIDAD_AUTONOMA, LOCAL)
- finalidad (exact: 11, 14, etc.)
- regiones (array overlap)
- fecha_desde/fecha_hasta (date range)
- estado (abierta, cerrada, próxima)
- importe_min/importe_max (amount range)

**Search Modes**:
- **Semantic only**: Pure vector similarity
- **Filter only**: SQL WHERE clauses
- **Hybrid** (default): Combined with RRF ranking

### 4. RAG Chat System
**Purpose**: Conversational interface with context-aware responses

**Components**:
- Intent classification (search, explain, compare, recommend)
- Context assembly (top 5 grants with full details)
- Progressive data loading (summary first, full on demand)
- Clarification prompts (too many/few results, ambiguous)
- Model selection (Gemini Flash for simple, GPT-4o for complex)
- Pagination support ("¿y más opciones?")

**Response Format**:
```json
{
  "response_id": "uuid",
  "answer": "He encontrado 5 subvenciones...",
  "grants": [
    {
      "id": 123,
      "titulo": "...",
      "summary_preview": "...",
      "key_facts": {...},
      "pdf": {"url": "...", "should_display": true}
    }
  ],
  "suggested_actions": {
    "filters": [...],
    "follow_up_questions": [...]
  },
  "metadata": {
    "total_found": 45,
    "showing": 5,
    "has_more": true
  }
}
```

### 5. Security & Performance
**Purpose**: Ensure secure, fast, reliable system

**Security Measures**:
- Read-only PostgreSQL user (`grants_readonly`)
- Docker network isolation
- Environment variables for credentials
- Connection timeouts
- Input validation on all filters

**Performance Optimizations**:
- Redis caching (query embeddings, search results, sessions)
- Database connection pooling
- HNSW index on embeddings (already created)
- Query result pagination
- Lazy loading for full grant details

**Cache Strategy**:
```python
CACHE_TTL = {
    'embeddings': 3600,       # 1 hour
    'search_results': 300,    # 5 minutes
    'sessions': 7200,         # 2 hours
}
```

### 6. Documentation
**Purpose**: Guide implementation and enable future development

**Deliverables**:
- EXTRACTION_PROJECT_PLAN.md (this file)
- EXTRACTION_SPRINT_PLAN.md (daily breakdown)
- EXTRACTION_SCOPE.md (decisions + rationale)
- EXTRACTION_SECTION_PLANNER.md (phase tracking)
- API documentation (endpoint specs)
- Component documentation (frontend guide)
- Deployment guide (production setup)

## 5. Risks & Assumptions

### Assumptions
- ✅ **Ingestion complete**: 18+ grants in database, embeddings generated
- ✅ **Supabase access**: PostgreSQL connection working
- ✅ **ARTISTING access**: Can modify Django backend + Next.js frontend
- ✅ **Design system**: ARTISTING components available for reuse
- ✅ **Auth system**: ARTISTING authentication already working
- ✅ **Gemini API**: API key available and working
- ⚠️ **GPT-4o API**: Need key if using fallback model

### Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| **Supabase connection issues** | High | Low | Test connection first, Docker network isolation |
| **Search performance slow** | Medium | Low | HNSW index exists, add caching if needed |
| **LLM cost overrun** | Low | Medium | Start with Gemini Flash, monitor usage |
| **Frontend integration complexity** | Medium | Medium | Reuse ARTISTING patterns, minimal custom code |
| **Model switching difficulty** | Low | Low | Abstraction layer makes switching trivial |
| **Security vulnerability** | High | Low | Read-only user, input validation, credentials in env |

## 6. Technical Decisions (Summary)

### Decided (from planning session)
- ✅ **Embedding model**: Gemini text-embedding-004 (768-dim) - keep existing
- ✅ **PDF display**: Multi-tab (markdown default, PDF iframe, download)
- ✅ **Context size**: Top 5 grants for chat responses
- ✅ **Clarification triggers**: Too many (>20) or too few (<3) results
- ✅ **Chat models**: Tiered (Gemini Flash → GPT-4o → fallback)
- ✅ **Database connection**: Direct (Option A) with read-only user
- ✅ **Pagination**: Session-based, 5 results per page
- ✅ **Progressive loading**: Summary first, full details on demand

**See EXTRACTION_SCOPE.md for detailed rationale**

## 7. Integration with ARTISTING

### What Exists (Reuse)
- ✅ Next.js 15 + React 19 + TypeScript
- ✅ shadcn/ui component library
- ✅ Tailwind CSS styling
- ✅ Authentication system
- ✅ User management
- ✅ Chat interface at `/chat`
- ✅ Design system (colors, fonts, spacing)

### What We Build (New)
- 🆕 `apps/grants/` Django app
- 🆕 Grant search/chat API endpoints
- 🆕 Frontend grant components
- 🆕 PDF viewer component
- 🆕 Search results page

### Integration Points
1. **Backend**: Add `apps/grants/` to ARTISTING Django backend
2. **Frontend**: Add grant components to existing Next.js app
3. **Chat**: Modify existing chat UI to support grants mode
4. **Database**: Connect to existing Supabase PostgreSQL (read-only)

## 8. Next Actions

| Owner | Task | Status | Due |
|-------|------|--------|-----|
| Claude | ✅ Create EXTRACTION_PROJECT_PLAN.md | Done | Day 1 |
| Claude | Create EXTRACTION_SPRINT_PLAN.md | In Progress | Day 1 |
| Claude | Create EXTRACTION_SCOPE.md | Pending | Day 1 |
| Claude | Create EXTRACTION_SECTION_PLANNER.md | Pending | Day 1 |
| You | Verify Supabase read-only user exists | Pending | Day 1 |
| You | Provide GPT-4o API key (if using) | Pending | Day 1 |
| Claude | Create Django grants app structure | Pending | Day 2 |
| Claude | Implement search endpoint | Pending | Day 2 |
| Claude | Implement chat endpoint | Pending | Day 2-3 |
| Claude | Create frontend components | Pending | Day 4-5 |
| Codex | Test all scenarios | Pending | Day 6 |

---

**Last Updated**: 2025-12-03
**Status**: Day 1 - Documentation in progress
**Next Session**: Complete remaining docs, start Django implementation