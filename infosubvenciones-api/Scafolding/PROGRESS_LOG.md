# Progress Log Template

> Purpose: keep a journal of every working session (manual or with Codex/Claude) so you can trace decisions, tests, and blockers.

## Session Entry Format
```
### Session YYYY-MM-DD – [Author/Assistant]
- **Context**: _What section/task were we working on?_
- **Commands run**: `_pytest`, `_npm run lint`, etc.
- **Code changes**: _Short summary + files touched._
- **Test results**: _Pass/fail, screenshots, logs._
- **Decisions made**: _Architecture, product, infra._
- **Blockers / TODOs**: _What’s pending? who owns it?_
- **Next steps**: _List concrete actions for the following session._
```

## Example Entry
```
### Session 2025-11-26 – Codex
- **Context**: Section B / Task “Implement JWT login”.
- **Commands run**: `pytest users/tests`, `npm run lint`.
- **Code changes**: Added `/api/v1/auth/login/` view + frontend auth service.
- **Test results**: All tests passed; manual login via UI succeeded.
- **Decisions**: Store tokens in httpOnly cookies + localStorage fallback.
- **Blockers**: Need UX input for error states.
- **Next steps**: Hook up forgot-password, update docs.
```

Maintain chronological entries so anyone can audit progress. Link to corresponding PRs or issues when available.
