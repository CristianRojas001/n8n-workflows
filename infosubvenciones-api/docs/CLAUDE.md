# CLAUDE.md — Project briefing for Claude Code

## What we’re building
- App: <NAME>
- One-liner: <WHAT IT DOES>
- Primary users: <WHO>
- MVP success = <3 bullet acceptance criteria>

## Repo map
- apps/web            Frontend (React/Next)
- apps/api            Backend (TypeScript API)
- packages/shared     Shared schemas/types/utils
- infra/              Docker + deploy notes
- docs/               PRD, architecture, runbook

## Golden rules (follow strictly)
1) Don’t invent requirements. If unknown, write an **Assumptions** section.
2) Work in **small vertical slices** (UI → API → DB → tests).
3) Every change must include a **verification command** (tests/build/lint/run).
4) Prefer boring solutions. Only add deps with a short justification.
5) Update docs when decisions change (docs/ARCHITECTURE.md, docs/RUNBOOK.md).

## Commands (must stay accurate)
- Install: pnpm install
- Dev: pnpm dev
- Web dev: pnpm --filter web dev
- API dev: pnpm --filter api dev
- Typecheck: pnpm typecheck
- Lint: pnpm lint
- Unit tests: pnpm test
- DB migrate: pnpm db:migrate
- DB seed: pnpm db:seed

## Engineering standards
- TypeScript strict.
- Validate all external input at boundaries (API). Use shared schemas in packages/shared.
- No secrets in repo. Use .env + commit .env.example.
- Add minimal tests for each shipped feature (at least one happy-path + one edge case).

## Workflow (how you should operate)
- Before coding: summarize current state + propose plan in bullets.
- While coding: keep diffs small; don’t refactor unrelated code.
- After coding: run verification command(s); report results.
- Finish: list files changed + what to check in review.

## Where requirements live
- docs/PRD.md (source of truth)
- docs/TASKS.md (task list with IDs + verification commands)
- docs/ARCHITECTURE.md (stack + data model + API shape)