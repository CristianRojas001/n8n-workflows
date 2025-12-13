# InfoSubvenciones UX Surfaces

> Purpose: enumerate every page, component, and state so design/dev work stays aligned. This document defines all UI elements for the grant discovery platform.

## 1. Personas & Journeys

### Persona A: Freelance Artist (Autónomo)
- **Role**: Self-employed artist (theater, music, visual arts)
- **Goals**: Find grants for projects, equipment, training
- **Pain points**: Overwhelmed by legal jargon, unsure which grants apply, tight deadlines
- **Tech savvy**: Medium - comfortable with web search but not legal databases

### Persona B: Small Business Owner (PYME)
- **Role**: Owner of small cultural/commerce business (gallery, bookstore, production company)
- **Goals**: Find funding for expansion, digitalization, innovation
- **Pain points**: Limited time to research, needs quick summaries, wants to delegate to employee
- **Tech savvy**: Medium to high

### Critical Journeys

**Journey 1: First-time Discovery**
1. Land on homepage → See value proposition
2. Type natural language query in search bar
3. Browse results with filters (sector, region, budget)
4. Click grant card → Read AI summary
5. Download PDF for detailed review
6. (Future) Save grant for later

**Journey 2: Targeted Search**
1. Direct to search page (returning user)
2. Apply filters first (region: Madrid, sector: Arts, budget: 10k-50k)
3. Scan results, sort by deadline
4. Compare 2-3 grants side-by-side
5. Download PDFs, note application deadlines

**Journey 3: Mobile Quick Check**
1. Search on mobile while commuting
2. See featured/urgent grants (closing soon)
3. Read summary on mobile
4. Share grant link via WhatsApp to business partner
5. Return on desktop to apply

## 2. Page/Surface Catalog

| Surface | Type | Primary Purpose | Key Data/API Hooks | Notes |
|---------|------|-----------------|-------------------|-------|
| **Landing / Home** | Marketing | Value prop, immediate search, build trust | Featured grants (`/api/v1/grants/search?featured=true`), grant count | Hero with search bar, "How it works" section, stats (136k grants), testimonials (future) |
| **Search Results** | App view | Display filtered grants, enable comparison | `POST /api/v1/grants/search` (vector + filters), pagination | Grid/list toggle, sidebar filters, sort options, loading skeletons, empty state |
| **Grant Detail** | App view | Full grant information, decision support | `GET /api/v1/grants/<numero>`, PDF download | Summary, all metadata, PDF viewer/download, citation, "Similar grants" (future) |
| **About / How It Works** | Support | Explain data source, usage, trust signals | Static content | Sections: Data source (InfoSubvenciones), How AI works, Update frequency, Contact |
| **Help / FAQ** | Support | Common questions, search tips | Static markdown or CMS | Search syntax, filter usage, how to apply (external link), definitions (finalidad, sectores) |
| **404 / Error States** | Utility | Handle broken links, API failures gracefully | N/A | Friendly error messages, link back to search, report issue button |

## 3. Component Inventory

### Navigation
- **Header**: Logo (ARTISTING branding), nav links (Home, Search, About, Help), mobile hamburger menu
- **Footer**: Copyright, Links (About, Help, Privacy, InfoSubvenciones source), Social media (future)
- **MobileNav**: Drawer menu for mobile, same links as header

### Search Components
- **SearchBar**:
  - Props: `initialQuery`, `onSearch`, `placeholder`
  - State: query text, loading, autocomplete suggestions (future)
  - Variations: Large (homepage hero), compact (results page header)
  - Accessibility: Label "Buscar ayudas y subvenciones", aria-live for results count

- **FilterPanel**:
  - Props: `filters`, `onFilterChange`, `availableOptions` (from API)
  - State: Selected filters (sector[], region[], budget range, dates, organo)
  - Variations: Desktop sidebar, mobile bottom sheet
  - Features: Clear all filters, filter chips, collapse/expand sections
  - Accessibility: Fieldset/legend for groups, keyboard navigation

- **ResultsGrid**:
  - Props: `grants[]`, `loading`, `layout` (grid/list)
  - State: View mode (grid/list), sort order
  - Variations: Loading skeleton (6 cards), empty state ("No se encontraron ayudas"), error state
  - Accessibility: Semantic list markup, focus management on load

### Grant Components
- **GrantCard**:
  - Props: `grant` (summary, metadata, score)
  - Content: Title (descripcion), summary (150 chars), organo_nivel2, presupuesto_total, fecha_fin, relevance badge, sector badges, "Ver más" CTA
  - State: Hover effect (lift shadow)
  - Variations: Featured (larger, highlighted), compact (list view)
  - Accessibility: Card is button/link, heading hierarchy

- **GrantDetail**:
  - Props: `grant` (full object)
  - Sections:
    - Header: numero_convocatoria, descripcion, organo hierarchy
    - Summary: AI-generated summary with "📝 Generado por IA" badge
    - Key Info: Budget, dates (inicio/fin solicitud), abierto status
    - Details: Sectores, regiones, tipos_beneficiarios, instrumentos
    - Extracted Fields: gastos_subvencionables, requisitos, plazos (from pdf_extractions)
    - Downloads: PDF button, sede_electronica link
    - Citation: Source reference, "Última actualización" date
  - State: Expanded/collapsed sections for long text
  - Variations: Print-friendly view
  - Accessibility: Heading structure (h1-h4), skip links for long content

- **CitationBadge**:
  - Props: `numeroConvocatoria`, `pdfUrl`, `sedeElectronica`
  - Content: "Fuente: Convocatoria #{numero}", link to PDF, link to official site
  - Style: Subtle background, small text, icon for external links
  - Accessibility: Descriptive link text ("Descargar PDF de convocatoria 871838")

### Feedback Components
- **Toast**: Success/error notifications (e.g., "PDF descargado", "Error al cargar ayuda")
- **Banner**: Info banners (e.g., "Datos actualizados: 1 de diciembre de 2025")
- **InlineError**: Form validation errors, API error messages
- **LoadingSkeleton**: Placeholder for loading grants (cards, detail view)
- **EmptyState**: No results found, suggestions to modify search

### UI Library (from ARTISTING)
- **Button**: Primary, secondary, ghost, icon variants
- **Card**: Base card component (used in GrantCard)
- **Input**: Text input for SearchBar
- **Select**: Dropdowns for filters
- **Badge**: Sector tags, status badges (abierto/cerrado)
- **Checkbox**: Multi-select filters
- **RadioGroup**: Single-select filters (e.g., sort order)
- **Slider**: Budget range filter
- **DatePicker**: Date range for deadline filters
- **Tabs**: Switch between sections in GrantDetail (future)
- **Tooltip**: Explanations for technical terms (e.g., "¿Qué es BDNS?")
- **Dialog/Modal**: Confirm actions, display full PDF (future)

## 4. Content & Localization

### Supported Languages
- **Primary**: Spanish (Castilian) - All UI, all summaries
- **Future**: Catalan, Basque, Galician (UI translation only, summaries stay Spanish)

### Translation Files
- **Location**: `frontend/locales/es.json`, `ca.json`, `eu.json`, `gl.json` (future)
- **Format**: JSON key-value
- **Example**:
  ```json
  {
    "search.placeholder": "Buscar ayudas y subvenciones...",
    "search.button": "Buscar",
    "filters.sector": "Sector",
    "filters.region": "Región",
    "results.count": "Se encontraron {count} ayudas",
    "grant.budget": "Presupuesto",
    "grant.deadline": "Fecha límite"
  }
  ```

### Dynamic Copy
- **Static content**: Homepage hero, About page, Help text → Hard-coded in components (can move to CMS later)
- **Grant content**: All from API (descriptions, summaries, metadata)
- **UI labels**: From translation files

### Content Guidelines
- **Tone**: Professional but approachable, empowering
- **Avoid**: Bureaucratic jargon in UI (explain terms when used)
- **Clarity**: Short sentences, active voice, bullet points for lists
- **Trust signals**: "Datos oficiales de InfoSubvenciones", "Actualizado [date]", "IA verificada"

## 5. Brand & Theming

### Design Tokens (from ARTISTING)
**Colors**:
- Primary: ARTISTING brand color (to be confirmed from codebase)
- Secondary: Accent for CTAs
- Neutral: Gray scale for backgrounds, borders, text
- Semantic: Green (success, open grants), Red (closed), Yellow (warning, closing soon), Blue (info)

**Typography**:
- Headings: Same font family as ARTISTING (check tailwind.config.ts)
- Body: Same as ARTISTING
- Code/Monospace: For numero_convocatoria, technical references

**Spacing**:
- Base unit: 4px (Tailwind default)
- Container max-width: 1280px
- Grid gaps: 4, 6, 8 (spacing units)

**Breakpoints**:
- sm: 640px
- md: 768px
- lg: 1024px
- xl: 1280px
- 2xl: 1536px

### Light/Dark Mode Strategy
- **MVP**: Light mode only (simpler, matches ARTISTING if they don't have dark mode)
- **Future**: Implement dark mode using CSS variables, detect system preference (`prefers-color-scheme`)
- **Storage**: localStorage key `theme` ("light"/"dark"/"system")

### Illustrations / Assets
- **Location**: `frontend/public/images/`
- **Assets Needed**:
  - Logo (ARTISTING logo)
  - Hero illustration (grants/money/support theme)
  - Empty state illustrations (no results, error)
  - Icons: Search, filter, download, external link, calendar, euro
- **Licensing**: Use open-source icons (Lucide, Heroicons) or ARTISTING's existing icon set
- **Optimization**: SVG preferred, PNG compressed with TinyPNG

## 6. Accessibility & Compliance

### Standards
- **Target**: WCAG 2.1 Level AA
- **Keyboard Navigation**: All interactive elements accessible via Tab, Enter, Space, Arrow keys
- **Screen Readers**: ARIA labels, semantic HTML (nav, main, aside, article, section)
- **Focus Management**: Visible focus indicators, skip links ("Saltar a contenido")
- **Color Contrast**: Minimum 4.5:1 for text, 3:1 for large text and UI elements

### Specific Requirements
- **SearchBar**: aria-label, aria-describedby for instructions
- **Filters**: Fieldset/legend, clear labels, announce filter count changes
- **Results**: Announce results count on search ("Se encontraron 234 ayudas")
- **Links**: Descriptive text (not "click here"), external link indicators
- **Images**: Alt text for illustrations, decorative images marked as such
- **Forms**: Error messages linked to inputs, visible validation states

### Legal Content
- **Privacy Policy**: No user data collection for MVP (analytics only, anonymized)
- **Terms of Use**: Disclaimer: "Información oficial de InfoSubvenciones, verificar en fuente original antes de aplicar"
- **Cookie Notice**: If using analytics (Google Analytics), display consent banner
- **Attribution**: "Powered by ARTISTING", "Datos de InfoSubvenciones (Gobierno de España)"
- **Copyright**: Footer text, "© 2025 ARTISTING. Datos públicos de InfoSubvenciones."

## 7. Detailed Page Specifications

### Homepage (Landing)

**Layout**:
```
┌─────────────────────────────────────┐
│ Header: Logo | Nav (About, Help)   │
├─────────────────────────────────────┤
│                                     │
│        🔍 HERO SECTION              │
│  "Encuentra ayudas y subvenciones"  │
│  [Large SearchBar]                  │
│  "136,920 ayudas disponibles"       │
│                                     │
├─────────────────────────────────────┤
│   HOW IT WORKS (3 steps)            │
│   1️⃣ Busca  2️⃣ Filtra  3️⃣ Aplica   │
├─────────────────────────────────────┤
│   FEATURED GRANTS (4 cards)         │
│   [GrantCard] [GrantCard] ...       │
│   "Ver todas las ayudas" button     │
├─────────────────────────────────────┤
│   TRUST SIGNALS                     │
│   "Datos oficiales" | "Actualizado" │
├─────────────────────────────────────┤
│ Footer: Links | Copyright           │
└─────────────────────────────────────┘
```

**Features**:
- Auto-focus on search bar
- Suggested searches (e.g., "Ayudas para artes escénicas", "Subvenciones comercio Madrid")
- Featured grants: 4 most recent or highest budget
- Stats: Total grants, total budget, sectors covered

**States**:
- Loading: Skeleton for featured grants
- Empty: If API fails, show fallback message + link to About

### Search Results Page

**Layout**:
```
┌───────────────────────────────────────────┐
│ Header (with compact SearchBar)           │
├─────────┬─────────────────────────────────┤
│ FILTERS │ RESULTS (Grid)                  │
│         │ "234 resultados para 'artes'"   │
│ Sector  │ Sort: [Relevancia ▼]            │
│ ☐ Cultura│                                 │
│ ☐ Comerc│ [GrantCard] [GrantCard] [Grant] │
│         │ [GrantCard] [GrantCard] [Grant] │
│ Región  │ [GrantCard] [GrantCard] [Grant] │
│ ☐ Madrid│                                 │
│ ☐ BCN   │                                 │
│         │ [Pagination: < 1 2 3 ... 12 >]  │
│ Budget  │                                 │
│ [Slider]│                                 │
│         │                                 │
│ [Clear] │                                 │
└─────────┴─────────────────────────────────┘
```

**Features**:
- Persistent search bar (modify query without going back)
- Filter sidebar (collapsible on mobile → bottom sheet)
- Sort options: Relevancia, Presupuesto (desc), Fecha límite (asc)
- View toggle: Grid (default) / List (compact)
- Pagination: 20 results per page
- Filter chips above results ("× Madrid", "× Cultura")
- "No results" state with suggestions ("Try broader search", "Remove filters")

**States**:
- Loading: Skeleton cards (6 placeholders)
- Empty: "No se encontraron ayudas. Intenta con otros filtros."
- Error: "Error al cargar resultados. [Reintentar]"

**Mobile Adaptations**:
- Filters: Bottom sheet (slide up from bottom)
- Grid: 1 column
- Pagination: Simpler (<Prev Next>)

### Grant Detail Page

**Layout**:
```
┌─────────────────────────────────────────┐
│ Header (with Back to results link)     │
├─────────────────────────────────────────┤
│ BREADCRUMB: Home > Search > #871838    │
├─────────────────────────────────────────┤
│ TITLE: [descripcion]                    │
│ Número: 871838 | ESTADO > Ministerio... │
│                                         │
│ 📝 RESUMEN (AI-generated)               │
│ [Summary text, 200-250 words]           │
│ "Generado por IA basado en PDF oficial"│
│                                         │
├─────────────────────────────────────────┤
│ 💰 INFORMACIÓN CLAVE                    │
│ • Presupuesto: 50.000 €                 │
│ • Plazo: 1 ene - 31 dic 2025            │
│ • Estado: 🟢 Abierto                    │
│ • Beneficiarios: PYMES, Autónomos       │
│                                         │
├─────────────────────────────────────────┤
│ 📋 DETALLES                             │
│ [Expandable sections]                   │
│ ▼ Sectores: [Badge: Cultura]           │
│ ▼ Regiones: [Badge: ES300 - Madrid]    │
│ ▼ Requisitos: [From pdf_extractions]   │
│ ▼ Gastos subvencionables: [...]        │
│                                         │
├─────────────────────────────────────────┤
│ 📥 DOCUMENTOS                           │
│ [Button: Descargar PDF] [Link: Sede]   │
│                                         │
├─────────────────────────────────────────┤
│ 🔗 CITACIÓN                             │
│ Fuente: Convocatoria #871838           │
│ InfoSubvenciones (Gobierno de España)  │
│                                         │
└─────────────────────────────────────────┘
```

**Features**:
- Sticky header with back button
- Collapsible sections for long content
- PDF download button (downloads from `/api/v1/grants/{numero}/pdf`)
- Sede electrónica external link (new tab)
- Social share buttons (future)
- "Similar grants" section (future, based on vector similarity)

**States**:
- Loading: Skeleton for entire page
- 404: "Ayuda no encontrada. [Volver a búsqueda]"
- Error: "Error al cargar. [Reintentar]"

### About / How It Works Page

**Content Sections**:
1. **¿Qué es InfoSubvenciones?**
   - Explanation of official government database
   - Scope: 136k grants, cultura + comercio, PYMES/autónomos

2. **¿Cómo funciona esta plataforma?**
   - AI-powered search (semantic search con embeddings)
   - Summaries generated by AI (Gemini 2.0)
   - Data updated [frequency]

3. **¿Es confiable?**
   - Official data source: InfoSubvenciones API
   - AI summaries for convenience, always verify in PDF
   - Link to InfoSubvenciones.es

4. **Contacto / Feedback**
   - Email or form for questions
   - Report data errors
   - Feature requests

**Layout**: Simple markdown-style content, illustrations for visual interest

## 8. Open Questions

- **ARTISTING design system details**: Need to extract exact colors, fonts from `ARTISTING-main/frontend/`
- **Dark mode**: Does ARTISTING have dark mode? Should we implement it?
- **Featured grants logic**: Random, most recent, highest budget, or manual curation?
- **Mobile menu**: Hamburger or bottom nav bar?
- **Analytics**: Which tool? Google Analytics, Plausible, or self-hosted?
- **PDF viewer**: Inline (iframe/embed) or always download? Browser support issues?
- **Sorting options**: What sort orders are most useful? (relevance, budget, deadline, date added)
- **Pagination vs Infinite scroll**: Which is better for UX? (Pagination for MVP, easier implementation)

---

**Last Updated**: 2025-12-01
**Status**: Complete specification, ready for implementation
**Next Step**: Extract ARTISTING design tokens, begin frontend development
