# Database Schema Reference

> **Source of Truth**: This document reflects the actual PostgreSQL database schema in production.
>
> **Last Updated**: 2025-12-02
>
> **Note**: This is a reference document. The schema shown here represents the current state of the database. All code models must match this schema.

---

## Tables Overview

1. **convocatorias** - Grant opportunities from InfoSubvenciones API
2. **staging_items** - Pipeline tracking (fetcher → PDF → LLM → embedder)
3. **pdf_extractions** - Structured data extracted from PDFs by LLM
4. **embeddings** - Vector embeddings for semantic search (pgvector)

---

## Table: `convocatorias`

Stores grant opportunity data fetched from InfoSubvenciones API.

```sql
CREATE TABLE public.convocatorias (
  id integer NOT NULL DEFAULT nextval('convocatorias_id_seq'::regclass),
  numero_convocatoria character varying NOT NULL,
  codigo character varying,
  titulo text,
  descripcion text,
  objeto text,
  organismo character varying,
  organismo_id character varying,
  departamento character varying,
  tipo_administracion character varying,
  nivel_administracion character varying,
  finalidad character varying,
  finalidad_descripcion character varying,
  sectores ARRAY,
  regiones ARRAY,
  ambito character varying,
  tipos_beneficiario ARRAY,
  beneficiarios_descripcion text,
  requisitos_beneficiarios text,
  fecha_publicacion date,
  fecha_inicio_solicitud date,
  fecha_fin_solicitud date,
  fecha_resolucion date,
  abierto boolean NOT NULL,
  importe_total character varying,
  importe_minimo character varying,
  importe_maximo character varying,
  porcentaje_financiacion character varying,
  forma_solicitud text,
  lugar_presentacion text,
  tramite_electronico boolean,
  url_tramite text,
  documentos jsonb,
  tiene_pdf boolean,
  pdf_url text,
  pdf_nombre character varying,
  pdf_id_documento character varying,
  pdf_hash character varying,
  bases_reguladoras text,
  normativa jsonb,
  compatibilidades text,
  contacto jsonb,
  observaciones text,
  raw_api_response jsonb,
  fuente character varying NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT convocatorias_pkey PRIMARY KEY (id)
);
```

**Indexes**:
- Primary key on `id`
- Unique constraint on `numero_convocatoria` (implied by business logic)

**Relationships**:
- Referenced by `staging_items.convocatoria_id`
- Referenced by `pdf_extractions.convocatoria_id`

---

## Table: `staging_items`

Tracks each grant through the ingestion pipeline.

```sql
CREATE TABLE public.staging_items (
  id integer NOT NULL DEFAULT nextval('staging_items_id_seq'::regclass),
  numero_convocatoria character varying NOT NULL,
  status USER-DEFINED NOT NULL,  -- ENUM: pending, processing, completed, failed, skipped
  batch_id character varying,
  retry_count integer NOT NULL,
  error_message text,
  last_stage character varying,  -- 'fetcher', 'processor', 'embedder'
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  completed_at timestamp with time zone,
  pdf_url text,
  pdf_hash character varying,
  convocatoria_id integer,
  CONSTRAINT staging_items_pkey PRIMARY KEY (id),
  CONSTRAINT staging_items_convocatoria_id_fkey FOREIGN KEY (convocatoria_id) REFERENCES public.convocatorias(id)
);
```

**Indexes**:
- Primary key on `id`
- Unique constraint on `numero_convocatoria` (implied)
- Index on `status`
- Index on `batch_id`
- Index on `convocatoria_id`

**Relationships**:
- Foreign key `convocatoria_id` → `convocatorias.id`
- Referenced by `pdf_extractions.staging_id`

**Status Enum Values**:
- `pending` - Fetched from API, not yet processed
- `processing` - Currently being processed
- `completed` - Successfully processed (PDF + embedding)
- `failed` - Failed after max retries
- `skipped` - Skipped (duplicate or no PDF)

---

## Table: `pdf_extractions`

Stores structured data extracted from PDFs using LLM (Gemini).

```sql
CREATE TABLE public.pdf_extractions (
  id integer NOT NULL DEFAULT nextval('pdf_extractions_id_seq'::regclass),

  -- Foreign Keys
  convocatoria_id integer NOT NULL,
  staging_id integer UNIQUE,

  -- Basic Info
  numero_convocatoria character varying NOT NULL,

  -- Extracted Text (for embeddings)
  extracted_text text,
  extracted_summary text,
  summary_preview character varying,
  titulo character varying,
  organismo character varying,
  ambito_geografico character varying,

  -- Beneficiary Info (for nominative grants)
  beneficiario_nombre character varying,  -- Specific beneficiary name
  beneficiario_cif character varying,  -- Tax ID (CIF/NIF)
  proyecto_nombre character varying,  -- Specific project/activity name

  -- Financial Details
  gastos_subvencionables text,
  cuantia_subvencion character varying,
  cuantia_min double precision,
  cuantia_max double precision,
  intensidad_ayuda character varying,
  compatibilidad_otras_ayudas text,

  -- Deadlines & Execution
  plazo_ejecucion text,
  plazo_justificacion text,
  fecha_inicio_ejecucion date,
  fecha_fin_ejecucion date,
  plazo_resolucion character varying,

  -- Justification Requirements
  forma_justificacion text,
  documentacion_requerida jsonb,
  sistema_evaluacion text,

  -- Payment & Guarantees
  forma_pago text,
  pago_anticipado character varying,
  garantias text,
  exige_aval character varying,

  -- Obligations & Conditions
  obligaciones_beneficiario text,
  publicidad_requerida text,
  subcontratacion text,
  modificaciones_permitidas text,

  -- Specific Requirements
  requisitos_tecnicos text,
  criterios_valoracion jsonb,
  documentos_fase_solicitud jsonb,

  -- Raw Extractions (for debugging)
  raw_gastos_subvencionables text,
  raw_forma_justificacion text,
  raw_plazo_ejecucion text,
  raw_plazo_justificacion text,
  raw_forma_pago text,
  raw_compatibilidad text,
  raw_publicidad text,
  raw_garantias text,
  raw_subcontratacion text,

  -- Extraction Metadata
  extraction_model character varying NOT NULL,
  extraction_confidence double precision,
  extraction_error text,
  markdown_path character varying,
  pdf_page_count integer,
  pdf_word_count integer,

  -- Timestamps
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),

  CONSTRAINT pdf_extractions_pkey PRIMARY KEY (id),
  CONSTRAINT pdf_extractions_convocatoria_id_fkey FOREIGN KEY (convocatoria_id) REFERENCES public.convocatorias(id),
  CONSTRAINT pdf_extractions_staging_id_fkey FOREIGN KEY (staging_id) REFERENCES public.staging_items(id)
);
```

**Indexes**:
- Primary key on `id`
- Unique constraint on `convocatoria_id` (one extraction per grant)
- Unique constraint on `staging_id` (one extraction per staging item)
- Index on `numero_convocatoria`

**Relationships**:
- Foreign key `convocatoria_id` → `convocatorias.id`
- Foreign key `staging_id` → `staging_items.id`
- Referenced by `embeddings.extraction_id`

**Important Notes**:
- Has **both** `convocatoria_id` and `staging_id` foreign keys
- `convocatoria_id` (NOT NULL) - Direct link for fast queries and API compatibility
- `staging_id` (nullable) - Pipeline tracking, may be NULL for legacy data
- This dual-FK design allows both direct convocatoria lookups and pipeline tracking

---

## Table: `embeddings`

Stores vector embeddings for semantic search using pgvector.

```sql
CREATE TABLE public.embeddings (
  id integer NOT NULL DEFAULT nextval('embeddings_id_seq'::regclass),
  extraction_id integer NOT NULL UNIQUE,
  embedding_vector vector(768) NOT NULL,  -- pgvector type
  model_name character varying NOT NULL DEFAULT 'text-embedding-004'::character varying,
  embedding_dimensions integer NOT NULL DEFAULT 768,
  text_length integer,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT embeddings_pkey PRIMARY KEY (id),
  CONSTRAINT embeddings_extraction_id_fkey FOREIGN KEY (extraction_id) REFERENCES public.pdf_extractions(id)
);
```

**Indexes**:
- Primary key on `id`
- Unique constraint on `extraction_id` (one embedding per extraction)
- HNSW index on `embedding_vector` for fast cosine similarity search:
  ```sql
  CREATE INDEX idx_embeddings_vector_new
  ON embeddings USING hnsw (embedding_vector vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
  ```

**Relationships**:
- Foreign key `extraction_id` → `pdf_extractions.id`

**Vector Search**:
- Uses pgvector extension
- 768-dimensional vectors from Gemini text-embedding-004
- Cosine similarity search via `<=>` operator
- HNSW index for fast approximate nearest neighbor search

---

## Relationships Diagram

```
convocatorias (1) ←--→ (1) staging_items
      ↑                        ↓
      |                        | (1)
      |                        ↓
      └────────────→ pdf_extractions (1)
                            ↓
                            | (1)
                            ↓
                        embeddings
```

**Pipeline Flow**:
1. **Fetcher**: Creates `convocatoria` + `staging_item`
2. **PDF Processor**: Creates `pdf_extraction` (links to `staging_id`)
3. **LLM Processor**: Updates `pdf_extraction` with extracted fields
4. **Embedder**: Creates `embedding` (links to `extraction_id`)

---

## Data Types

### Custom Types

**ProcessingStatus** (ENUM):
- `pending`
- `processing`
- `completed`
- `failed`
- `skipped`

**vector(768)** (pgvector):
- 768-dimensional float vector
- Stored as binary for efficiency
- Supports cosine similarity operations

---

## Key Constraints & Indexes

### Unique Constraints
- `convocatorias.numero_convocatoria` (unique, implied)
- `staging_items.numero_convocatoria` (unique)
- `pdf_extractions.convocatoria_id` (unique)
- `pdf_extractions.staging_id` (unique)
- `embeddings.extraction_id` (unique)

### Foreign Keys
- `staging_items.convocatoria_id` → `convocatorias.id`
- `pdf_extractions.convocatoria_id` → `convocatorias.id`
- `pdf_extractions.staging_id` → `staging_items.id`
- `embeddings.extraction_id` → `pdf_extractions.id`

### Performance Indexes
- `idx_embeddings_vector_new` - HNSW on `embeddings.embedding_vector`
- Index on `staging_items.status`
- Index on `staging_items.batch_id`
- Index on `pdf_extractions.numero_convocatoria`

---

## Migration Notes

### Recent Changes (2025-12-02)

1. **Added to `staging_items`**:
   - `convocatoria_id` (FK to convocatorias)

2. **Added to `pdf_extractions`**:
   - `staging_id` (FK to staging_items)
   - `extracted_text` (full PDF text)
   - `extracted_summary` (LLM summary)
   - `summary_preview` (first 500 chars)
   - `titulo` (grant title from PDF)
   - `organismo` (organization from PDF)
   - `ambito_geografico` (geographic scope from PDF)
   - `beneficiario_nombre` (VARCHAR 500) - Specific beneficiary name for nominative grants
   - `beneficiario_cif` (VARCHAR 20) - Tax ID (CIF/NIF) for searchability
   - `proyecto_nombre` (VARCHAR 500) - Specific project/activity name

3. **Added to `embeddings`**:
   - `extraction_id` (FK to pdf_extractions, replacing old convocatoria_id)
   - `embedding_vector` (renamed from `embedding`, 768 dims)
   - `model_name` (Gemini model name)
   - `text_length` (length of embedded text)

4. **Index Updates**:
   - New HNSW index on `embeddings.embedding_vector` (replaces old index on `embedding`)

### Applied via
- `scripts/update_embedding_schema.py` (automated)
- `scripts/migrate_add_beneficiary_fields.py` (beneficiary fields)
- Manual backfills for `staging_items.convocatoria_id`

---

## Future Schema Changes

When adding new fields, update this document FIRST, then update the models to match.

**Procedure**:
1. Update this document with the new schema
2. Create migration script in `scripts/migrate_*.py`
3. Update SQLAlchemy models to match
4. Run migration on database
5. Update Sprint Plan with changes

---

**End of Schema Reference**
