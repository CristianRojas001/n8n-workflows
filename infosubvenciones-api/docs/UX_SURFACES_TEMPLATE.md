# UX Surfaces Template

> Purpose: enumerate every page, component, and state so design/dev work stays aligned. Fill this before starting UI implementation so Codex/Claude knows what to generate.

## 1. Personas & Journeys
- **Persona A**: _Role, goals, pain points._
- **Persona B**: _
- **Critical journeys**: _Login → ask question → review result → upgrade plan, etc._

## 2. Page/Surface Catalog
Fill in the table; add rows as needed.

| Surface | Type | Primary purpose | Key data/API hooks | Notes |
|---------|------|-----------------|--------------------|-------|
| Landing / Home | Marketing | _Value prop, CTA._ | _Feature list, testimonials._ | _A/B testing? localization?_ |
| Auth (Login/Signup/Forgot) | Form flow | _Onboard users._ | `/auth/login`, `/auth/register`, email service. | _Include error handling states._ |
| Chat Workspace | App view | _Ask/answer with RAG._ | `/chat/stream`, `/chat/sessions`, semantic cache. | _Streaming UI, credit banners._ |
| Credits/Billing | Dashboard | _Upgrade, checkout._ | `/billing/*`, Stripe SDK. | _Plan cards, history table._ |
| Analytics / History | Dashboard | _Usage insights._ | `/metrics`, `/chat/sessions`. | _Filters, export actions._ |
| Help/Status/Docs | Support | _Trust & transparency._ | Static markdown or CMS. | _GDPR, terms, widget instructions._ |

## 3. Component Inventory
- **Navigation**: _Header, sidebar, account menu._
- **Feedback**: _Toast notifications, banners, inline errors._
- **Forms**: _Reusable form controls, validators._
- **AI widgets**: _Chat bubble, suggestion cards, citation list._
- **Visualizations**: _Charts, tables, metric cards._

For each component, note props/state, loading/empty/error variations, and accessibility requirements.

## 4. Content & Localization
- **Supported languages**: _Default + others._
- **Translation files**: _Where they live, format (JSON, TS object)._
- **Dynamic copy**: _What needs CMS integration vs hard-coded text._

## 5. Brand & Theming
- **Design tokens**: _Colors, typography, spacing, breakpoints._
- **Light/dark mode strategy**: _CSS variables, system preference detection._
- **Illustrations / assets**: _Location, licensing, optimization tips._

## 6. Accessibility & Compliance
- **Standards**: _WCAG level, keyboard navigation rules, aria usage._
- **Legal content**: _Cookie notices, consent flows, disclaimers._

## 7. Open Questions
- _Unresolved UX decisions, pending research, integration blockers._
