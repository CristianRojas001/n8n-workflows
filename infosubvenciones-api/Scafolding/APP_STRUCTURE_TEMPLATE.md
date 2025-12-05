# App Structure Template

> Purpose: give the assistant a concrete map of the repo. Fill this with the directories, technologies, and responsibilities you plan to use. Update whenever structure changes.

## 1. Tech Stack Summary
- **Frontend**: _Framework + language + key libs (e.g., Next.js + TypeScript + Tailwind)._
- **Backend**: _Framework + language + ORM + API style._
- **AI/RAG stack**: _LLM provider, embedding model, retrieval store._
- **Data stores**: _Primary DB, cache, message broker._
- **Infra tooling**: _Containerization, CI/CD, infra as code._

## 2. Root Layout
```
repo-root/
├─ backend/              # _Server app (describe framework + key apps)._
├─ frontend/             # _Web client (list app router/components)._
├─ docs/                 # _Architecture references._
├─ scripts/              # _Automation (setup, deploy, data tooling)._
├─ infrastructure/       # _IaC, docker compose, monitoring configs._
└─ Cristian_work/        # _Research notes / analyses (optional)._
```

## 3. Backend Modules
| Path | Purpose | Notes |
|------|---------|-------|
| `backend/app_name/` | _e.g., auth, chat, billing._ | _Dependencies, signals, Celery tasks._ |
| `backend/config/` | _settings split by env, Celery, logging._ | _Env vars required._ |
| `backend/tests/` | _Pytest structure + fixtures._ | _How to run tests._ |

## 4. Frontend Modules
| Path | Purpose | Notes |
|------|---------|-------|
| `frontend/app/(segment)` | _Routes/pages for marketing, auth, dashboard, support._ | _SSR/CSR behavior._ |
| `frontend/lib/services` | _Typed API clients + shared fetch helpers._ | _Base URL conventions._ |
| `frontend/contexts` | _Auth, language, theme providers._ | _Storage strategy, hydration notes._ |
| `frontend/components` | _Reusable UI kits, layouts, widgets._ | _Design tokens / styling system._ |

## 5. Shared Utilities & Scripts
- **`scripts/setup_backend.sh`** – _Installs dependencies, runs migrations._
- **`scripts/setup_frontend.sh`** – _Node install/build/start steps._
- **`scripts/deploy.sh`** – _Combined deployment flow; mention target environment._

## 6. Environment Variables
| Name | Description | Required? | Default/Example |
|------|-------------|-----------|-----------------|
| `DATABASE_URL` | _Primary DB connection string._ | Y | `postgres://...` |
| `LLM_API_KEY` | _Key for chosen LLM provider._ | Y |  |
| ... | | | |

## 7. API Surface
Document major endpoints so assistants can reason about them.
| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/v1/auth/login/` | POST | _Login flow._ | Public |
| `/api/v1/chat/stream/` | POST/SSE | _LLM chat streaming._ | JWT |
| `/api/v1/billing/...` | ... | ... | ... |

## 8. Testing & Tooling
- **Linters/formatters**: _ESLint, Ruff, etc._
- **Test commands**: `_npm run test`, `pytest`, etc._
- **CI pipelines**: _Describe steps if already defined._

Keep this template synchronized with reality—assistants will reference it to choose file paths and technologies automatically.
