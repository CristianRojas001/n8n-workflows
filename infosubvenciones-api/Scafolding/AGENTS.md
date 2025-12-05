# AGENTS.md — Instructions for coding agents (Codex, etc.)

## Read-first
- Source of truth: docs/PRD.md and docs/ARCHITECTURE.md
- Work in small vertical slices; don’t attempt “big bang” rewrites.

## Setup & verification commands
- pnpm install
- pnpm dev
- pnpm typecheck
- pnpm lint
- pnpm test
- pnpm db:migrate

## Change policy
- No secrets committed. Use .env + .env.example.
- Add/update tests for changed behavior.
- If you add a dependency: explain why + consider simpler alternatives.
- Keep diffs small; one task/commit.

## Output format after each task
- Summary (3 bullets)
- Files changed
- Verification command(s) + result
- Follow-ups / risks (if any)
