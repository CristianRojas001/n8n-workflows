# Day 6 Testing & Polish Plan

**Date**: 2025-12-04
**Status**: 🚧 **IN PROGRESS**
**Goal**: Comprehensive testing and bug fixes

---

## 🎯 Testing Objectives

1. Verify all backend endpoints work correctly
2. Test frontend components with real data
3. Validate search accuracy (semantic, filter, hybrid)
4. Verify chat responses and LLM routing
5. Test mobile responsiveness
6. Identify and fix bugs
7. Performance validation

---

## 📋 Backend API Tests

### Search Endpoint Tests

#### Test 1: Semantic Search Only
```bash
curl -X POST http://127.0.0.1:8000/api/v1/grants/search/ \
  -H "Content-Type: application/json" \
  -d '{"query":"ayudas para empresas tecnológicas","mode":"semantic","page_size":5}'
```
**Expected**: Returns 5 most relevant grants based on semantic similarity

#### Test 2: Filter Search Only
```bash
curl -X POST http://127.0.0.1:8000/api/v1/grants/search/ \
  -H "Content-Type: application/json" \
  -d '{"filters":{"abierto":true,"regiones":["ES30"]},"mode":"filter","page_size":5}'
```
**Expected**: Returns only open grants in Madrid region

#### Test 3: Hybrid Search (Default)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/grants/search/ \
  -H "Content-Type: application/json" \
  -d '{"query":"cultura","filters":{"abierto":true},"page_size":5}'
```
**Expected**: Combines semantic + filter with RRF ranking

#### Test 4: Empty Query with Filters
```bash
curl -X POST http://127.0.0.1:8000/api/v1/grants/search/ \
  -H "Content-Type: application/json" \
  -d '{"filters":{"organismo":"Ministerio"},"page_size":10}'
```
**Expected**: Filter-only search by organismo

#### Test 5: Pagination
```bash
curl -X POST http://127.0.0.1:8000/api/v1/grants/search/ \
  -H "Content-Type: application/json" \
  -d '{"query":"ayudas","page":1,"page_size":5}'

curl -X POST http://127.0.0.1:8000/api/v1/grants/search/ \
  -H "Content-Type: application/json" \
  -d '{"query":"ayudas","page":2,"page_size":5}'
```
**Expected**: Different grants on page 2, no duplicates

#### Test 6: Date Range Filter
```bash
curl -X POST http://127.0.0.1:8000/api/v1/grants/search/ \
  -H "Content-Type: application/json" \
  -d '{"filters":{"fecha_desde":"2024-01-01","fecha_hasta":"2024-12-31"},"page_size":10}'
```
**Expected**: Only grants published in 2024

#### Test 7: Multiple Regions
```bash
curl -X POST http://127.0.0.1:8000/api/v1/grants/search/ \
  -H "Content-Type: application/json" \
  -d '{"filters":{"regiones":["ES30","ES61"]},"page_size":10}'
```
**Expected**: Grants from Madrid OR Andalucía

#### Test 8: No Results
```bash
curl -X POST http://127.0.0.1:8000/api/v1/grants/search/ \
  -H "Content-Type: application/json" \
  -d '{"query":"quantum computing nanotechnology","page_size":5}'
```
**Expected**: Empty grants array, total_count: 0

---

### Chat Endpoint Tests

#### Test 9: Simple Search Intent
```bash
curl -X POST http://127.0.0.1:8000/api/v1/grants/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message":"¿Qué ayudas hay para pymes?"}'
```
**Expected**: Intent: search, model: gemini-2.5-flash-lite, grants returned

#### Test 10: Explain Intent
```bash
curl -X POST http://127.0.0.1:8000/api/v1/grants/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message":"Explica qué son los gastos subvencionables"}'
```
**Expected**: Intent: explain, detailed explanation, grants as examples

#### Test 11: Compare Intent
```bash
curl -X POST http://127.0.0.1:8000/api/v1/grants/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message":"Compara las ayudas para empresas y autónomos"}'
```
**Expected**: Intent: compare, comparative analysis, no clarification

#### Test 12: Recommend Intent
```bash
curl -X POST http://127.0.0.1:8000/api/v1/grants/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message":"¿Cuál me conviene para mi startup en Madrid?"}'
```
**Expected**: Intent: recommend, personalized suggestions

#### Test 13: Clarification Trigger (Too Vague)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/grants/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message":"ayudas"}'
```
**Expected**: model_used: system-clarification, suggested actions

#### Test 14: Complex Query (Should Use Better Model)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/grants/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message":"Analiza en detalle las diferencias entre las subvenciones para I+D en el sector tecnológico versus el sector cultural, considerando criterios de elegibilidad, cuantías máximas, plazos de ejecución y requisitos de justificación. Dame una comparativa exhaustiva."}'
```
**Expected**: High complexity score (>60), model: gpt-4o or high-tier

#### Test 15: Conversation Context
```bash
# First message
curl -X POST http://127.0.0.1:8000/api/v1/grants/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message":"Busca ayudas en Madrid"}'

# Follow-up (use conversation_id from response)
curl -X POST http://127.0.0.1:8000/api/v1/grants/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message":"¿Y en Andalucía?","conversation_id":"<uuid>"}'
```
**Expected**: Context maintained across messages

---

### Grant Details Endpoint Tests

#### Test 16: Get Grant Summary
```bash
curl http://127.0.0.1:8000/api/v1/grants/48/
```
**Expected**: 15 summary fields returned

#### Test 17: Get Full Grant Details
```bash
curl http://127.0.0.1:8000/api/v1/grants/48/details/
```
**Expected**: All 110+ fields returned, including pdf_extraction data

#### Test 18: Invalid Grant ID
```bash
curl http://127.0.0.1:8000/api/v1/grants/99999/
```
**Expected**: 404 Not Found

---

## 🖥️ Frontend Tests

### Grant Search Page Tests

#### Test 19: Initial Page Load
- Navigate to http://localhost:3000/grants
- **Check**: Empty state displays with search examples
- **Check**: Search form loads correctly
- **Check**: No console errors

#### Test 20: Basic Search
- Enter query: "empresas"
- Click "Buscar"
- **Check**: Loading skeletons appear
- **Check**: Results grid displays grants
- **Check**: Grant cards show all information correctly
- **Check**: Status badges (Abierta/Cerrada) correct

#### Test 21: Advanced Filters
- Click "Filtros" button
- Toggle "Solo convocatorias abiertas"
- Select region: "Madrid"
- Enter organismo: "Ministerio"
- Click "Buscar"
- **Check**: Filter badge shows count
- **Check**: Results match filters
- **Check**: Clear filters button works

#### Test 22: Grant Detail Modal
- Click "Ver detalles" on any grant
- **Check**: Modal opens full-screen
- **Check**: All grant information displays
- **Check**: Organized sections visible
- **Check**: Close button works
- **Check**: Scrolling works in modal

#### Test 23: PDF Viewer
- Open grant detail modal
- **Check**: PDF tabs visible (Contenido, Vista previa)
- Click "Vista previa" tab
- **Check**: PDF iframe loads (or shows error alert)
- Click "Descargar PDF" button
- **Check**: PDF opens in new tab

#### Test 24: Pagination
- Perform search with many results
- **Check**: "Siguiente" button enabled
- Click "Siguiente"
- **Check**: Different grants on page 2
- **Check**: "Anterior" button now enabled
- **Check**: Page counter updates

#### Test 25: Empty Results
- Search for: "quantum nanotechnology blockchain AI"
- **Check**: "No se encontraron subvenciones" message
- **Check**: Suggestions to adjust filters
- Click "Limpiar búsqueda"
- **Check**: Returns to initial state

#### Test 26: Error Handling
- Stop Django backend
- Perform search
- **Check**: Error alert displays
- **Check**: User-friendly error message
- Restart backend and retry

---

## 📱 Mobile Responsiveness Tests

#### Test 27: Mobile View (375px width)
- Use browser DevTools mobile view
- **Check**: Search form stacks vertically
- **Check**: Grant cards take full width
- **Check**: Filters panel scrollable
- **Check**: Modal adapts to mobile
- **Check**: Text is readable
- **Check**: Buttons are tappable (44px min)

#### Test 28: Tablet View (768px width)
- **Check**: 2-column grid for grants
- **Check**: Filters side-by-side in 2 columns
- **Check**: Modal width appropriate

#### Test 29: Desktop View (1920px width)
- **Check**: 3-column grid for grants
- **Check**: Max-width container centers content
- **Check**: No horizontal scroll

---

## ⚡ Performance Tests

#### Test 30: Search Response Time
- Measure search endpoint response time
- **Target**: < 2 seconds
- **Check**: Actual time (already ~1.06s ✅)

#### Test 31: Chat Response Time
- Measure chat endpoint response time
- **Target**: < 5 seconds
- **Check**: Gemini Flash ~2-3s ✅
- **Check**: GPT-4o ~4-5s ✅

#### Test 32: Page Load Time
- Measure /grants page first load
- **Target**: < 3 seconds
- Use Lighthouse for audit

#### Test 33: Large Result Set
- Search with no filters (all grants)
- **Check**: Pagination handles 100+ results
- **Check**: No memory leaks
- **Check**: Smooth scrolling

---

## 🐛 Edge Cases & Error Scenarios

#### Test 34: Special Characters in Query
- Query: "I+D & empresas (más del 50%)"
- **Check**: Search doesn't crash
- **Check**: Results returned correctly

#### Test 35: Very Long Query
- Query: 500+ character string
- **Check**: Backend handles gracefully
- **Check**: No 414 URI Too Long error

#### Test 36: SQL Injection Attempt
- Filter: `{"organismo":"'; DROP TABLE convocatorias; --"}`
- **Check**: No SQL injection vulnerability
- **Check**: Treated as literal string

#### Test 37: XSS Attempt
- Query: `<script>alert('XSS')</script>`
- **Check**: Escaped properly in frontend
- **Check**: No script execution

#### Test 38: Invalid Filter Values
- Date: "not-a-date"
- Region: "INVALID"
- **Check**: Validation error or graceful handling

#### Test 39: Concurrent Requests
- Send 10 search requests simultaneously
- **Check**: All return correctly
- **Check**: No race conditions
- **Check**: Cache works properly

#### Test 40: Network Timeout
- Simulate slow network (Chrome DevTools)
- **Check**: Loading state persists
- **Check**: Timeout after reasonable time
- **Check**: Error message displayed

---

## 🔒 Security Tests

#### Test 41: CORS
- Make request from different origin
- **Check**: CORS headers configured (if needed)
- **Check**: Unauthorized origins blocked

#### Test 42: Authentication
- Access /grants without login
- **Check**: Protected route redirects to login
- **Check**: After login, grants page accessible

#### Test 43: Database Read-Only User
- Verify grants_readonly can only SELECT
- **Check**: No INSERT/UPDATE/DELETE possible
- **Check**: Connection limit enforced (15)

---

## ✅ Acceptance Criteria

### Critical (Must Pass)
- [ ] All search modes work (semantic, filter, hybrid)
- [ ] Chat endpoint returns proper responses
- [ ] Grant details display correctly
- [ ] Pagination works
- [ ] Mobile responsive
- [ ] No console errors
- [ ] Error handling graceful
- [ ] Backend filters enforced (abierto=true works)

### Important (Should Pass)
- [ ] PDF viewer functional
- [ ] Relevance scores accurate
- [ ] LLM routing correct (Flash vs GPT-4o)
- [ ] Intent classification accurate
- [ ] Performance targets met
- [ ] No security vulnerabilities

### Nice to Have
- [ ] Loading animations smooth
- [ ] Accessibility (keyboard navigation, screen readers)
- [ ] Analytics tracking
- [ ] SEO optimization

---

## 📊 Test Results Template

```markdown
## Test Results - [Date]

### Backend Tests (18 tests)
- ✅ Passed: X/18
- ❌ Failed: Y/18
- Failures: [list]

### Frontend Tests (12 tests)
- ✅ Passed: X/12
- ❌ Failed: Y/12
- Failures: [list]

### Performance Tests (4 tests)
- ✅ Passed: X/4
- ❌ Failed: Y/4
- Metrics: [list]

### Edge Case Tests (7 tests)
- ✅ Passed: X/7
- ❌ Failed: Y/7
- Failures: [list]

### Security Tests (3 tests)
- ✅ Passed: X/3
- ❌ Failed: Y/3
- Findings: [list]

### Overall: X/44 tests passing (Y%)
```

---

## 🔧 Bug Fix Process

1. **Document Bug**:
   - Test number that failed
   - Expected vs actual behavior
   - Steps to reproduce
   - Screenshots/logs

2. **Prioritize**:
   - Critical: Blocks core functionality
   - High: Affects user experience
   - Medium: Minor issues
   - Low: Cosmetic

3. **Fix & Verify**:
   - Implement fix
   - Rerun failed test
   - Check for regressions
   - Update documentation

4. **Track Progress**:
   - Use TodoWrite for tracking
   - Update test results
   - Document in DAY_6_RESULTS.md

---

## 📝 Testing Tools

- **Backend**: curl, Python test scripts
- **Frontend**: Browser DevTools, Lighthouse
- **Mobile**: Chrome DevTools Device Mode
- **Performance**: Network tab, Chrome Performance
- **Security**: Manual testing, OWASP guidelines

---

**Next**: Execute tests and document results in DAY_6_RESULTS.md
