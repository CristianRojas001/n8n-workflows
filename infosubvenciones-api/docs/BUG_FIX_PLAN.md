# Bug Fix Plan - User Reported Issues

**Date**: 2025-12-04
**Status**: 🔧 **IN PROGRESS**

---

## 🐛 Issues Reported by User

### 1. Chat responds to greetings as search queries
**Issue**: Typing "hi" or "hola" triggers grant search instead of conversational response

**Root Cause**: Intent classifier defaults unknown queries to SEARCH
**Location**: `apps/grants/services/intent_classifier.py:123`

**Solution Options**:
- [ ] Option A: Add GREETING intent with patterns for hi/hola/hello
- [ ] Option B: Require minimum query length (3+ words) for searches
- [ ] Option C: Add greeting detection in RAG engine

**Awaiting User Input**: Which approach do you prefer?

---

### 2. Grant PDF shows markdown instead of PDF
**Issue**: Opening grant details shows markdown, downloads markdown file

**Root Cause**: TBD - Need to check `pdf_url` field content
**Location**: `components/grants/PDFViewer.tsx`

**Questions for User**:
- Are PDFs stored somewhere accessible?
- What's in the `pdf_url` field - actual PDF URL or markdown?
- Should we fetch

 from a different source?

**Possible Solutions**:
- [ ] Fix `pdf_url` to point to actual PDF files
- [ ] Add separate `pdf_markdown` field for extracted text
- [ ] Update PDFViewer to handle both PDF and markdown properly

---

### 3. Missing "Ask AI Expert" button on grant cards
**Issue**: No quick way to ask about a specific grant

**Solution**: Add button to GrantCard component
**Location**: `components/grants/GrantCard.tsx`

**Implementation**:
```typescript
<Button onClick={() => onAskAI(grant)}>
  <MessageSquare className="h-4 w-4 mr-2" />
  Preguntar al Experto IA
</Button>
```

**Actions**:
- [ ] Add `onAskAI` prop to GrantCard
- [ ] Switch to Chat tab when clicked
- [ ] Pre-fill chat with "Tell me about [grant title]"

---

### 4. Grants show "Sin titulo"
**Issue**: Grant cards display "Sin titulo" instead of actual title

**Root Cause**: TBD - Check if `titulo` field exists/populated
**Location**: `components/grants/GrantCard.tsx:85`

**Possible Causes**:
- Database missing `titulo` field?
- Field named differently (e.g., `title`, `nombre`)?
- Data not populated during ingestion?

**Awaiting User Input**: Can you check a sample grant in the database?

---

### 5. Can't find open grants in Valencia
**Issue**: Search for Valencia grants returns no results

**Root Cause**: TBD - Need example query
**Location**: `apps/grants/services/search_engine.py`

**Questions for User**:
- What query did you use? (e.g., "ayudas abiertas en Valencia")
- What region code should Valencia use? (ES52, ES53, ES61?)
- Are there actually open grants in Valencia in the database?

**Debugging Steps**:
- [ ] Check region code mapping
- [ ] Test filter with correct region code
- [ ] Verify data exists in database

---

### 6. Filters not working
**Issue**: Advanced filters don't filter results

**Root Cause**: TBD - Which filters?
**Location**: `app/grants/page.tsx`, `apps/grants/services/search_engine.py`

**Questions for User**:
- Which specific filters? (organismo, regiones, abierto, dates, finalidad?)
- What happens? No results? Same results? Error?

**Actions**:
- [ ] Test each filter type
- [ ] Check backend filter application
- [ ] Verify frontend sends filters correctly

---

### 7. Empty query gives error
**Issue**: Clicking "Buscar" with empty query throws error

**Root Cause**: Backend validation requires query or filters
**Location**: `apps/grants/views.py:95-99`

**Current Code**:
```python
if not query and not filters:
    return Response(
        {"error": "Either 'query' or 'filters' must be provided"},
        status=status.HTTP_400_BAD_REQUEST
    )
```

**Solution**: Show recent grants (sorted by fecha_publicacion DESC)

**Implementation**:
- [ ] Remove validation error
- [ ] Default to showing 10 most recent grants
- [ ] Update frontend to handle empty state better

---

### 8. PDF download gets markdown file without extension
**Issue**: Downloading PDF gets markdown content as file without type

**Root Cause**: Same as Issue #2 - `pdf_url` points to wrong content
**Location**: `components/grants/PDFViewer.tsx`, `GrantDetailModal.tsx`

**Solution**: TBD after understanding PDF storage

---

## 📋 Investigation Needed

### Database Structure Check
```python
# Need to run:
from apps.grants.models import Convocatoria
c = Convocatoria.objects.first()
print(f"Titulo: {c.titulo}")
print(f"PDF URL: {c.pdf_url}")
print(f"Regiones: {c.regiones}")
print(f"Abierto: {c.abierto}")
```

### Region Code Mapping
Need to verify Spanish region codes:
- Valencia/Comunidad Valenciana: ES52
- Madrid: ES30
- Andalucía: ES61
etc.

---

## 🔧 Fix Priority

### High Priority (Blocking)
1. ✅ Empty query error (quick fix)
2. ⏳ "Sin titulo" issue (data problem)
3. ⏳ Filters not working (core functionality)
4. ⏳ PDF display/download (core functionality)

### Medium Priority
5. ⏳ Valencia search issue (may be data or filter issue)
6. ⏳ Chat greeting detection (UX improvement)

### Low Priority
7. ⏳ "Ask AI Expert" button (nice to have)

---

## 📊 Status

**Awaiting User Feedback On**:
1. Greeting detection approach preference
2. PDF URL content/structure
3. Sample query for Valencia search
4. Which filters specifically not working
5. Database structure (titulo field)

**Ready to Fix Once Info Provided**:
- All 8 issues have solution paths identified
- Just need clarification on data structure and user preferences

---

**Next**: User provides answers, then implement fixes systematically

