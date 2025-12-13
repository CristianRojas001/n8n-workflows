# InfoSubvenciones App Structure

> Purpose: give the assistant a concrete map of the repo. This document describes the complete architecture of the InfoSubvenciones grant discovery platform.

## 1. Tech Stack Summary

- **Frontend**: Next.js 15.2.4 + TypeScript + Shadcn/UI + Tailwind CSS + Radix UI
- **Backend**: Django 5.0+ REST Framework + Python 3.11+ + SQLAlchemy (for ingestion) + psycopg2
- **AI/RAG stack**:
  - LLM: Google Gemini 2.0 Flash (summaries + extraction)
  - Embeddings: OpenAI text-embedding-3-small (1536 dimensions)
  - Vector store: PostgreSQL with pgvector extension (HNSW index)
- **Data stores**:
  - Primary DB: PostgreSQL 15+ with pgvector
  - Cache: Redis 7+ (Celery broker + optional query cache)
  - File storage: Local filesystem (PDFs + Markdown)
- **Task Queue**: Celery 5.3+ with Redis broker
- **Infra tooling**: Docker (optional for PostgreSQL/Redis), systemd/supervisor for production, Git for version control

## 2. Root Layout

```
infosubvenciones-api/
├─ Ingestion/              # Standalone ingestion pipeline (Python/Celery)
│  ├─ config/              # Settings, database, Celery config
│  ├─ models/              # SQLAlchemy models (staging, convocatorias, embeddings)
│  ├─ schemas/             # Pydantic validation schemas
│  ├─ services/            # API client, PDF processor, LLM, embeddings
│  ├─ tasks/               # Celery tasks (fetcher, processor, embedder)
│  ├─ utils/               # Logging, hashing, retry logic
│  ├─ scripts/             # DB init, run ingestion, test pipeline, stats
│  ├─ migrations/          # Alembic migrations
│  ├─ data/                # Local storage (pdfs/, markdown/)
│  ├─ tests/               # Pytest unit/integration tests
│  ├─ requirements.txt     # Python dependencies
│  ├─ .env.example         # Environment template
│  └─ README.md            # Ingestion setup guide
│
├─ api/                    # Django REST API (search + grants endpoints)
│  ├─ grants_api/          # Main Django project
│  │  ├─ settings.py       # Django settings (prod/dev split)
│  │  ├─ urls.py           # URL routing
│  │  ├─ wsgi.py / asgi.py # Server interfaces
│  ├─ apps/
│  │  ├─ common/           # APIResponse, error handlers
│  │  ├─ grants/           # Grant models, views, serializers
│  │  │  ├─ models.py      # Django models (read-only proxy to Ingestion DB)
│  │  │  ├─ views.py       # Search, detail, filters, PDF download
│  │  │  ├─ serializers.py # DRF serializers
│  │  │  ├─ urls.py        # /api/v1/grants/* routes
│  │  │  └─ services.py    # Vector search service, filter builders
│  ├─ requirements.txt     # Django dependencies
│  ├─ manage.py            # Django management
│  └─ README.md            # API setup guide
│
├─ frontend/               # Next.js search UI (reuses ARTISTING design)
│  ├─ app/                 # Next.js 15 App Router
│  │  ├─ page.tsx          # Landing page with search
│  │  ├─ search/           # Search results page
│  │  │  ├─ page.tsx       # Results grid + filters
│  │  │  └─ [id]/          # Grant detail page
│  │  ├─ about/            # About/Help page
│  │  ├─ layout.tsx        # Root layout with ARTISTING branding
│  │  └─ globals.css       # Global styles
│  ├─ components/
│  │  ├─ ui/               # Shadcn/UI components (from ARTISTING)
│  │  ├─ search/           # SearchBar, FilterPanel, ResultsGrid
│  │  ├─ grants/           # GrantCard, GrantDetail, CitationBadge
│  │  └─ layout/           # Header, Footer, Navigation
│  ├─ lib/
│  │  ├─ services/         # API clients (base, grants service)
│  │  │  ├─ base.service.ts    # Base HTTP service
│  │  │  ├─ grants.service.ts  # Grants API client
│  │  │  ├─ config.ts          # API config
│  │  │  └─ index.ts           # Exports
│  │  ├─ utils.ts          # Utility functions
│  │  └─ types.ts          # TypeScript types
│  ├─ package.json         # Node dependencies
│  ├─ tsconfig.json        # TypeScript config
│  ├─ tailwind.config.ts   # Tailwind config (ARTISTING theme)
│  ├─ next.config.js       # Next.js config
│  └─ README.md            # Frontend setup guide
│
├─ docs/                   # Architecture documentation
│  ├─ PROJECT_PLAN.md      # Vision, milestones, scope
│  ├─ APP_STRUCTURE.md     # This file
│  ├─ RAG_PIPELINE.md      # Ingestion pipeline details
│  ├─ UX_SURFACES.md       # UI design specs
│  ├─ PROGRESS_LOG.md      # Session journal
│  ├─ ingestion_strategy.md # Original technical strategy
│  ├─ *_TEMPLATE.md        # Templates for future use
│  └─ info/                # Source documents (customer needs, API fields)
│
├─ scripts/                # Automation scripts
│  ├─ install_dependencies.sh  # System packages (PostgreSQL, Redis, Python, Node)
│  ├─ setup_ingestion.sh       # Python venv, pip install, DB init
│  ├─ setup_api.sh             # Django setup, migrations
│  ├─ setup_frontend.sh        # npm install, build
│  ├─ start_celery.sh          # Start Celery workers + beat
│  ├─ start_api.sh             # Start Django API server
│  ├─ start_frontend.sh        # Start Next.js dev/prod server
│  ├─ start_all.sh             # Combined startup
│  └─ deploy.sh                # Production deployment
│
├─ ARTISTING-main/         # Reference - original ARTISTING codebase
│  └─ (Reuse design system, components, branding)
│
├─ .gitignore              # Git ignore (venvs, .env, data/, node_modules)
├─ README.md               # Project overview + quick start
└─ .env                    # Environment variables (gitignored)
```

## 3. Backend Modules

### Ingestion Pipeline (Python/Celery)

| Path | Purpose | Notes |
|------|---------|-------|
| `Ingestion/config/settings.py` | Central configuration (loads .env, validates) | DATABASE_URL, REDIS_URL, API keys |
| `Ingestion/config/database.py` | SQLAlchemy engine, session management | Connection pooling, async support |
| `Ingestion/config/celery_app.py` | Celery configuration, task routing | 3 queues: fetcher, processor, embedder |
| `Ingestion/models/staging.py` | StagingItem model (processing tracker) | Status tracking, error handling, retries |
| `Ingestion/models/convocatoria.py` | Convocatoria model (API metadata) | 40+ fields, JSONB arrays for sectors/regions |
| `Ingestion/models/pdf_extraction.py` | PDFExtraction model (PDF-only fields) | 20+ fields extracted by LLM |
| `Ingestion/models/embedding.py` | Embedding model (vectors + summaries) | pgvector(1536), metadata JSONB |
| `Ingestion/services/api_client.py` | InfoSubvenciones API client | Pagination, retry logic, rate limiting |
| `Ingestion/services/pdf_processor.py` | PDF download + conversion | pymupdf → markdown, marker fallback |
| `Ingestion/services/llm_service.py` | Gemini integration | Summaries (200-250 words) + field extraction |
| `Ingestion/services/embedding_service.py` | OpenAI embeddings | text-embedding-3-small, batch processing |
| `Ingestion/services/deduplication.py` | PDF hash checking | SHA256, skip duplicates |
| `Ingestion/tasks/fetcher.py` | Celery: Fetch from API | Finalidad 11+14, pagination, insert DB |
| `Ingestion/tasks/processor.py` | Celery: Process PDFs | Download → convert → LLM → extract |
| `Ingestion/tasks/embedder.py` | Celery: Generate embeddings | Summary → OpenAI → pgvector |
| `Ingestion/tasks/retry_handler.py` | Celery: Retry failed items | Scheduled task (every 30 min), exponential backoff |
| `Ingestion/scripts/init_db.py` | Create database schema | Run first, creates all tables + indexes |
| `Ingestion/scripts/run_ingestion.py` | Main orchestrator | Start full ingestion (136k items) |
| `Ingestion/scripts/test_pipeline.py` | Test with N items | Validate pipeline with small batch |
| `Ingestion/scripts/export_stats.py` | Progress reporting | Show completion %, errors, ETA |
| `Ingestion/tests/` | Pytest tests | Unit tests (80% coverage), integration tests |

### Django REST API

| Path | Purpose | Notes |
|------|---------|-------|
| `api/grants_api/settings.py` | Django settings | CORS, DRF, database (same as Ingestion) |
| `api/apps/common/responses.py` | APIResponse class | Consistent response format |
| `api/apps/common/exceptions.py` | Custom exception handlers | 400/404/500 error formatting |
| `api/apps/grants/models.py` | Django models | Read-only proxies to Ingestion DB tables |
| `api/apps/grants/views.py` | API views | SearchView, DetailView, FiltersView, PDFView |
| `api/apps/grants/serializers.py` | DRF serializers | GrantSerializer, SearchRequestSerializer |
| `api/apps/grants/services.py` | Business logic | VectorSearchService, FilterBuilder |
| `api/apps/grants/urls.py` | URL routing | /api/v1/grants/* |
| `api/apps/grants/pagination.py` | Custom pagination | 20 results/page default |
| `api/tests/` | Django tests | API endpoint tests, search tests |

## 4. Frontend Modules

| Path | Purpose | Notes |
|------|---------|-------|
| `frontend/app/page.tsx` | Landing page | Hero, search bar, featured grants, how it works |
| `frontend/app/search/page.tsx` | Search results | Grid + filters sidebar, pagination |
| `frontend/app/search/[id]/page.tsx` | Grant detail | Full metadata, summary, PDF link, citations |
| `frontend/app/about/page.tsx` | About/Help | Data source info, usage guide, contact |
| `frontend/app/layout.tsx` | Root layout | ARTISTING branding, nav, footer, SEO meta |
| `frontend/components/search/SearchBar.tsx` | Search input | Natural language queries, autocomplete (future) |
| `frontend/components/search/FilterPanel.tsx` | Filters sidebar | Sector, region, budget, dates, organo |
| `frontend/components/search/ResultsGrid.tsx` | Results display | Grant cards, loading states, empty state |
| `frontend/components/grants/GrantCard.tsx` | Grant preview | Summary, key metadata, CTA |
| `frontend/components/grants/GrantDetail.tsx` | Full grant view | All fields, PDF viewer, citations |
| `frontend/components/grants/CitationBadge.tsx` | Source citation | Link to convocatoria, PDF download |
| `frontend/components/ui/*` | Shadcn/UI components | Button, Card, Input, Select, Badge (from ARTISTING) |
| `frontend/lib/services/grants.service.ts` | Grants API client | search(), getDetail(), getFilters(), downloadPDF() |
| `frontend/lib/types.ts` | TypeScript types | Grant, SearchRequest, SearchResponse, Filters |
| `frontend/lib/utils.ts` | Utility functions | formatDate, formatCurrency, cn() for classnames |

## 5. Shared Utilities & Scripts

- **`scripts/install_dependencies.sh`** – Installs PostgreSQL, Redis, Python 3.11+, Node 18+, system packages
- **`scripts/setup_ingestion.sh`** – Creates Python venv, installs requirements, runs init_db.py
- **`scripts/setup_api.sh`** – Sets up Django, runs migrations, creates superuser (optional)
- **`scripts/setup_frontend.sh`** – Runs npm install, builds Next.js
- **`scripts/start_celery.sh`** – Starts 3 Celery workers (fetcher, processor, embedder) + beat scheduler
- **`scripts/start_api.sh`** – Starts Django API server (port 8000)
- **`scripts/start_frontend.sh`** – Starts Next.js (port 3000, dev or prod mode)
- **`scripts/start_all.sh`** – Combined startup for all services
- **`scripts/stop_all.sh`** – Stop all services gracefully
- **`scripts/deploy.sh`** – Production deployment (build, migrate, restart services)

## 6. Environment Variables

| Name | Description | Required? | Default/Example |
|------|-------------|-----------|-----------------|
| **Ingestion & API (shared)** | | | |
| `DATABASE_URL` | PostgreSQL connection string | Y | `postgresql://user:pass@localhost:5432/infosubvenciones` |
| `REDIS_URL` | Redis connection string | Y | `redis://localhost:6379/0` |
| `GEMINI_API_KEY` | Google Gemini API key | Y | `AIza...` |
| `OPENAI_API_KEY` | OpenAI API key | Y | `sk-...` |
| **Ingestion specific** | | | |
| `API_BASE_URL` | InfoSubvenciones API | N | `https://www.infosubvenciones.es/bdnstrans/api` |
| `BATCH_SIZE` | Items per API page | N | `100` |
| `MAX_WORKERS` | Celery concurrency | N | `10` |
| `PDF_STORAGE_PATH` | Local PDF directory | N | `./data/pdfs` |
| `MARKDOWN_STORAGE_PATH` | Local markdown directory | N | `./data/markdown` |
| `GEMINI_MODEL` | Gemini model name | N | `gemini-2.5-flash-lite` |
| `EMBEDDING_MODEL` | OpenAI embedding model | N | `text-embedding-3-small` |
| `MAX_RETRIES` | Retry attempts | N | `3` |
| `LOG_LEVEL` | Logging level | N | `INFO` |
| **Django API specific** | | | |
| `DJANGO_SECRET_KEY` | Django secret key | Y | (generate random) |
| `DJANGO_DEBUG` | Debug mode | N | `False` |
| `DJANGO_ALLOWED_HOSTS` | Allowed hosts | Y | `localhost,127.0.0.1,yourdomain.com` |
| `CORS_ALLOWED_ORIGINS` | CORS origins | Y | `http://localhost:3000,https://yourdomain.com` |
| **Frontend specific** | | | |
| `NEXT_PUBLIC_API_URL` | Backend API URL | Y | `http://localhost:8000/api/v1` |
| `NEXT_PUBLIC_SITE_NAME` | Site name | N | `InfoSubvenciones by ARTISTING` |

## 7. API Surface

### Ingestion Pipeline (Internal)

No external API - Celery tasks communicate via Redis/database.

### Django REST API (Public)

| Endpoint | Method | Description | Auth | Response |
|----------|--------|-------------|------|----------|
| `/api/v1/health/` | GET | Health check | None | `{"status": "ok", "db": "connected"}` |
| `/api/v1/grants/search/` | POST | Semantic search + filters | None | `SearchResponse` (grants array, total, page) |
| `/api/v1/grants/<numero>/` | GET | Grant detail | None | Full grant metadata + summary |
| `/api/v1/grants/<numero>/pdf/` | GET | Download PDF | None | Binary PDF file or redirect |
| `/api/v1/grants/filters/` | GET | Available filter options | None | Sectors, regions, organos lists |

**Search Request Body** (POST `/api/v1/grants/search/`):
```json
{
  "query": "ayudas para autónomos de artes escénicas en Madrid",
  "filters": {
    "sectores": ["R - Actividades artísticas"],
    "regiones": ["ES300 - Madrid"],
    "organo_nivel1": "ESTADO",
    "presupuesto_min": 5000,
    "presupuesto_max": 50000,
    "fecha_fin_after": "2025-12-01",
    "abierto": true
  },
  "page": 1,
  "page_size": 20
}
```

**Search Response**:
```json
{
  "code": 200,
  "is_success": true,
  "message": "Search successful",
  "data": {
    "results": [
      {
        "numero_convocatoria": "871838",
        "descripcion": "...",
        "summary": "...",
        "relevance_score": 0.87,
        "organo_nivel1": "ESTADO",
        "sectores": ["R - Actividades artísticas"],
        "presupuesto_total": 50000.00,
        "fecha_fin_solicitud": "2025-12-31",
        "abierto": true,
        "pdf_url": "/api/v1/grants/871838/pdf/"
      }
    ],
    "total": 234,
    "page": 1,
    "page_size": 20,
    "total_pages": 12
  }
}
```

## 8. Testing & Tooling

### Linters/Formatters
- **Backend (Python)**: Black (formatting), Ruff (linting), isort (import sorting)
- **Frontend (TypeScript)**: ESLint, Prettier

### Test Commands
- **Ingestion**: `pytest Ingestion/tests/ -v --cov=Ingestion`
- **API**: `python api/manage.py test apps.grants`
- **Frontend**: `npm run test` (future - Jest + React Testing Library)
- **Integration**: `python Ingestion/scripts/test_pipeline.py --limit 10`

### Running Locally
```bash
# Terminal 1 - Start Redis (if not running as service)
redis-server

# Terminal 2 - Start Celery workers
./scripts/start_celery.sh

# Terminal 3 - Start Django API
./scripts/start_api.sh

# Terminal 4 - Start Next.js frontend
./scripts/start_frontend.sh

# Access:
# Frontend: http://localhost:3000
# API: http://localhost:8000/api/v1
# Django Admin: http://localhost:8000/admin
```

### CI/CD Pipeline (Future)
- **Linting**: Black, Ruff, ESLint on every commit
- **Testing**: Pytest + Django tests on PR
- **Build**: Next.js production build
- **Deploy**: SSH to server, pull, migrate, restart services

## 9. Data Flow Summary

```
InfoSubvenciones API
        ↓
   [Ingestion Pipeline]
   → Fetcher: API → staging_items + convocatorias
   → Processor: PDF → markdown → Gemini → pdf_extractions
   → Embedder: Summary → OpenAI → embeddings
        ↓
   PostgreSQL (pgvector)
   ↓           ↓
[Django API]  [Django Admin]
   ↓
[Next.js UI] ← User searches
```

## 10. Modularity & Future Integration

### Design for ARTISTING Merge
The system is designed to be **modular** and **exchangeable**:

1. **Shared Database**: Both systems can read from same PostgreSQL (grants data is read-only for ARTISTING)
2. **API Layer**: Django REST API can be consumed by ARTISTING frontend or integrated as Django app
3. **Decoupled Frontend**: Next.js UI can be:
   - Standalone website (current)
   - Embedded in ARTISTING as `/grants` route
   - Replaced by ARTISTING's React components consuming same API
4. **No Authentication Coupling**: No user accounts in grants system, easy to add ARTISTING auth later

### Integration Options (Future)
- **Option A (Lightweight)**: ARTISTING frontend calls grants API, keeps separate Next.js UI
- **Option B (Medium)**: Add `grants` Django app to ARTISTING backend, share database
- **Option C (Full)**: Migrate Next.js components to ARTISTING frontend, unified navigation

---

**Last Updated**: 2025-12-01
**Status**: Initial structure defined, ready for implementation
**Next Step**: Fill RAG_PIPELINE.md template
