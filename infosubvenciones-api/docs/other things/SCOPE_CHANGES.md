# Scope Changes - New Project Contract

**Date**: 2025-12-01
**Source**: Sistema Inteligente de Subvenciones y RAG Legal – Prototipado + Producción.pdf

---

## 🔄 What Changed

### Original Scope (from ingestion_strategy.md)
- Standalone InfoSubvenciones grant search platform
- 6 weeks, single deliverable
- Public access, no authentication
- New Next.js frontend

### New Scope (from contract PDF)
- **Two systems**: InfoSubvenciones + Legal RAG (separate ingestion, separate DB)
- **Two milestones**: Prototype (21 days) + Production (21 days)
- **Integrated into existing ARTISTING platform** (not standalone)
- Uses existing ARTISTING CRM, auth, admin panel
- Newsletters handled separately in n8n (out of scope)

---

## ✅ What Stays the Same

### Technical Stack
- ✅ Django REST Framework for API
- ✅ PostgreSQL + pgvector for vector storage
- ✅ Gemini 2.0 Flash for summaries/extraction
- ✅ OpenAI embeddings for semantic search
- ✅ Celery + Redis for ingestion pipeline
- ✅ Python 3.11+

### InfoSubvenciones Features
- ✅ Ingestion from InfoSubvenciones API (136k grants)
- ✅ PDF processing + LLM summaries
- ✅ Semantic search with filters
- ✅ Citation with original PDFs

---

## 🆕 What's New

### 1. Integration with Existing ARTISTING
- **Reuse**: ARTISTING's existing auth, CRM, user profiles, admin panel
- **New**: Only add chat interface for grants + legal RAG
- **UI**: Use ARTISTING design system (already have it)
- **Deployment**: Integrate into existing ARTISTING Django backend

### 2. Two Separate RAG Systems

#### InfoSubvenciones RAG
- **Data**: 136k grants from InfoSubvenciones API
- **Database**: `infosubvenciones` PostgreSQL (as planned)
- **Purpose**: Search/chat about grants
- **UI**: Chat interface in ARTISTING

#### Legal RAG (Separate)
- **Data**: BOE, CENDOJ, PETETE (legal documents)
- **Database**: Separate PostgreSQL database `legal_rag`
- **Purpose**: Legal/tax/labor advice
- **UI**: Chat interface in ARTISTING (different from grants)
- **Note**: Different ingestion process, separate models

### 3. Two-Milestone Approach

#### Milestone 1 (21 days): Prototype with Subset
- **InfoSubvenciones**: 10 → 100 → 1,000 grants (incremental testing)
- **Legal RAG**: Subset of BOE/CENDOJ/PETETE
- **Deliverable**: Working chat interfaces for both systems
- **Price**: €1,500 (1 revision)

#### Milestone 2 (21 days): Production with Full Corpus
- **InfoSubvenciones**: Full 136k grants
- **Legal RAG**: Full BOE, CENDOJ, PETETE corpus
- **Deliverable**: Production-ready systems
- **Price**: €2,000 (2 revisions)
- **Support**: 30 days post-production

### 4. Reference Design
- **Primary**: ARTISTING design system (reuse existing components)
- **Inspiration**: fandit.es functionality (already in ingestion_strategy.md)
- **Note**: No need to copy fandit.es design, just functionality

### 5. Out of Scope (Handled Elsewhere)
- ❌ **Newsletters**: Handled in n8n separately (not part of this project)
- ❌ **CRM/Auth/Admin**: Already exists in ARTISTING (reuse, don't rebuild)
- ❌ **User registration**: Already exists in ARTISTING

---

## 📋 What Needs to Change in Planning Docs

### 1. PROJECT_PLAN.md
**Change**:
- Timeline: 6 weeks → 2 milestones (3 weeks each)
- Scope: Add Legal RAG as second system (separate DB)
- Remove: CRM, auth, newsletters (already exist or out of scope)
- Add: Integration with existing ARTISTING backend

**Keep**:
- InfoSubvenciones ingestion strategy (same as before)
- Tech stack decisions
- Cost estimates

### 2. APP_STRUCTURE.md
**Change**:
- Root location: `ARTISTING-main/backend/` (not separate repo)
- Add: `apps/grants/` - InfoSubvenciones RAG
- Add: `apps/legal_rag/` - Legal RAG (separate DB)
- Add: Chat interface in existing frontend
- Remove: Standalone Next.js frontend
- Remove: New auth/CRM (use existing)

**Keep**:
- Ingestion/ folder (standalone for processing)
- Database schemas for grants
- API endpoints design

### 3. SPRINT_PLAN.md
**Change**:
- Milestone 1 (Weeks 1-3): Prototype with 10/100/1000 grants
- Milestone 2 (Weeks 4-6): Full 136k grants + Legal RAG
- Add: Legal RAG ingestion (Week 3)
- Add: Chat interface integration (Week 2-3)
- Remove: Build CRM/auth/admin (already exists)

### 4. RAG_PIPELINE.md
**Add**:
- Section: Legal RAG Pipeline (separate from grants)
- Different ingestion for BOE/CENDOJ/PETETE
- Separate database: `legal_rag`

### 5. UX_SURFACES.md
**Change**:
- Remove: User registration/login pages (already exist)
- Remove: CRM dashboard pages (already exist)
- Remove: Admin panel (already exist)
- Add: Chat interface for grants (integrate into ARTISTING)
- Add: Chat interface for legal RAG (separate chat)
- Reference: ARTISTING design system (not fandit.es design)

### 6. INFRASTRUCTURE_CHECKLIST.md
**Add**:
- Second database: `legal_rag` PostgreSQL
- Access to existing ARTISTING codebase
- Integration points with ARTISTING backend

---

## 🎯 Clarifications from Discussion

1. **Design Reference**: ARTISTING (not fandit.es design)
   - fandit.es functionality is already covered in ingestion_strategy.md

2. **Newsletters**: n8n separate project (just mention, not implement)

3. **Legal RAG**: Separate database, separate ingestion, built in Phase 1 after InfoSubvenciones

4. **Existing ARTISTING Features** (reuse, don't rebuild):
   - User registration/login
   - User profiles/CRM
   - Admin panel
   - Authentication system

5. **What We're Building**:
   - InfoSubvenciones ingestion pipeline
   - Legal document ingestion pipeline (BOE/CENDOJ/PETETE)
   - Two chat interfaces (grants + legal)
   - API endpoints for both RAG systems
   - Integration with existing ARTISTING chat UI

6. **Progressive Testing**:
   - Start: 10 grants
   - Then: 100 grants
   - Then: 1,000 grants (Milestone 1 complete)
   - Finally: 136k grants (Milestone 2)

---

## 📊 Updated Project Structure

```
ARTISTING-main/                     # Existing project (reuse)
├── backend/
│   ├── apps/
│   │   ├── core/                   # ✅ Already exists (auth, users)
│   │   ├── chat/                   # ✅ Already exists (chat UI)
│   │   ├── grants/                 # 🆕 NEW - InfoSubvenciones RAG
│   │   │   ├── models.py           # Grant models (read-only to infosubvenciones DB)
│   │   │   ├── views.py            # Search API, chat API
│   │   │   ├── services.py         # Vector search, filters
│   │   │   └── urls.py
│   │   └── legal_rag/              # 🆕 NEW - Legal RAG
│   │       ├── models.py           # Legal doc models (separate DB)
│   │       ├── views.py            # Legal search/chat API
│   │       └── urls.py
│   └── ...
│
├── frontend/                       # ✅ Already exists
│   ├── app/
│   │   ├── chat/                   # ✅ Modify to add grants/legal chat
│   │   └── ...
│   └── ...
│
└── ...

infosubvenciones-api/               # New standalone ingestion system
├── Ingestion/                      # InfoSubvenciones pipeline
│   ├── (same structure as planned)
│   └── ...
│
├── LegalIngestion/                 # 🆕 NEW - Legal documents pipeline
│   ├── config/
│   ├── models/
│   ├── services/
│   │   ├── boe_client.py
│   │   ├── cendoj_client.py
│   │   └── petete_client.py
│   └── ...
│
└── docs/
    └── (all planning docs)
```

---

## 🚨 Critical Dependencies

Before starting, must have:
1. ✅ Access to ARTISTING-main codebase
2. ✅ ARTISTING already has auth/CRM/admin
3. ✅ ARTISTING chat interface exists (just integrate new backends)
4. ⏳ Verify infrastructure (Redis, Python, disk space, PostgreSQL)

---

## 📅 Updated Timeline

### Milestone 1 - Prototype (21 days / 3 weeks)
**Week 1**: Foundation + 10-100 grants
- Day 1-2: Infrastructure verification
- Day 3-5: InfoSubvenciones ingestion (10 grants)
- Day 6-7: Test with 100 grants

**Week 2**: 1,000 grants + Chat Integration
- Day 8-10: Scale to 1,000 grants
- Day 11-14: Integrate chat interface into ARTISTING

**Week 3**: Legal RAG Prototype
- Day 15-17: Legal document ingestion (subset)
- Day 18-21: Legal chat interface integration

**Deliverable**: €1,500 (1 revision)
- Working chat for 1,000 grants
- Working chat for legal docs (subset)
- Both integrated into ARTISTING

### Milestone 2 - Production (21 days / 3 weeks)
**Week 4**: Full InfoSubvenciones Ingestion
- Day 22-28: Process all 136k grants

**Week 5**: Full Legal RAG + Optimization
- Day 29-35: Process full BOE/CENDOJ/PETETE
- Optimize both systems

**Week 6**: Production Deployment
- Day 36-42: Final testing, deployment, handoff

**Deliverable**: €2,000 (2 revisions)
- Full 136k grants searchable
- Full legal corpus searchable
- 30 days post-production support

---

## ✅ Next Steps

1. **Infrastructure Verification** (You - Day 1-2)
   - Run 4 commands (Redis, Python, disk space, PostgreSQL)
   - Get access to ARTISTING-main codebase

2. **Update Planning Docs** (Claude - After infrastructure verified)
   - Update PROJECT_PLAN.md with 2-milestone structure
   - Update APP_STRUCTURE.md with ARTISTING integration
   - Update SPRINT_PLAN.md with progressive testing (10/100/1000)
   - Add Legal RAG section to RAG_PIPELINE.md

3. **Start Milestone 1** (Week 1)
   - Create Ingestion/ structure
   - Test with 10 grants
   - Scale to 100, then 1,000

---

**Last Updated**: 2025-12-01
**Status**: Scope clarified, ready to update planning docs after infrastructure verification