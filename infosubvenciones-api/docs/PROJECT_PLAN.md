# InfoSubvenciones Project Plan

> Purpose: align everyone (and the assistant) on goals, scope, and sequence. Treat this as the single source of truth for priorities.

## 1. Vision & Success Criteria

### Problem Statement
Spanish freelancers and SMEs in culture and commerce sectors struggle with:
1. **Grants Discovery**: Official InfoSubvenciones portal has 136k+ grants but lacks semantic search, AI assistance, and easy filtering
2. **Legal/Tax Questions**: Need expert advice on legal, fiscal, and labor matters specific to their sector

This leads to missed funding opportunities and costly legal/tax mistakes.

### High-Level Outcome
Build **two integrated RAG systems within ARTISTING**:

#### System 1: InfoSubvenciones RAG
AI-powered grant discovery that enables users to:
1. Search grants using natural language queries ("ayudas para autónomos de artes escénicas en Madrid")
2. Filter by sector, region, budget, deadlines
3. Get AI-generated summaries in Spanish
4. Access original PDFs with citations
5. Chat with AI about specific grants

#### System 2: Legal RAG
AI-powered legal/tax advisor that enables users to:
1. Ask questions about legal, fiscal, and labor regulations
2. Get answers based on BOE, CENDOJ, and PETETE official sources
3. Receive contextualized advice with citations
4. Minimize hallucinations through proper legal reasoning

### Success Metrics (KPIs)
- **Data Coverage**: 136,920 grants ingested (Cultura: 105,139 + Comercio: 31,781)
- **Ingestion Success Rate**: >95% of PDFs processed successfully
- **Search Quality**: <2s response time for semantic queries
- **Data Freshness**: Initial load complete, future updates monthly/quarterly
- **User Adoption**: Track search queries, grant views, PDF downloads
- **Cost Efficiency**: Stay within ~$75 budget for initial ingestion

### Non-Negotiables
- **Data Accuracy**: All summaries must be faithful to source PDFs, no hallucinations
- **Performance**: Search results <2s, UI responsive on mobile
- **Accessibility**: Public access (no login required for MVP)
- **Citations**: Every AI response must cite source convocatoria + PDF
- **Privacy**: No user data collection beyond anonymous analytics (for now)
- **Modularity**: Architecture must allow future integration with ARTISTING main app
- **Cost Control**: Monitor LLM API usage, use Gemini free tier where possible

## 2. Stakeholders & Roles

- **Product Owner**: You (Cristian) - defines priorities, validates features
- **Tech Lead**: You + Claude - architecture, implementation, deployment
- **AI/RAG Owner**: Claude - ingestion pipeline, embeddings, semantic search
- **Design/UX**: Reuse ARTISTING design system, adapt for grants search
- **Data Provider**: InfoSubvenciones API (official government source)
- **Infrastructure**: PostgreSQL + pgvector + Redis (to be verified)

## 3. Timeline & Milestones

### Two-Milestone Delivery Structure

**HITO 1 - Pre-producción (21 días)**: €1,500 (1 revision)
- Prototypes with subset of data (10 → 100 → 1,000 grants)
- Both InfoSubvenciones + Legal RAG working with subsets
- Integration with existing ARTISTING chat interface

**HITO 2 - Producción (21 días)**: €2,000 (2 revisions)
- Full corpus integration (136k grants + full legal corpus)
- Production deployment
- 30 days post-launch support

---

| Milestone | Week | Definition of Done | Deliverable |
|-----------|------|-------------------|-------------|
| **Kickoff** | Day 1 | ✅ Docs completed, scope clarified, infrastructure verified | Planning complete |
| **Foundation** | Week 1 | Ingestion working with 10 grants, then 100 grants | First working prototype |
| **Milestone 1 Prototype** | Week 2-3 | 1,000 grants ingested, Legal RAG prototype (subset), Chat integration | €1,500 + working chat |
| **Milestone 2 Start** | Week 4 | Full 136k grants ingestion running | Data pipeline at scale |
| **Legal RAG Production** | Week 5 | Full BOE/CENDOJ/PETETE ingested, optimized | Complete legal system |
| **Production Launch** | Week 6 | Both systems deployed, tested, documented | €2,000 + 30-day support |

## 4. Scope Breakdown

### 1. Data Ingestion Pipeline (Backend - Python/Celery)
**Purpose**: Ingest 136k grants from InfoSubvenciones API, process PDFs, generate embeddings

**Components**:
- API fetcher (paginated, handles 105k+ items for finalidad=11, 31k+ for finalidad=14)
- PDF downloader + converter (pymupdf + marker fallback)
- LLM processor (Gemini 2.0 Flash: summaries + field extraction)
- Embedding generator (OpenAI text-embedding-3-small)
- PostgreSQL storage (convocatorias, pdf_extractions, embeddings, staging_items)
- Celery workers + Redis broker
- Error handling + retry logic (3 retries, exponential backoff)

**Dependencies**: PostgreSQL with pgvector, Redis, Gemini API key ✅, OpenAI API key

**Constraints**:
- Must handle multilingual PDFs (Spanish, Catalan, Basque, Galician) → summaries always Spanish
- Deduplication by PDF hash to avoid reprocessing
- Track processing status per item (staging_items table)

### 2. Search API (Backend - Django REST Framework)
**Purpose**: Expose RESTful API for semantic search + filtering

**Endpoints**:
- `POST /api/v1/grants/search` - Semantic search with optional filters
- `GET /api/v1/grants/<numero_convocatoria>` - Grant detail with metadata
- `GET /api/v1/grants/<numero_convocatoria>/pdf` - Download original PDF
- `GET /api/v1/grants/filters` - Get available filter options (sectors, regions, organismo)
- `GET /api/v1/health` - Health check

**Features**:
- pgvector similarity search on embeddings
- Filter by: sector, region, organo (nivel1/2/3), budget range, deadline, abierto status
- Pagination (default 20 results)
- Response includes: summary, metadata, citation, relevance score

**Dependencies**: Ingestion pipeline completed, Django REST Framework, CORS for frontend

**Constraints**:
- No authentication required (public API for MVP)
- Rate limiting (optional for later)
- CORS headers for Next.js frontend

### 3. Search UI (Frontend - Next.js)
**Purpose**: User-facing web app for discovering grants

**Pages**:
- Landing page with search bar + featured grants
- Search results page (list view with filters sidebar)
- Grant detail page (summary + metadata + PDF viewer/download)
- About/Help page (how to use, data source info)

**Components**:
- SearchBar (natural language input)
- FilterPanel (sector, region, budget, dates)
- ResultsGrid (grant cards with summary + CTA)
- GrantDetailView (full metadata + PDF link)
- CitationBadge (links to source convocatoria)

**Branding**: Reuse ARTISTING design system (Shadcn/UI, Tailwind, same colors/fonts)

**Dependencies**: Search API deployed, ARTISTING frontend code for reference

**Constraints**:
- Mobile-first responsive design
- No login required
- Public access
- SSR for SEO

### 4. Monitoring & Observability (Backend - Scripts/Dashboards)
**Purpose**: Track ingestion progress, search performance, data quality

**Tools**:
- PostgreSQL queries for ingestion stats (progress report script)
- Celery Flower for task monitoring (optional)
- Django admin for manual data inspection
- Log files (structured JSON logging)

**Metrics**:
- Ingestion: items/hour, error distribution, retry stats
- Search: query latency, result relevance, popular filters
- Data: summary word count, field extraction completeness

**Dependencies**: Ingestion pipeline, Search API

### 5. Legal RAG System (Backend - Python/Celery + Django REST)
**Purpose**: Separate RAG system for legal, fiscal, and labor advice

**Components**:
- Separate ingestion pipeline for legal documents
- BOE API integration (official Spanish legal bulletin)
- CENDOJ integration (judicial documentation center)
- PETETE integration (binding tax consultations)
- Separate PostgreSQL database (`legal_rag`)
- Legal reasoning prompts (minimize hallucinations)
- Same embedding strategy (OpenAI text-embedding-3-small)
- Django REST API endpoints for legal queries

**Integration**:
- Connects to same ARTISTING chat UI (separate mode)
- Reuses authentication from ARTISTING
- Separate from grants system (different data model)

**Dependencies**: InfoSubvenciones system completed first (Week 3), reuse ingestion patterns

**Constraints**:
- Must avoid hallucinations (legal advice requires accuracy)
- Different chunking strategy (legal documents are different from grants)
- Separate database (different schema, separate concerns)

### 6. ARTISTING Integration (Existing Platform)
**Purpose**: Integrate both RAG systems into existing ARTISTING platform

**Existing Components (Reuse, Don't Rebuild)**:
- User authentication & registration (already exists)
- User profiles & CRM (already exists)
- Admin panel (already exists)
- Chat UI at chat.artisting.es (already exists)
- Design system (Shadcn/UI, Tailwind)

**New Integration Points**:
- Grants search API → ARTISTING chat backend
- Legal RAG API → ARTISTING chat backend
- Two chat modes: "Grants" and "Legal Advice"
- API endpoints accessible from existing chat interface

**Implementation**:
- Add `apps/grants/` to ARTISTING Django backend
- Add `apps/legal_rag/` to ARTISTING Django backend
- Modify existing chat UI to support two RAG backends
- No new frontend pages needed

**Dependencies**: Access to ARTISTING-main codebase

### 7. Newsletters (External - n8n)
**Purpose**: Automated weekly/monthly grant bulletins

**Implementation**: Handled separately in n8n (not part of this project)

**Integration**: n8n queries our grants API to generate newsletters

**Our Role**: Provide API endpoints, document them, mention in docs only

### 8. Documentation & Setup (Docs + Scripts)
**Purpose**: Enable future developers to understand and extend the system

**Deliverables**:
- APP_STRUCTURE.md (architecture with ARTISTING integration)
- RAG_PIPELINE.md (both InfoSubvenciones + Legal RAG)
- SCOPE_CHANGES.md (clarifications from contract)
- PROGRESS_LOG.md (session notes)
- setup scripts (database init, dependency install)
- README for each subsystem (Ingestion/, LegalIngestion/, integration/)

**Dependencies**: None (parallel track)

## 5. Risks & Assumptions

### Assumptions
- ✅ **PostgreSQL + pgvector available**: Confirmed ready
- ✅ **Gemini API key available**: Confirmed
- ⚠️ **Redis available**: To be verified (see Next Actions)
- **InfoSubvenciones API stable**: No breaking changes during ingestion (risk: government API downtime)
- **PDF quality**: Most PDFs are machine-readable text (not scanned images)
- **LLM cost**: Gemini free tier covers most processing (~$70 if paid)
- **Future integration**: ARTISTING Django backend can consume same PostgreSQL database

### Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| **InfoSubvenciones API changes/downtime** | High | Medium | Implement robust retry logic, cache responses, monitor API health |
| **PDF conversion failures** | Medium | Medium | Two-tier fallback (pymupdf → marker), skip if both fail, manual review of failures |
| **Gemini rate limits** | Medium | Low | Use free tier limits, batch processing, exponential backoff, fallback to GPT-4o-mini |
| **Embedding cost overrun** | Low | Low | OpenAI embeddings cheap ($1.23 total), monitor usage |
| **Search performance degradation** | High | Low | pgvector HNSW index, optimize queries, cache popular searches |
| **Redis not installed** | Medium | Medium | Verify in Foundation phase, install if needed, use Docker if complex |
| **Future ARTISTING merge complexity** | Medium | Medium | Design modular API from day 1, use Django REST Framework (same as ARTISTING), shared DB design |
| **Data quality issues (LLM hallucinations)** | High | Medium | Prompt engineering, validation checks, manual QA on sample, confidence scores |

## 6. Open Questions

### Resolved (Updated Scope)
- ✅ Use Django REST Framework (matches ARTISTING)
- ✅ Reuse ARTISTING branding and design system
- ✅ **Authentication**: Reuse existing ARTISTING auth (not building from scratch)
- ✅ **Integration approach**: Add to ARTISTING backend, not standalone
- ✅ **Two systems**: InfoSubvenciones + Legal RAG (separate databases)
- ✅ **Milestone delivery**: Prototype (subset) then Production (full corpus)
- ✅ **Progressive testing**: 10 → 100 → 1,000 → 136k grants
- ✅ **Newsletters**: Handled in n8n separately (out of scope)
- ✅ **Reference**: ARTISTING design, fandit.es functionality already in ingestion_strategy.md
- ✅ **Chat UI**: Existing chat.artisting.es (just integrate backend)

### To Be Resolved
- ⚠️ **Redis installation status** - Need to verify Day 2
- ⚠️ **Access to ARTISTING-main codebase** - Need Git access
- **Ingestion schedule**: One-time load or periodic updates? (Monthly/quarterly refresh?)
- **Legal RAG data sources**: Exact BOE/CENDOJ/PETETE API endpoints and access
- **Error notification**: Email alerts for ingestion failures or just logs?
- **PDF storage**: Keep all PDFs locally or download on-demand? (Estimate 50GB for 205k PDFs)
- **Backup strategy**: Database backup frequency, restore process
- **Legal RAG chunking**: How to chunk legal documents (different from grants)

## 7. Next Actions

| Owner | Task | Status | Due |
|-------|------|--------|-----|
| Claude | ✅ Fill PROJECT_PLAN.md | Done | Today |
| Claude | Fill APP_STRUCTURE_TEMPLATE.md | In Progress | Today |
| Claude | Fill RAG_PIPELINE_TEMPLATE.md | Pending | Today |
| Claude | Fill UX_SURFACES_TEMPLATE.md | Pending | Today |
| You | Verify Redis installation (`redis-cli ping`) | Pending | Foundation Week |
| Claude | Create Ingestion/ project structure | Pending | Foundation Week |
| Claude | Initialize Django API project (api/) | Pending | Foundation Week |
| Claude | Set up database schema (run init_db.py) | Pending | Foundation Week |
| You | Provide OpenAI API key (if not already in env) | Pending | Foundation Week |
| Claude | Test API client with 10 grants | Pending | Foundation Week |
| You | Review ingestion results (1,000 item test) | Pending | Week 2-3 |
| You | Review frontend beta (search + filters) | Pending | Week 4-5 |
| You | Decide on domain name for public launch | Pending | Before GA |

---

**Last Updated**: 2025-12-01
**Status**: Kickoff - Templates in progress
**Next Session**: Fill APP_STRUCTURE, RAG_PIPELINE, UX_SURFACES templates
