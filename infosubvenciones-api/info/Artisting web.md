# ARTISTING Project Analysis

## Overview
- ARTISTING is an AI legal/tax assistant (Django REST backend + Next.js frontend) aimed at Spanish cultural professionals (see `APP_STRUCTURE.md`, repository root).
- Backend mixes Celery, Redis, PostgreSQL, OpenSearch, DeepSeek-based reasoning, Stripe billing, and semantic caching.
- Frontend (Next.js 15 App Router) implements multilingual marketing pages, authenticated chat, and widget integrations; services live under `frontend/lib/services`.

## Backend Notes
- `ovra_backend/settings.py` hard codes production secrets (DeepSeek/DB/Stripe), enables `DEBUG=True`, and `CORS_ALLOW_ALL_ORIGINS`; move to environment variables ASAP.
- Chat workflow (`backend/chat/views.py`) streams SSE responses, debits credits (`users.models.UserProfile`), writes `ChatLog`s, fetches BOE context, and asynchronously validates claims. Bugs: `chatLog` typo when building history, storing `response_id` on a model that lacks the field, and passing raw text to `validate_claims`.
- BOE ingestion/retrieval uses management commands + Celery tasks (`boe/management/commands/ingest_boe.py`, `boe/tasks.py`), indexing via OpenSearch (`boe/opensearch_client.py`) and `search_boe`.
- `apps/agent` contains reasoning pipeline definitions, rerankers, DeepSeek client, regression testing models/tests, orchestration stubs, and semantic cache hooks. `Reasoner` still has placeholder code (`mlr.reason(...)`), and `llm_client` defines conflicting `call_llm` functions.
- Semantic cache uses pgvector-backed `SemanticCacheEntry` plus Celery embedding jobs (`semantic_cache/models.py`, `semantic_cache/tasks.py`).
- Billing integrates Stripe Checkout, subscription tracking, Celery-based credit allocation (`billing/models.py`, `billing/views.py`, `billing/tasks.py`); metrics collected via `MetricLog`.
- Testing: pytest configured for SQLite (`pytest.ini`, `ovra_backend/test_settings.py`); only regression service tests exist (`apps/agent/tests`).

## Frontend Notes
- Next.js App Router app with Auth/Language providers (`frontend/app/layout.tsx`); translations centralized (`contexts/language-context.tsx`) though there is mojibake due to encoding.
- Core services (`frontend/lib/services/*`) wrap auth, chat, billing, and user APIs. Defaults point to `/api`; production should set `NEXT_PUBLIC_API_URL` to the Django `/api/v1` base.
- Chat UI (`frontend/app/chat/page.tsx`) streams messages, tracks credits, renders Markdown, and shows credit banners.
- Marketing/help/pricing/status/privacy/etc. pages prebuilt; widgets + documentation in `frontend/public/*`.
- Next.js API route `app/api/chat/route.ts` streams GPT-4o using the `ai` SDK without auth/rate limiting—decide whether to keep or remove.

## Operational Considerations
- Celery beat schedules BOE ingestion; workers need Redis broker, pgvector-enabled Postgres, OpenSearch cluster, Stripe webhooks.
- Scripts under `scripts/` automate backend/frontend setup and deployment.
- Ensure environment variables for DeepSeek, OpenSearch, Stripe, Redis, and frontend URLs are set in deployments.

## Key Risks / Gaps
1. **Secrets + permissive settings in git**: DB password, DeepSeek keys, Stripe placeholders, `DEBUG=True`, open CORS—must be moved to env vars and rotated.
2. **Chat/Reasoner bugs**: `chatLog` typo, missing `response_id` field, `validate_claims` misuse, placeholder `mlr.reason(...)`, duplicate `call_llm` definitions—all can crash requests.
3. **API contract mismatches**: frontend expects `/user/profile`, `/user/notifications`, etc., which backend lacks; `users/urls.py` registers `'/login'` (leading slash) causing malformed paths.
4. **Widget/Next.js GPT route exposure**: publicly accessible GPT-4 endpoint and widget embeds need auth/rate limiting or removal.
5. **Encoding + documentation drift**: translation strings contain mojibake; docs reference `test_integration.js` which is missing.
6. **Multiple lockfiles**: `package-lock.json`, `pnpm-lock.yaml`, and `yarn.lock` coexist—choose one package manager to avoid drift.

## Suggested Next Steps
1. Externalize secrets, tighten security settings (CORS, DEBUG, CSRF origins) before any public deployment.
2. Fix chat/agent pipeline issues (typos, model fields, validation flow, `Reasoner` placeholders, `llm_client` duplication) and add regression/unit coverage.
3. Align REST contracts by adding missing endpoints or adjusting frontend service paths; ensure `NEXT_PUBLIC_API_URL` includes `/api/v1`.
4. Stand up and document supporting services (Celery worker/beat, Redis, OpenSearch, pgvector DB, Stripe webhooks) along with deployment scripts.
5. Decide on widget/GPT-4 route strategy—secure or remove to prevent token leakage.
6. Clean up localization files (proper UTF-8) and reconcile documentation references (e.g., add or remove `test_integration.js`).
