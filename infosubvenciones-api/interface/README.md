# Interface (Frontend)

Light-mode chat interface that talks to the n8n agent via POST. Thin client: renders chat, filters, citations, results, and PDF viewer.

## Stack
- React + Vite + TypeScript
- Simple fetch POST to n8n webhook (no streaming)

## Environment
Copy `.env.example` to `.env.local` and set:
- `VITE_AGENT_ENDPOINT` – n8n webhook URL
- `VITE_AGENT_BASIC_AUTH_USER` / `VITE_AGENT_BASIC_AUTH_PASS` – Basic Auth credentials
- `VITE_AGENT_TIMEOUT_MS` – request timeout (ms)
- `VITE_APP_LAST_UPDATED` – optional string to show in badge

## Run
```
npm install
npm run dev
npm run build
npm run preview
```
> Nota: no abras `index.html` directamente con doble clic (file://); usa `npm run dev` o `npm run preview` para que Vite sirva los módulos.

## Behavior
- Chat input is sticky; sends POST with `{ sessionId, message, filters }`.
- Filters: región, beneficiario, finalidad, fechas, cuantía; presets for Autónomos, PYMES, Cultura (11), Comercio (14), Próx. 30 días.
- Pipeline status stripe animates during in-flight request.
- Responses render citations (chips), top convocatorias with `Ver PDF` (opens viewer) and `Descargar` (direct link).
- PDF viewer in right drawer (desktop) or stacked (mobile); shows fallback link if preview blocked.
- "Resetear chat" regenerates sessionId and clears context locally; n8n should drop context on new session.

## Notes
- CORS: allow your frontend origin on the webhook. If preview is blocked, have n8n return a proxied `pdfUrl` for viewing; direct link still used for download.
- Auth: Google Sign-In on frontend; webhook also protected via Basic Auth; add token validation if needed.
- Rate limits: n8n should reply 429 with `retryAfter` header for bursts; UI shows generic message (can be refined later).
