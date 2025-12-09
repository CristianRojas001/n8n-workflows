# Search System Architecture

**Date**: 2025-12-09
**Purpose**: Complete explanation of search mechanisms in the grants system

---

## Overview

The system implements two search interfaces that share the same underlying search engine:

1. **Direct Database Search** - `/api/v1/grants/search` - Returns raw grant results
2. **Chat-Based Search** - `/api/v1/grants/chat` - Returns conversational responses with grants

Both use **hybrid search** combining semantic (vector) similarity and traditional SQL filters.

---

## 🔍 1. Direct Database Search

**Endpoint**: `/api/v1/grants/search`
**Implementation**: [search_engine.py](../ARTISTING-main/backend/apps/grants/services/search_engine.py)

### Step-by-Step Flow

#### **Step 1: Query Processing**
```python
# Input
{
  "query": "ayudas para pymes en andalucía",
  "filters": {
    "regiones": ["ES61"],
    "abierto": true
  },
  "mode": "hybrid",  # or "semantic" or "filter"
  "limit": 5,
  "offset": 0
}
```

#### **Step 2: Semantic Search** (if query provided)

**2.1 Generate Query Embedding** ([search_engine.py:104](../ARTISTING-main/backend/apps/grants/services/search_engine.py#L104))
```python
query_embedding = generate_embedding(query)
# Returns: [0.123, -0.456, 0.789, ...] (768 dimensions via Gemini)
```

**2.2 Vector Similarity Search** ([search_engine.py:124-133](../ARTISTING-main/backend/apps/grants/services/search_engine.py#L124-L133))
```sql
SELECT
    e.extraction_id,
    1 - (e.embedding_vector <=> %s::vector) as similarity
FROM embeddings e
ORDER BY e.embedding_vector <=> %s::vector
LIMIT 50 OFFSET 0
```
- Uses **pgvector** extension
- Operator `<=>`: Cosine distance
- Similarity = `1 - distance` (higher = more similar)
- Returns top 50 candidates

**2.3 Similarity Threshold Filter** ([search_engine.py:211-214](../ARTISTING-main/backend/apps/grants/services/search_engine.py#L211-L214))
```python
MIN_SIMILARITY_THRESHOLD = 0.25
grants_list = [
    g for g in grants_list
    if similarity_scores.get(extraction_id, 0) >= 0.25
]
```

**2.4 Field Boosting** ([search_engine.py:216-243](../ARTISTING-main/backend/apps/grants/services/search_engine.py#L216-L243))
```python
# Boost scores based on field matches
if query_lower == titulo_lower:
    boosted_score *= 3.0  # Exact title match
elif query_lower in titulo_lower:
    boosted_score *= 2.0  # Partial title match

if any(word in organismo_lower for word in query_words):
    boosted_score *= 2.0  # Organismo match
```

#### **Step 3: Filter Search** (if filters provided)

**Supported Filters** ([search_engine.py:373-457](../ARTISTING-main/backend/apps/grants/services/search_engine.py#L373-L457)):

| Filter | Type | SQL Operation | Example |
|--------|------|---------------|---------|
| `organismo` | string | `ICONTAINS` | "Ministerio" |
| `ambito` | enum | Exact match | "ESTATAL" |
| `finalidad` | string | Exact code | "11" |
| `regiones` | array | Array overlap + `ICONTAINS` | ["ES61", "ES213"] |
| `fecha_desde` | date | `fecha_fin_solicitud >= fecha_desde` | "2025-12-01" |
| `fecha_hasta` | date | `fecha_inicio_solicitud <= fecha_hasta` | "2025-12-31" |
| `abierto` | boolean | Exact match | true |

**Example Query**:
```python
queryset = Convocatoria.objects.all()
queryset = queryset.filter(organismo__icontains="Ministerio")
queryset = queryset.filter(abierto=True)
queryset = queryset.filter(regiones__icontains="ES61")
```

#### **Step 4: Reciprocal Rank Fusion (RRF)** ([search_engine.py:301-371](../ARTISTING-main/backend/apps/grants/services/search_engine.py#L301-L371))

**Algorithm**: Combines semantic and filter results using RRF scoring

**Formula**: `score = 1 / (k + rank)` where `k = 60` (constant)

```python
# Get semantic results (top 50)
semantic_results = semantic_search(query, limit=50)

# Get filter results (top 50)
filter_results = filter_search(filters, limit=50)

# Calculate RRF scores
rrf_scores = {}

# Add semantic ranks
for rank, grant in enumerate(semantic_results, start=1):
    rrf_scores[grant.id] += 1 / (60 + rank)

# Add filter ranks
for rank, grant in enumerate(filter_results, start=1):
    rrf_scores[grant.id] += 1 / (60 + rank)

# Sort by combined score (descending)
sorted_grants = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
```

**Why RRF?**
- Grants appearing in **both** semantic and filter results get higher scores
- Balances relevance (semantic) with criteria (filters)
- Standard in hybrid search systems

#### **Step 5: Pagination & Response**

```python
# Apply pagination
grants_page = sorted_grants[offset:offset + limit]

# Return response
return {
    "grants": grants_page,  # List of Convocatoria objects
    "total_count": len(sorted_grants),
    "similarity_scores": [0.87, 0.82, 0.79, 0.75, 0.71],
    "search_mode": "hybrid"
}
```

---

## 💬 2. Chat-Based Search (RAG)

**Endpoint**: `/api/v1/grants/chat`
**Implementation**: [rag_engine.py](../ARTISTING-main/backend/apps/grants/services/rag_engine.py)

### Step-by-Step Flow

#### **Step 1: Intent Classification** ([rag_engine.py:94](../ARTISTING-main/backend/apps/grants/services/rag_engine.py#L94))

**Intent Types**:
```python
class QueryIntent:
    GREETING     # "hola", "buenos días"
    SEARCH       # "buscar ayudas para pymes"
    EXPLAIN      # "qué son gastos subvencionables"
    COMPARE      # "diferencias entre ayudas estatales y locales"
    RECOMMEND    # "cuál es la mejor opción para mí"
    CLARIFY      # System-generated clarifications
```

**Example**:
```python
query = "¿Qué ayudas hay para pymes en Andalucía?"
intent, confidence = intent_classifier.classify(query)
# Returns: (QueryIntent.SEARCH, 0.85)
```

**Special Case - Greetings** ([rag_engine.py:97-98](../ARTISTING-main/backend/apps/grants/services/rag_engine.py#L97-L98)):
- No grant search performed
- Returns conversational response with follow-up suggestions

#### **Step 2: Filter Extraction** ([rag_engine.py:101-102](../ARTISTING-main/backend/apps/grants/services/rag_engine.py#L101-L102))

**NLP-based filter extraction from query**:
```python
extracted_filters = intent_classifier.extract_filters_from_query(query)

# Examples:
"en Andalucía"           → {"regiones": ["ES61"]}
"abiertas"               → {"abierto": true}
"este mes"               → {"fecha_desde": "2025-12-01", "fecha_hasta": "2025-12-31"}
"del Ministerio"         → {"organismo": "Ministerio"}
```

**Merge with explicit filters**:
```python
all_filters = {**extracted_filters, **filters_from_api}
```

#### **Step 3: Execute Hybrid Search** ([rag_engine.py:105-113](../ARTISTING-main/backend/apps/grants/services/rag_engine.py#L105-L113))

```python
search_results = search_engine.hybrid_search(
    query=query,
    filters=all_filters,
    mode="hybrid",
    limit=5  # Top 5 for context
)

grants = search_results["grants"]
total_found = search_results["total_count"]
```

**Uses the same search engine as direct search!**

#### **Step 4: Clarification Check** ([rag_engine.py:121-133](../ARTISTING-main/backend/apps/grants/services/rag_engine.py#L121-L133))

**Logic**:
```python
# Skip clarification for analytical intents
analytical_intents = [COMPARE, EXPLAIN, RECOMMEND]

if intent not in analytical_intents:
    if total_found > 20:
        return "Encontré 45 subvenciones. ¿Quieres filtrar por región específica?"

    elif total_found < 3:
        return "Solo encontré 2 resultados. ¿Quieres ampliar la búsqueda?"
```

**Why skip analytical intents?**
- These queries benefit from LLM analysis regardless of result count
- "Compara todas las ayudas" is valid even with 50 results

#### **Step 5: Context Assembly** ([rag_engine.py:136](../ARTISTING-main/backend/apps/grants/services/rag_engine.py#L136))

**Progressive Loading Strategy**:
```python
def _assemble_context(grants, include_full_details=False):
    # Initial: Summary only (~500 chars)
    # On demand: Full 110+ fields
```

**Context Format** ([rag_engine.py:237-256](../ARTISTING-main/backend/apps/grants/services/rag_engine.py#L237-L256)):
```
Se encontraron 5 subvenciones relevantes:

1. Ayudas para la transformación digital de pymes
   - Número: C2023-001234
   - Organismo: Junta de Andalucía
   - Finalidad: 11 - Apoyo a las empresas
   - Región: ES61 - Andalucía, ES611 - Almería
   - Estado: Abierta
   - Importe: 5.000.000 EUR
   - Resumen: Subvención destinada a financiar proyectos de transformación...

2. [Next grant...]
```

**Data Sources**:
- Summary: `PDFExtraction.summary_preview` (LLM-generated preview)
- Full details: All fields from `Convocatoria` + `PDFExtraction` models

#### **Step 6: Model Selection** ([rag_engine.py:138-143](../ARTISTING-main/backend/apps/grants/services/rag_engine.py#L138-L143))

**Tiered Selection Strategy**:
```python
model_tier, metadata = model_selector.select_model(
    query=query,
    intent=intent.value,
    context_size=len(grants)
)

# Tiers:
ModelTier.FLASH   # Gemini Flash 2.0 Lite - $0.10/1M tokens
ModelTier.GPT4O   # GPT-4o - $2.50/1M tokens
```

**Selection Criteria**:
- **Simple queries** (SEARCH, GREETING) → Gemini Flash
- **Complex queries** (COMPARE, RECOMMEND) → GPT-4o
- **Low confidence** → Automatic retry with better model

#### **Step 7: LLM Response Generation** ([rag_engine.py:146-168](../ARTISTING-main/backend/apps/grants/services/rag_engine.py#L146-L168))

**7.1 Build Prompt** ([rag_engine.py:278-286](../ARTISTING-main/backend/apps/grants/services/rag_engine.py#L278-L286)):

```python
system_prompt = """
Eres un asistente especializado en subvenciones y ayudas públicas de España.

Directrices:
- Sé claro y conciso
- Cita siempre el número de convocatoria cuando menciones una subvención
- Si no sabes algo, admítelo (no inventes información)
- Usa un tono profesional pero amigable
- Proporciona información práctica y accionable

[Intent-specific instructions...]
"""

user_prompt = f"""
Contexto de subvenciones:
{context}

Pregunta del usuario:
{query}

Proporciona una respuesta clara y útil basada solo en la información del contexto.
Si la respuesta no está en el contexto, indícalo claramente.
"""
```

**Intent-Specific Instructions**:
- **SEARCH**: "Presenta las opciones de forma estructurada"
- **EXPLAIN**: "Explica los conceptos de forma clara, usa ejemplos"
- **COMPARE**: "Compara punto por punto, destaca ventajas/desventajas"
- **RECOMMEND**: "Justifica tus recomendaciones"

**7.2 Call LLM**:

**Gemini Flash** ([rag_engine.py:317-331](../ARTISTING-main/backend/apps/grants/services/rag_engine.py#L317-L331)):
```python
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash-lite",
    system_instruction=system_prompt
)
response = model.generate_content(user_prompt)
answer = response.text
confidence = 0.75  # Default estimate
```

**GPT-4o** ([rag_engine.py:337-359](../ARTISTING-main/backend/apps/grants/services/rag_engine.py#L337-L359)):
```python
response = openai_client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    temperature=0.7
)
answer = response.choices[0].message.content
confidence = 0.85  # Higher reliability
```

**7.3 Confidence Check & Retry** ([rag_engine.py:155-168](../ARTISTING-main/backend/apps/grants/services/rag_engine.py#L155-L168)):
```python
retry_model = model_selector.should_retry_with_better_model(
    current_model=model_tier,
    confidence=confidence
)

if retry_model:
    # Retry with GPT-4o if initial confidence too low
    answer, confidence = _generate_llm_response(
        query, context, intent, retry_model
    )
```

#### **Step 8: Generate Suggestions** ([rag_engine.py:179-184](../ARTISTING-main/backend/apps/grants/services/rag_engine.py#L179-L184))

**Filter Suggestions** (if > 10 results):
```python
"filters": [
    {"label": "Filtrar por región", "type": "region"},
    {"label": "Solo abiertas", "type": "status", "value": {"abierto": true}}
]
```

**Follow-up Questions** (based on intent):
```python
if intent == SEARCH:
    ["¿Cuál es la mejor opción para mí?",
     "¿Cuáles son los requisitos?",
     "¿Cómo se solicitan estas ayudas?"]

elif intent == EXPLAIN:
    ["¿Hay opciones similares?",
     "¿Cuál es el plazo de solicitud?"]
```

#### **Step 9: Session Storage** ([rag_engine.py:187-188](../ARTISTING-main/backend/apps/grants/services/rag_engine.py#L187-L188))

**Redis Cache for Pagination**:
```python
cache_key = f"session:{session_id}:results"
cache.set(cache_key, {
    "grant_ids": [g.id for g in grants],
    "total_found": total_found,
    "timestamp": datetime.now().isoformat()
}, timeout=3600)  # 1 hour TTL
```

**Usage**:
- User: "¿y más opciones?"
- System: Returns next 5 grants from cached results

#### **Step 10: Response**

```json
{
  "response_id": "550e8400-e29b-41d4-a716-446655440000",
  "answer": "He encontrado 5 subvenciones para pymes en Andalucía. Las más relevantes son:\n\n1. **Ayudas para transformación digital** (C2023-001234)\n   - Organismo: Junta de Andalucía\n   - Importe: 5.000.000 EUR\n   - Estado: Abierta hasta marzo 2026\n   - Ideal para proyectos de digitalización\n\n2. [More grants...]\n\n¿Te gustaría conocer más detalles sobre alguna en particular?",
  "grants": [/* 5 Convocatoria objects */],
  "suggested_actions": {
    "filters": [
      {"label": "Filtrar por región", "type": "region"},
      {"label": "Solo abiertas", "type": "status"}
    ],
    "follow_up_questions": [
      "¿Cuál es la mejor opción para mí?",
      "¿Cuáles son los requisitos?",
      "¿Cómo se solicitan estas ayudas?"
    ]
  },
  "metadata": {
    "total_found": 45,
    "showing": 5,
    "has_more": true,
    "intent": "search",
    "intent_confidence": 0.85
  },
  "model_used": "gemini-flash",
  "confidence": 0.75
}
```

---

## 🔑 Key Differences

| Aspect | Direct Search | Chat Search |
|--------|---------------|-------------|
| **Endpoint** | `/api/v1/grants/search` | `/api/v1/grants/chat` |
| **Purpose** | Find grants by criteria | Conversational Q&A |
| **Input** | Query + explicit filters | Natural language query |
| **Processing** | Hybrid search only | Intent → Extract filters → Search → LLM |
| **Output** | Raw grant list | Natural language + grants |
| **Context** | None | LLM analyzes top 5 grants |
| **Cost** | Free (DB only) | LLM tokens ($) |
| **Filters** | Explicit in request | Extracted from query text |
| **Intelligence** | Ranking algorithm | LLM reasoning & analysis |
| **Use Case** | Programmatic search | User-facing chat interface |

---

## 📊 Search Performance

### Database Layer
- **pgvector extension**: Cosine similarity in SQL
- **Fallback**: Python numpy if pgvector unavailable
- **Indexing**: Vector index on `embeddings.embedding_vector`

### Caching Strategy
- **Grant-to-extraction mapping**: 1 hour cache
- **Session results**: 1 hour Redis cache
- **No query result caching** (real-time data)

### Optimization Techniques
1. **Similarity threshold**: Filter out low-relevance results (>= 0.25)
2. **Field boosting**: Prioritize title/organismo matches
3. **RRF fusion**: Combine semantic + filter relevance
4. **Progressive loading**: Summary first, full details on demand
5. **Model tiering**: Use cheap model (Gemini) for simple queries

---

## 🛠️ Technical Stack

### Search Engine
- **Vector DB**: PostgreSQL + pgvector
- **Embeddings**: Gemini text-embedding-004 (768 dim)
- **ORM**: Django QuerySets
- **Caching**: Redis

### RAG Engine
- **Intent Classification**: Pattern matching + NLP
- **LLM (Tier 1)**: Gemini Flash 2.0 Lite
- **LLM (Tier 2)**: GPT-4o
- **Context Assembly**: Dynamic field selection

---

## 📝 Example Queries

### Direct Search
```bash
POST /api/v1/grants/search
{
  "query": "ayudas digitalización",
  "filters": {
    "regiones": ["ES61"],
    "abierto": true,
    "finalidad": "11"
  },
  "limit": 10
}
```

### Chat Search
```bash
POST /api/v1/grants/chat
{
  "query": "¿Qué ayudas hay abiertas para digitalización de pymes en Andalucía?",
  "session_id": "uuid-here"
}
```

**Response includes**:
- Natural language answer
- Top 5 relevant grants
- Suggested follow-up questions
- Filter suggestions
- Intent classification metadata

---

## 🚀 Future Enhancements

### Search Engine
- [ ] Amount filtering (parse CharField amounts)
- [ ] Query result caching (5 min TTL)
- [ ] A/B testing for RRF parameters

### RAG Engine
- [ ] Conversation history (multi-turn context)
- [ ] Citation tracking (which grant answered which part)
- [ ] User feedback loop (thumbs up/down)
- [ ] Streaming responses (SSE)

---

**Last Updated**: 2025-12-09
**Maintained By**: InfoSubvenciones Team
