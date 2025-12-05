# AGENTS.md - Instructions for coding agents

## Read first
- Source of truth: `docs/PROJECT_PLAN.md`, `docs/APP_STRUCTURE.md`, `docs/RAG_PIPELINE.md`, `docs/UX_SURFACES.md`, and `docs/ingestion_strategy.md`.
- Check `docs/INFRASTRUCTURE_CHECKLIST.md` and `docs/SPRINT_PLAN.md` for current blockers before starting a task.
- Work in focused vertical slices; avoid large rewrites unless explicitly requested.

## Setup & verification commands
Run the commands relevant to the subsystem you are touching and include the results in your task summary.

### Ingestion pipeline (Python/Celery)
- `python -m venv .venv && .\.venv\Scripts\activate` (or `source .venv/bin/activate` on Unix)
- `pip install -r Ingestion/requirements.txt`
- `python Ingestion/scripts/init_db.py`
- `python Ingestion/scripts/test_api.py --limit 10`
- `pytest Ingestion/tests -v`
- `celery -A Ingestion.config.celery_app worker -l info`

### Django API
- `pip install -r api/requirements.txt`
- `python api/manage.py migrate`
- `python api/manage.py test`
- `python api/manage.py runserver 0.0.0.0:8000`

### Frontend (Next.js)
- `npm install` (or `pnpm install` if the lockfile indicates)
- `npm run dev`
- `npm run lint`
- `npm run test`

## Change policy
- Never commit secrets; update `.env.example` when variables change.
- Add or update tests whenever you change behavior.
- Document new dependencies with justification and prefer the simplest approach.
- Keep diffs small and scoped to a single task.

## Output format after each task
- Summary (three concise bullets)
- Files changed (path list)
- Verification command(s) + result
- Follow-ups / risks (if any)
