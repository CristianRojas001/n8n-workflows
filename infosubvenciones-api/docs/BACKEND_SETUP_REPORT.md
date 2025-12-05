# Backend Setup & Stabilization Report

**Date:** 2025-12-04  
**Owner:** Codex (backend bring-up)

---

## 1. What Was Done

1. **Documented environment variables** – added `ARTISTING-main/backend/.env` so Django loads Supabase read-only credentials, Redis, LLM keys, and helper flags (`DJANGO_ALLOWED_HOSTS`, `ALLOW_ANONYMOUS_API`, `DEEPSEEK_AGENT_URL`).
2. **Cleaned dependency set** – updated `requirements.txt` to drop the stray `psycopg-2`, ensured `google-generativeai>=0.3.0` is present, and provisioned a dedicated virtual environment (`.venv`) with `pip install -r requirements.txt` plus `psycopg`.
3. **Database access verification** – re-used the newly created Supabase read-only role, granted it access to the `extensions` schema, and verified ORM connectivity via `test_grants_connection.py`.
4. **Search engine hardening** – `apps/grants/services/search_engine.py` now tries pgvector SQL first, and if the `vector` type or `<=>` operator is unavailable it falls back to a Python-side cosine similarity using NumPy.
5. **Local testing harness** – used a transient PowerShell helper to launch `manage.py runserver` and hit `/api/v1/grants/search/` and `/api/v1/grants/chat/`. Search returns data; chat currently bubbles up Gemini quota errors so you can see what to fix next.

---

## 2. Environment & Configuration Details

### `.env` in `ARTISTING-main/backend`

```dotenv
GRANTS_DB_USER=grants_readonly.vtbvcabetythqrdedgee
GRANTS_DB_PASSWORD=...
GRANTS_DB_HOST=aws-1-eu-central-2.pooler.supabase.com
GRANTS_DB_PORT=6543
GEMINI_API_KEY=...
OPENAI_API_KEY=...
REDIS_URL=redis://localhost:6379/0
DEEPSEEK_AGENT_URL=http://localhost:11434
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
ALLOW_ANONYMOUS_API=true
```

Key points:

- `load_dotenv()` in `ovra_backend/settings.py` reads this file automatically.
- `ALLOW_ANONYMOUS_API` toggles DRF permissions: `AllowAny` in development, `IsAuthenticated` in all other cases. Set it to `false` (or remove the variable) before deploying.
- `DJANGO_ALLOWED_HOSTS` supplements the hard-coded list (`chat.artisting.es`, `www.chat.artisting.es`, `localhost`, `127.0.0.1`) so curl/Postman can hit the dev server without header errors.

### Supabase read-only role

- Already provisioned (`grants_readonly.vtbvcabetythqrdedgee / ezc7ta43cY%Se-@X1kqFNwRm`).
- Granted `USAGE` on the `extensions` schema so pgvector types are visible, plus the usual `CONNECT/USAGE/SELECT`.
- Confirmed counts via ORM (`Convocatoria`, `PDFExtraction`, `Embedding`) and direct SQL.

---

## 3. Dependencies & Tooling

1. **Removed duplication** – `psycopg-binary` remains the default Postgres driver; `psycopg-2` was removed.  
2. **Added LLM SDK** – explicitly lists `google-generativeai>=0.3.0` alongside `openai==1.106.1`.  
3. **Virtual environment** – created at `ARTISTING-main/backend/.venv` and bootstrapped with:

   ```powershell
   cd "D:\IT workspace\infosubvenciones-api\ARTISTING-main\backend"
   python -m venv .venv
   .\.venv\Scripts\python -m pip install --upgrade pip
   .\.venv\Scripts\pip install -r requirements.txt
   .\.venv\Scripts\pip install psycopg  # ensures Django can import psycopg3
   ```

4. **Redis** – existing Docker container `redis-infosubvenciones` already exposes `6379`; nothing else required.

---

## 4. Search Engine Changes

- File: `apps/grants/services/search_engine.py`
- Additions:
  - Imports `numpy` and `connections` to support both SQL and Python similarity calculations.
  - `_semantic_db_search()` keeps the pgvector path (using `<=>` cosine distance).
  - `_semantic_python_search()` streams embeddings through NumPy, computes cosine similarity in Python, and sorts results locally. This path activates automatically when the SQL query fails (e.g., vector type hidden in local Supabase clones).
  - `_prepare_semantic_response()` consolidates serialization/pagination logic so both search paths return identical payloads.
- Result: local/dev machines can issue semantic/hybrid searches even if pgvector operators aren’t available, without impacting production where pgvector works.

---

## 5. Verification & Current Status

| Step | Command | Result |
|------|---------|--------|
| Dependency sync | `.\.venv\Scripts\pip install -r requirements.txt` | All packages installed inside venv |
| DB sanity | `.\.venv\Scripts\python test_grants_connection.py` | ✔ Found 100 grants, 18 PDF extractions, 18 embeddings |
| Search API | `curl -X POST http://127.0.0.1:8000/api/v1/grants/search/ -d "{\"query\": \"ayudas cultura\", \"page_size\": 3}"` | ✔ Returns grant list with similarity scores |
| Chat API | same with `/chat/` | ⚠️ Returns JSON error explaining Gemini quota exhaustion (service code runs, but upstream key lacks quota) |

Notes:
- The Django helper script (`run_backend_checks.ps1`) was temporary and removed; use the manual commands below when you need to re-run tests.
- Because Gemini quota is exhausted, chat responses currently contain the provider error. Once quota is topped up, the pipeline should respond normally.

---

## 6. How to Continue

1. **Update secrets for real use**  
   - Replace placeholder API keys in `.env` with working ones.  
   - Set `ALLOW_ANONYMOUS_API=false` (or remove it) before shipping to any shared environment.  
   - Consider moving secrets into the deployment platform (Docker env vars, Azure/App Service config, etc.).

2. **Re-run backend verification after quota reset**  
   ```powershell
   cd "D:\IT workspace\infosubvenciones-api\ARTISTING-main\backend"
   .\.venv\Scripts\python manage.py runserver
   # In a second terminal
   curl -X POST http://127.0.0.1:8000/api/v1/grants/search/ ^
        -H "Content-Type: application/json" ^
        -d "{\"query\":\"ayudas cultura\",\"page_size\":3}"
   curl -X POST http://127.0.0.1:8000/api/v1/grants/chat/ ^
        -H "Content-Type: application/json" ^
        -d "{\"message\":\"¿Qué ayudas hay para empresas?\"}"
   ```
   Keep Redis running (`docker start redis-infosubvenciones`) before launching Django.

3. **Frontend integration (Day 4–5 scope)**  
   - Consume `/api/v1/grants/search/` for the listings page with paginated cards.  
   - Wire `/api/v1/grants/chat/` into the chat interface; gracefully surface quota or backend errors to users.  
   - Use `GrantSummarySerializer` data to populate cards/modals.

4. **Production hardening**  
   - Swap the temporary read-only password before go-live and store it in a secrets manager.  
   - Re-enable authentication (SimpleJWT) once frontend sessions are ready.  
   - Optional: add management commands or tests for the new fallback logic.

5. **Monitoring & alerts**  
   - Add checks around Gemini/OpenAI quotas to avoid silent failures (e.g., alert when confidence=0).  
   - Consider logging the fallback activations so you know when pgvector is unusable.

---

## 7. Quick Reference

| Item | Location / Command |
|------|-------------------|
| Backend env file | `ARTISTING-main/backend/.env` |
| Search service | `apps/grants/services/search_engine.py` |
| Test script | `ARTISTING-main/backend/test_grants_connection.py` |
| Virtualenv activation | `.\.venv\Scripts\activate` (PowerShell: `.\.venv\Scripts\Activate.ps1`) |
| Runserver | `.\.venv\Scripts\python manage.py runserver` |
| Redis container | `docker start redis-infosubvenciones` (already created) |

---

This report should give you full traceability for Day 3 backend stabilization and the exact steps to reproduce or extend the environment. Reach out if you need deeper diffs or automation around these steps. 

---

## Backend Test Results - Day 3

**Date**: 2025-12-04  
**Tester**: Codex

### Summary
- Total Tests: 14
- Passed: 12
- Failed: 2
- Warnings: 1 (chat clarification response returned `model_used: "none"`)

### Test Results

#### 1. Gemini API
- [x] PASS / [ ] FAIL
- Model: gemini-2.5-flash-lite
- Notes: SDK replied "Hola." confirming key and quota are valid.

#### 2. Database Connection
- [x] PASS / [ ] FAIL
- Grants: 100
- Extractions: 18
- Embeddings: 18

#### 3. Django Server
- [x] PASS / [ ] FAIL
- Started successfully: Yes (served all subsequent cURL requests)

#### 4. Search Endpoint
- [x] PASS / [ ] FAIL - Semantic mode (`"ayudas cultura"`, top 3)
- [x] PASS / [ ] FAIL - Filter mode (`abierto=true`, top 3)
- [ ] PASS / [x] FAIL - Hybrid mode (`"empresas"` + `abierto=true` returned closed grants such as IDs 71, 68, 95)
- Response time: 1.06s average across the three searches

#### 5. Chat Endpoint
- [x] PASS / [ ] FAIL - Simple query (Gemini Flash Lite, `complexity_score=10`)
- [ ] PASS / [x] FAIL - Complex query (never escalated to GPT-4o, responded with `model_used: "none"` and immediate clarification)
- [x] PASS / [ ] FAIL - Clarification trigger (prompted for filters but also emitted `model_used: "none"`)
- Response time: 2.50s average across the three prompts

#### 6. Pagination
- [x] PASS / [ ] FAIL
- Pages distinct: Yes (Page 1 IDs 48/85/90, Page 2 ID 106)

#### 7. Grant Details
- [x] PASS / [ ] FAIL - Summary endpoint (`/api/v1/grants/48/`)
- [x] PASS / [ ] FAIL - Details endpoint (`/api/v1/grants/48/details/`)

#### 8. Error Handling
- [x] PASS / [ ] FAIL - Missing field (`POST /chat/` + `{}`)
- [x] PASS / [ ] FAIL - Invalid request (`POST /search/` + `{"page":1}`)

### Issues Found
1. `POST /api/v1/grants/search/` in hybrid mode ignores the `abierto=true` filter: request `{"query":"empresas","filters":{"abierto":true},"page_size":5}` still returned closed grants (IDs 71, 68, 95). This breaks the expected hybrid behavior where both semantic match and filters are enforced.
2. Complex chat requests never switch to GPT-4o: `message="Compara las ayudas para pymes en Madrid y Andalucía..."` responded with `model_used: "none"` and `needs_clarification=true` even though the intent is clearly comparative and high complexity.
3. Clarification flow responses omit a model identifier: `message="ayudas"` produced the right clarification prompt but also returned `model_used: "none"`, making it hard to audit which LLM handled the request.

### Performance Metrics
- Search avg response: 1.06s
- Chat avg response: 2.50s
- Gemini quota remaining: Not explicitly checked, but the Flash Lite prompt succeeded on the first attempt.

### Recommendations
1. Enforce filters after hybrid ranking so grants that do not match `filters` never appear in the response payload.
2. Review the complexity scoring / routing logic so comparative or multi-region prompts escalate to GPT-4o and populate `model_used` accordingly.
3. Ensure all chat responses (even clarification shortcuts) record the model that produced the text for observability.
