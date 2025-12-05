# Extraction System Scope & Decisions

**Date**: 2025-12-03
**Context**: Data extraction system for 1-week delivery

---

## Key Decisions

### 1. Embedding Model: Gemini 768-dim ✅

**Decision**: Keep Gemini text-embedding-004 (768 dimensions)

**Rationale**:
- Already working in ingestion system
- Cost-effective for testing phase
- Easy to switch later (only 18 grants currently, ~2 min migration)

**Alternative**: OpenAI 1536-dim (rejected: 10x cost, <3% quality gain)

---

### 2. PDF Display: Multi-Tab ✅

**Decision**: Tabbed interface with 4 options

1. **Formatted View** (default) - Markdown rendering
2. **Full Document** - Complete markdown
3. **PDF Original** - iframe viewer
4. **Download** - Direct download

**Rationale**: Fast loading, user choice, mobile-friendly

---

### 3. Context: Top 5 Grants ✅

**Decision**: Send top 5 grants to LLM for chat

**Progressive Loading**:
- Initial: Summaries only (~500 chars)
- On detail: Full 110+ fields

**Rationale**: Balance cost & quality, prevent token overflow

---

### 4. Clarification: >20 or <3 Results ✅

**Decision**: Ask clarification when:
- Too many (>20): Suggest filters
- Too few (<3): Suggest broaden

**Example**:
```
>20: "Encontré 45 subvenciones. ¿Región específica?"
<3:  "Solo 2 resultados. ¿Ampliar búsqueda?"
```

---

### 5. Models: Tiered Selection ✅

**Decision**: Automatic model selection

```python
Simple → Gemini Flash ($0.10/1M)
Complex → GPT-4o ($2.50/1M)
Low confidence → GPT-4o fallback
```

**Rationale**: Cost optimization (80% use cheap model)

---

### 6. Database: Direct Connection ✅

**Decision**: Django → Supabase PostgreSQL (read-only user)

**Security**:
- Read-only user (`grants_readonly`)
- Connection timeouts (30s)
- Input validation
- Credentials in .env

**Can Change**: Abstraction layer allows API switch later

---

### 7. Pagination: Session-Based ✅

**Decision**: Store results in Redis, return 5/page

**Flow**:
```
Search → Store 50 in Redis (1h TTL)
Return first 5
"Más opciones" → Return next 5 (from cache)
```

**Rationale**: Fast, preserves context, simple

---

## Out of Scope

### Exists in ARTISTING (Reuse)
- ❌ User authentication
- ❌ CRM/admin panel
- ❌ Design system

### Handled Elsewhere
- ❌ Newsletters (n8n)
- ❌ Ingestion (complete)

---

## Success Criteria

### Functional
- [ ] Search <2s response time
- [ ] Chat <5s response time
- [ ] PDF display (all 3 modes)
- [ ] Pagination working
- [ ] All 110+ fields accessible

### Non-Functional
- [ ] Mobile responsive
- [ ] Secure (read-only DB)
- [ ] Cost-effective
- [ ] Production-ready

---

**Last Updated**: 2025-12-03
**Status**: All decisions finalized, ready for implementation
