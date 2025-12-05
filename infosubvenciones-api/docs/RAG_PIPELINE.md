# InfoSubvenciones RAG Pipeline

> Purpose: capture every moving part in the retrieval-augmented generation system. This document provides complete technical specifications for the ingestion and search pipeline.

## 1. Use Case Summary

### Primary User Tasks
- **Natural Language Search**: "¿Qué ayudas hay para autónomos de artes escénicas en Madrid con presupuesto entre 10k-50k?"
- **Filtered Discovery**: Browse grants by sector (Cultura/Comercio), region, budget, deadlines
- **Grant Analysis**: Read AI-generated summaries of complex PDF documentation
- **Source Verification**: Access original convocatoria PDFs with citations

### Domain Sources
- **InfoSubvenciones API**: Official Spanish government grants database
  - 105,139 culture grants (finalidad=11)
  - 31,781 commerce grants (finalidad=14)
  - Filter: PYMES + autónomos (tiposBeneficiario=3,2)
  - Status: Currently open (abierto=true)
- **Document Types**: PDF convocatorias, bases reguladoras, anexos, resoluciones
- **Languages**: Spanish (primary), Catalan, Basque, Galician (regional)
- **Update Frequency**: Initial one-time load of 136k grants, future updates monthly/quarterly

### Response Format Requirements
- **Summaries**: 200-250 words in Spanish, regardless of source document language
- **Structured Fields**: JSON schema with 20+ extracted fields (gastos_subvencionables, requisitos, etc.)
- **Citations**: Every result must link to original numero_convocatoria + PDF source
- **Metadata**: Sector, region, organo, budget, deadlines for filtering
- **Format**: JSON API responses, HTML for frontend

## 2. Data Ingestion

### Sources & Frequency

| Source | Type | Schedule | Volume | Notes |
|--------|------|----------|--------|-------|
| InfoSubvenciones API | Pull (HTTP REST) | One-time initial load | 136,920 grants | Paginated, 100 items/page |
| Future Updates | Pull (HTTP REST) | Monthly/Quarterly | ~1,000-5,000 new | TBD - monitor API for changes |

**API Endpoints**:
- Search: `GET /convocatorias/busqueda?abierto=true&finalidad={11|14}&tiposBeneficiario=3,2&page={n}&size=100`
- Detail: `GET /convocatorias?numConv={numeroConvocatoria}`
- PDF: `GET /convocatorias/documentos?idDocumento={id}`

### Parsing/Normalization

#### Phase 1: API Metadata Extraction
**Tool**: Python `requests` + Pydantic validation

**Fields Extracted** (40+ fields from API):
- **Identificación**: numero_convocatoria, api_id, codigo_bdns
- **Descripción**: descripcion, descripcion_leng
- **Organismo**: organo_nivel1, organo_nivel2, organo_nivel3
- **Clasificación**: finalidad_descripcion, tipo_convocatoria
- **Fechas**: fecha_recepcion, fecha_inicio_solicitud, fecha_fin_solicitud, abierto
- **Económico**: presupuesto_total
- **URLs**: sede_electronica, url_bases_reguladoras
- **Arrays (stored as JSONB)**: sectores, tipos_beneficiarios, regiones, fondos, instrumentos, documentos

**Normalization Rules**:
- Dates: ISO 8601 format (YYYY-MM-DD)
- Currency: Decimal(15,2)
- Booleans: True/False from API strings
- Null handling: Empty strings → NULL, missing fields → NULL
- JSONB arrays: Preserve original structure, validate schema

#### Phase 2: PDF Conversion
**Tools**:
- Primary: **pymupdf** (fitz) - Fast, good for simple layouts
- Fallback: **marker-pdf** - Better for complex tables, multi-column

**Process**:
1. Download PDF binary (calculate SHA256 hash)
2. Check for duplicate hash → skip if exists
3. Convert to Markdown:
   ```python
   import fitz
   doc = fitz.open(pdf_path)
   markdown = ""
   for page in doc:
       markdown += page.get_text("markdown")
   ```
4. If pymupdf fails → Try marker-pdf
5. Save to `data/markdown/{numero_convocatoria}_{doc_id}.md`

**Quality Checks**:
- File size > 0 bytes
- Markdown length > 100 chars
- No corruption errors
- Text extraction ratio > 50% of PDF size

#### Phase 3: LLM Processing (Gemini 2.5 Flash-Lite)
**Model**: value of `GEMINI_MODEL` (default `gemini-2.5-flash-lite`)
**Temperature**: 0.1 (deterministic)
**Max Tokens**: 8192

**Prompt Template**:
```
Eres un asistente experto en analizar convocatorias de subvenciones españolas.

Analiza el siguiente documento y realiza dos tareas:

1. RESUMEN (200-250 palabras en español):
- Propósito de la convocatoria
- Beneficiarios objetivo
- Cuantía o presupuesto
- Plazos clave
- Requisitos principales

2. EXTRACCIÓN DE CAMPOS (JSON estructurado):
{schema_json}

IMPORTANTE:
- Si el documento está en catalán, euskera o gallego, genera el resumen en español (castellano)
- Solo extrae información que aparezca explícitamente en el documento
- Si un campo no está presente, usa null
- Detecta el idioma original del documento

DOCUMENTO:
{markdown_content}
```

**Extracted Fields Schema** (20+ fields):
```json
{
  "gastos_subvencionables": "string | null",
  "actividades_elegibles": "string | null",
  "garantias_requeridas": "string | null",
  "compatibilidad_otras_ayudas": "string | null",
  "reglas_subcontratacion": "string | null",
  "plazo_ejecucion_proyecto": "string | null",
  "plazo_justificacion": "string | null",
  "forma_pago": "string | null",
  "forma_justificacion": "string | null",
  "requisitos_publicidad": "string | null",
  "modificaciones_permitidas": "string | null",
  "cuantia_individual": "string | null",
  "presupuesto_min_proyecto": "float | null",
  "presupuesto_max_proyecto": "float | null",
  "aplicacion_presupuestaria": "string | null",
  "beneficiario_especifico": "string | null",
  "csv_verificacion": "string | null",
  "firmantes": "string | null",
  "finalidad_detallada": "string | null",
  "original_language": "string"  // 'es', 'ca', 'eu', 'gl'
}
```

**Response Parsing**:
- Extract summary text (validate 200-250 words)
- Parse JSON fields (validate with Pydantic)
- Handle LLM errors (retry with truncated content if >8k tokens)

### Storage Targets

#### PostgreSQL Tables (4 main tables)

**1. staging_items** (Processing Tracker)
```sql
CREATE TABLE staging_items (
    id SERIAL PRIMARY KEY,
    numero_convocatoria VARCHAR(50) UNIQUE NOT NULL,
    convocatoria_id INTEGER,
    status VARCHAR(20) DEFAULT 'pending',
    pdf_hash VARCHAR(64),
    error_type VARCHAR(50),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    INDEX idx_status (status)
);
```

**2. convocatorias** (API Metadata - 40+ fields)
- All API fields as columns
- JSONB for arrays (sectores, regiones, documentos)
- GIN indexes on JSONB fields for fast filtering

**3. pdf_extractions** (LLM Extracted Fields - 20+ fields)
- Foreign key to convocatorias
- All extracted fields from Gemini
- Confidence scores

**4. embeddings** (Vectors + Summaries)
```sql
CREATE TABLE embeddings (
    id SERIAL PRIMARY KEY,
    convocatoria_id INTEGER REFERENCES convocatorias(id),
    summary_text TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_convocatoria_id (convocatoria_id)
);

CREATE INDEX ON embeddings USING hnsw (embedding vector_cosine_ops);
```

#### File Storage
- **PDFs**: `./data/pdfs/{numero_convocatoria}_{doc_id}.pdf` (~50GB total)
- **Markdown**: `./data/markdown/{numero_convocatoria}_{doc_id}.md` (~5GB total)
- **Backup**: Optional cloud storage (S3/GCS) for disaster recovery

### Quality Checks

**Pre-Ingestion**:
- PostgreSQL version >= 15 ✓
- pgvector extension installed ✓
- Redis connection alive
- Disk space > 60GB available
- API keys valid (Gemini, OpenAI)

**During Ingestion**:
- Duplicate detection by numero_convocatoria
- Duplicate detection by PDF hash
- Validation of API responses (Pydantic schemas)
- LLM response validation (summary length, JSON schema)
- Embedding dimension check (1536)

**Post-Ingestion**:
```sql
-- Check for orphaned records
SELECT COUNT(*) FROM pdf_extractions
WHERE convocatoria_id NOT IN (SELECT id FROM convocatorias);

-- Check for missing embeddings
SELECT COUNT(*) FROM convocatorias c
LEFT JOIN embeddings e ON c.id = e.convocatoria_id
WHERE e.id IS NULL;

-- Summary quality
SELECT
    CASE
        WHEN array_length(regexp_split_to_array(summary_text, '\s+'), 1) < 200 THEN 'too_short'
        WHEN array_length(regexp_split_to_array(summary_text, '\s+'), 1) > 250 THEN 'too_long'
        ELSE 'ok'
    END as quality,
    COUNT(*)
FROM embeddings
GROUP BY quality;
```

**Alerting**:
- Error rate > 5% → Email notification
- Stuck items (processing > 1 hour) → Alert
- Disk space < 10GB → Alert

## 3. Indexing & Retrieval Store

### Vector Store: PostgreSQL + pgvector

**Why pgvector**:
- Same database as relational data → No sync issues
- HNSW index for fast ANN search
- Cost-effective (no separate vector DB)
- Supports hybrid search (vector + filters)

**Index Configuration**:
```sql
-- HNSW index for cosine similarity
CREATE INDEX ON embeddings USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Composite indexes for filtered search
CREATE INDEX idx_conv_sector_region ON convocatorias
USING GIN (sectores, regiones);

CREATE INDEX idx_conv_dates ON convocatorias
(fecha_fin_solicitud, abierto);
```

**Performance Tuning**:
- `m = 16`: HNSW graph connections (balance speed/accuracy)
- `ef_construction = 64`: Build-time search depth
- `shared_buffers = 4GB`: PostgreSQL memory
- `work_mem = 256MB`: Query memory

### No Traditional Search Engine

Unlike typical RAG systems, we **don't use Elasticsearch/OpenSearch** because:
1. **Small corpus**: 136k items fit in PostgreSQL
2. **Structured filters**: PostgreSQL handles these natively
3. **Vector-first search**: pgvector is sufficient
4. **Cost**: One database instead of two systems
5. **Simplicity**: Easier maintenance

### Chunking Strategy

**No chunking needed** - Each grant is treated as a single document:
- Summary text (200-250 words) is the embedding unit
- PDFs are processed holistically (not split into chunks)
- Metadata provides context (sector, region, etc.)

**Rationale**:
- Grants are coherent documents (unlike large books)
- User queries target specific grants, not paragraphs
- Summary already condenses the full document

### Reranking

**Initial**: Cosine similarity from pgvector (top-k results)

**Future Enhancements** (optional):
- **Metadata boosting**: Boost exact sector/region matches
- **Recency bias**: Prefer grants with later deadlines
- **Budget relevance**: Prefer grants matching user's budget filter
- **Cross-encoder reranking**: Use a reranking model on top-20 results

**Current approach**: Simple similarity + filters is sufficient for MVP

## 4. Embeddings & Vector Store

### Embedding Model
**Provider**: OpenAI
**Model**: `text-embedding-3-small`
**Dimensions**: 1536
**Cost**: $0.02 per 1M tokens

**Why OpenAI**:
- Best retrieval quality for Spanish + English
- Fast API (3M tokens/min)
- Cost-effective ($1.23 total for 136k summaries)
- Mature, stable service

**Alternative (future)**: Multilingual models (e.g., `multilingual-e5-large`) if cost becomes issue

### Vector DB: pgvector in PostgreSQL

**Storage**:
- Table: `embeddings`
- Column: `embedding vector(1536)`
- Index: HNSW (approximate nearest neighbor)

**Query Example**:
```sql
SELECT
    e.id,
    e.summary_text,
    c.numero_convocatoria,
    c.descripcion,
    1 - (e.embedding <=> query_vector) as similarity
FROM embeddings e
JOIN convocatorias c ON e.convocatoria_id = c.id
WHERE c.abierto = true
  AND c.sectores @> '[{"codigo": "R"}]'::jsonb
ORDER BY e.embedding <=> query_vector
LIMIT 20;
```

**Operators**:
- `<=>`: Cosine distance (pgvector)
- `@>`: JSONB contains

### Fields Stored in Embeddings Table

```sql
CREATE TABLE embeddings (
    id SERIAL PRIMARY KEY,
    convocatoria_id INTEGER NOT NULL,
    summary_text TEXT NOT NULL,  -- 200-250 words Spanish summary
    summary_language VARCHAR(10) DEFAULT 'es',
    embedding vector(1536) NOT NULL,
    metadata JSONB,  -- Denormalized for fast access
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Metadata JSONB Structure** (denormalized for speed):
```json
{
    "numero_convocatoria": "871838",
    "descripcion": "Ayudas para proyectos de artes escénicas",
    "organo_nivel1": "ESTADO",
    "organo_nivel2": "MINISTERIO DE CULTURA",
    "sectores": ["R - Actividades artísticas, recreativas y de entretenimiento"],
    "tipos_beneficiarios": ["Pequeñas y medianas empresas", "Autónomos"],
    "regiones": ["ES300 - Madrid"],
    "presupuesto_total": 50000.00,
    "fecha_inicio_solicitud": "2025-01-01",
    "fecha_fin_solicitud": "2025-12-31",
    "abierto": true,
    "pdf_url": "https://www.infosubvenciones.es/bdnstrans/api/convocatorias/documentos?idDocumento=12345",
    "sede_electronica": "https://sede.cultura.gob.es"
}
```

**Why Denormalize**:
- Avoid JOINs during vector search (performance)
- Frontend gets everything in one query
- pgvector can't efficiently JOIN during similarity search

### Usage: Similarity Search

**Process**:
1. User query: "ayudas para autónomos de artes escénicas en Madrid"
2. Embed query: OpenAI API → query_vector(1536)
3. PostgreSQL search:
   ```sql
   SELECT * FROM embeddings
   WHERE metadata->>'abierto' = 'true'
     AND metadata->'regiones' @> '["ES300 - Madrid"]'
   ORDER BY embedding <=> query_vector
   LIMIT 20
   ```
4. Return results with similarity scores

**Caching** (future):
- Cache frequent queries in Redis
- TTL: 1 hour
- Key: hash(query + filters)

## 5. LLM Invocation

### Provider/Model
**LLM**: Google Gemini 2.5 Flash-Lite (configurable)
**Model ID**: `GEMINI_MODEL` (default `gemini-2.5-flash-lite`)
**Use Case**: Summary generation + field extraction (NOT query answering)

**Why Gemini**:
- Free tier: 2M tokens/min (may cover entire ingestion)
- Cost if paid: ~$70 for 136k PDFs (3x cheaper than GPT-4o)
- Fast: Good throughput
- Quality: Sufficient for summarization + extraction

**Alternative**: GPT-4o-mini as fallback if rate limited

### Prompt Architecture

**System Prompt**:
```
Eres un asistente experto en analizar convocatorias de subvenciones españolas.
Tu tarea es generar resúmenes concisos y extraer campos estructurados de documentos PDF.
```

**User Prompt Template**:
```
Analiza el siguiente documento de convocatoria y realiza:

1. RESUMEN (200-250 palabras en español):
   - Propósito de la convocatoria
   - Beneficiarios objetivo
   - Cuantía o presupuesto disponible
   - Plazos clave (solicitud, ejecución, justificación)
   - Requisitos principales

2. EXTRACCIÓN DE CAMPOS:
Extrae la siguiente información en formato JSON:
{schema}

REGLAS IMPORTANTES:
- Si el documento está en catalán, euskera o gallego, genera el resumen en español
- Solo extrae información explícita (no inventes datos)
- Si un campo no aparece, usa null
- Detecta el idioma original en el campo "original_language"

DOCUMENTO:
{markdown_content}

Responde en formato:
RESUMEN:
[tu resumen aquí]

CAMPOS:
```json
{tu json aquí}
```
```

**Prompt Variables**:
- `{schema}`: JSON schema with field descriptions
- `{markdown_content}`: Converted PDF text (max 8k tokens)

### Streaming/Latency

**No Streaming**: Batch processing, not user-facing
**Timeout**: 30 seconds per request
**Retry Policy**:
- Transient errors (500, network): Retry 3x with exponential backoff
- Rate limit (429): Wait 60s, retry
- Token limit exceeded: Truncate markdown to 7k tokens, retry once
- Persistent failures: Mark as failed, manual review

**Expected Latency**:
- Average: 3-5 seconds per PDF
- 95th percentile: 10 seconds
- Throughput: ~666 PDFs per minute (with rate limits)

### Cost Controls

**Monitoring**:
- Log token usage per request (input + output)
- Track cumulative cost in database
- Alert if cost > $100 (expected ~$70)

**Limits**:
- Max input tokens: 7000 (truncate if exceeded)
- Max output tokens: 1000 (summary + fields fit easily)
- Batch processing: Process in chunks, respect rate limits

**Free Tier Strategy**:
- Start with Gemini free tier
- Monitor usage against limits (2M tokens/min)
- Spread processing over time if approaching limits
- Switch to paid if needed

## 6. Response Post-processing

### Citation Formatting

**Every result includes**:
- `numero_convocatoria`: Unique ID
- `pdf_url`: Link to download original PDF
- `sede_electronica`: Link to official government page
- `api_source`: InfoSubvenciones API reference

**Frontend Display**:
```html
<CitationBadge>
  Fuente: Convocatoria #871838
  <a href="/api/v1/grants/871838/pdf">Ver PDF original</a>
  <a href="{sede_electronica}">Sede Electrónica</a>
</CitationBadge>
```

### Validation

**Automated Checks**:
- Summary word count: 200-250 words
- Language: Spanish (detect with `langdetect`)
- Field schema: Pydantic validation
- No hallucinations: Check extracted budget against API budget (warn if >20% difference)

**Manual QA** (random sample):
- Review 100 random summaries for quality
- Check field extraction accuracy on 50 PDFs
- Validate citations are correct

**Confidence Scores**:
- Store `extraction_confidence` in `pdf_extractions` table
- Based on: field completeness, LLM response structure, validation checks
- Range: 0.0-1.0 (1.0 = all fields extracted, no validation issues)

### Semantic Cache

**Not implemented in MVP** (future enhancement)

**Future Design**:
- Store frequent query-result pairs in Redis
- Key: `hash(query + filters)`
- Value: Top-20 grant IDs + scores
- TTL: 1 hour (grants don't change often)
- Invalidation: On database updates

### Moderation/Filters

**Not needed** - No user-generated content, trusted government data source

**Future** (if adding user comments/reviews):
- Profanity filter
- PII detection (email, phone)
- Spam detection

## 7. Monitoring & Metrics

### Operational Metrics

**Ingestion**:
- **Items/hour**: Track completion rate (target: 2000-3000/hr)
- **Success rate**: % of items reaching "completed" status (target: >95%)
- **Error distribution**: Count by error_type (api_error, pdf_conversion_failed, etc.)
- **Retry statistics**: Average retries per item
- **Processing time**: Average time per stage (fetch, PDF, LLM, embedding)
- **Cost tracking**: Cumulative API costs (Gemini + OpenAI)

**Queries** (from `scripts/export_stats.py`):
```sql
-- Progress overview
SELECT status, COUNT(*),
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM staging_items), 2) as pct
FROM staging_items GROUP BY status;

-- Processing rate
SELECT DATE_TRUNC('hour', completed_at) as hour, COUNT(*) as completed
FROM staging_items
WHERE status = 'completed' AND completed_at > NOW() - INTERVAL '24 hours'
GROUP BY hour ORDER BY hour DESC;

-- Error breakdown
SELECT error_type, COUNT(*) FROM staging_items
WHERE status = 'failed' GROUP BY error_type ORDER BY COUNT(*) DESC;
```

**Search API**:
- **Query latency**: p50, p95, p99 (target: <2s)
- **Throughput**: Queries per second
- **Error rate**: 4xx/5xx responses
- **Cache hit rate** (future)

### Quality Metrics

**Data Quality**:
- **Summary length distribution**: Count by too_short/ok/too_long
- **Field extraction completeness**: % of PDFs with each field populated
- **Language detection**: Count by original_language (es/ca/eu/gl)
- **Vector quality**: Verify no null embeddings, dimension = 1536

**Search Relevance** (manual testing):
- Test 20 sample queries
- Evaluate top-5 results for relevance
- Target: >80% relevant results

**User Feedback** (future):
- Thumbs up/down on results
- "Was this helpful?" on grant details
- Track click-through rate (search → detail → PDF)

### Alerting

**Triggers**:
- Ingestion error rate > 5% → Email alert
- Processing stuck (items in "processing" > 1 hour) → Alert
- Disk space < 10GB → Alert
- API costs > $100 → Alert
- Search API latency p95 > 5s → Alert

**Tools**:
- PostgreSQL triggers → Python email script
- Cron job monitoring (scripts/export_stats.py every 30 min)
- Celery Flower for task monitoring (optional web UI)

**Dashboards** (future):
- Grafana + PostgreSQL datasource
- Real-time progress, error rates, costs
- Search latency, popular queries

## 8. Open Questions / TODOs

### Resolved
- ✅ Embedding model: OpenAI text-embedding-3-small
- ✅ Vector DB: pgvector in PostgreSQL
- ✅ LLM: Gemini 2.0 Flash
- ✅ No chunking needed (full document summaries)

### To Be Resolved
- **Ingestion schedule**: One-time or periodic updates? (Monthly/Quarterly?)
- **PDF storage**: Keep all PDFs locally (50GB) or download on-demand?
- **Reranking**: Implement metadata boosting or keep simple similarity?
- **Semantic cache**: Add Redis caching for frequent queries?
- **Update strategy**: How to detect new grants from API? (Compare API IDs, use fechaRecepcion)
- **Backup**: S3/GCS for PDF backup or rely on API as source of truth?

---

**Last Updated**: 2025-12-01
**Status**: Complete specification, ready for implementation
**Next Step**: Fill UX_SURFACES.md template
