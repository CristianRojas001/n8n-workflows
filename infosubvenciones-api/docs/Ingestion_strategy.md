Ingestion Strategy - InfoSubvenciones RAG System
Project: InfoSubvenciones API Ingestion Pipeline Date: 2025-11-30 Scope: 136,920 convocatorias (Cultura + Comercio, PYMES/Autónomos, currently open)

Executive Summary
This document defines the complete architecture and implementation strategy for ingesting, processing, and storing Spanish government grant data (subvenciones) for semantic search via RAG.

Core Flow:

Fetch convocatoria metadata from API → Save to PostgreSQL
Download associated PDFs → Convert to Markdown
LLM processing (Gemini 2.0 Flash): Generate Spanish summary + Extract PDF-only fields
Embed summaries (OpenAI) → Store vectors + metadata in PostgreSQL (pgvector)
Enable ARTISTING to query via semantic search
Key Characteristics:

Standalone system (independent from ARTISTING Django app)
Batch processing with Celery + Redis
Resilient: Individual item tracking, retry logic, failure recovery
Scalable: Handles 136k+ items efficiently
Cost-effective: ~$5-10 total processing cost
Table of Contents
System Architecture
Data Flow
Database Schema
API Endpoints
Technology Stack
Project Structure
Processing Pipeline
Error Handling & Recovery
Cost & Performance Estimates
Environment Setup
Implementation Phases
Testing Strategy
Monitoring & Observability
System Architecture
┌─────────────────────────────────────────────────────────────────┐
│                     INGESTION PIPELINE (Standalone)              │
│                                                                  │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │   Fetcher    │ ───> │  Processor   │ ───> │   Embedder   │  │
│  │  (Celery)    │      │   (Celery)   │      │   (Celery)   │  │
│  └──────────────┘      └──────────────┘      └──────────────┘  │
│         │                      │                      │          │
│         ↓                      ↓                      ↓          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          PostgreSQL (pgvector enabled)                    │  │
│  │  - staging_items (tracking)                              │  │
│  │  - convocatorias (metadata + API fields)                 │  │
│  │  - pdf_extractions (PDF-only fields)                     │  │
│  │  - embeddings (vectors + summaries)                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────┐      ┌──────────────┐                        │
│  │    Redis     │      │  File Store  │                        │
│  │  (Broker)    │      │ (PDFs/MD)    │                        │
│  └──────────────┘      └──────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Reads from DB
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    ARTISTING (Django App)                        │
│  - Queries embeddings table via pgvector similarity search      │
│  - Retrieves metadata from convocatorias + pdf_extractions      │
│  - Downloads PDFs on-demand for detailed viewing                │
└─────────────────────────────────────────────────────────────────┘
Data Flow
Phase 1: API Ingestion
API Call → Parse Response → Deduplicate (hash) → Insert to staging_items
                                                          ↓
                                              Insert to convocatorias
                                                          ↓
                                              Queue PDF processing
Phase 2: PDF Processing
Download PDF → Calculate hash → Check duplicate → Convert to Markdown
                                                          ↓
                                                  Gemini 2.0 Flash
                                                  ├─> Summary (200-250 words, Spanish)
                                                  └─> Extract PDF fields (structured)
                                                          ↓
                                              Insert to pdf_extractions
                                                          ↓
                                              Queue embedding
Phase 3: Embedding
Summary text → OpenAI text-embedding-3-small → Vector (1536 dimensions)
                                                          ↓
                                    Insert to embeddings (with metadata)
                                                          ↓
                                              Mark staging_item as completed
Database Schema
PostgreSQL Setup
Prerequisites:

PostgreSQL 15+
pgvector extension
Installation (if not already installed):

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
Tables
1. staging_items (Processing Tracker)
CREATE TABLE staging_items (
    id SERIAL PRIMARY KEY,
    numero_convocatoria VARCHAR(50) UNIQUE NOT NULL,
    convocatoria_id INTEGER,  -- FK to convocatorias after insert

    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
        -- Values: 'pending', 'fetching', 'processing_pdf', 'embedding', 'completed', 'failed'

    -- Processing metadata
    pdf_hash VARCHAR(64),  -- SHA256 of PDF content
    pdf_url TEXT,
    pdf_local_path TEXT,
    markdown_path TEXT,

    -- Error tracking
    error_type VARCHAR(50),
        -- Values: 'api_error', 'pdf_download_failed', 'pdf_conversion_failed',
        --         'llm_failed', 'embedding_failed', 'db_error'
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_attempt TIMESTAMP,
    completed_at TIMESTAMP,

    -- Metadata
    finalidad INTEGER,  -- 11 or 14
    batch_id VARCHAR(50),  -- For grouping ingestion runs

    INDEX idx_status (status),
    INDEX idx_numero_convocatoria (numero_convocatoria),
    INDEX idx_batch_id (batch_id)
);
2. convocatorias (API Metadata)
CREATE TABLE convocatorias (
    id SERIAL PRIMARY KEY,

    -- API Direct Fields (from api_fields_complete_classification.md)
    numero_convocatoria VARCHAR(50) UNIQUE NOT NULL,
    api_id INTEGER,  -- Original API id
    codigo_bdns VARCHAR(50),

    -- Descripción
    descripcion TEXT,
    descripcion_leng TEXT,

    -- Organismo (3 niveles jerárquicos)
    organo_nivel1 VARCHAR(255),  -- ESTADO, ANDALUCÍA, etc.
    organo_nivel2 VARCHAR(255),  -- Ministerio/Consejería
    organo_nivel3 VARCHAR(255),  -- Dirección General

    -- Tipo y clasificación
    finalidad_descripcion TEXT,
    tipo_convocatoria VARCHAR(100),

    -- Fechas
    fecha_recepcion DATE,
    fecha_inicio_solicitud DATE,
    fecha_fin_solicitud DATE,
    text_inicio TEXT,
    text_fin TEXT,
    abierto BOOLEAN,

    -- Económico
    presupuesto_total DECIMAL(15,2),

    -- URLs y documentación
    sede_electronica TEXT,
    descripcion_bases_reguladoras TEXT,
    url_bases_reguladoras TEXT,
    ayuda_estado VARCHAR(100),
    url_ayuda_estado TEXT,

    -- Metadatos técnicos
    se_publica_diario_oficial BOOLEAN,
    mrr BOOLEAN,
    reglamento TEXT,
    codigo_invente VARCHAR(50),
    advertencia TEXT,

    -- Arrays almacenados como JSON
    sectores JSONB,  -- [{"codigo": "R", "descripcion": "Actividades artísticas..."}]
    tipos_beneficiarios JSONB,  -- [{"descripcion": "Pequeñas y medianas empresas"}]
    regiones JSONB,  -- [{"descripcion": "ES300 - Madrid"}]
    fondos JSONB,  -- [{"descripcion": "FEDER"}]
    objetivos JSONB,  -- [{"descripcion": "..."}]
    instrumentos JSONB,  -- [{"descripcion": "Subvención"}]
    documentos JSONB,  -- [{"id": 123, "nombreFic": "...", "long": 12345, ...}]
    anuncios JSONB,
    sectores_productos JSONB,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_numero_convocatoria (numero_convocatoria),
    INDEX idx_abierto (abierto),
    INDEX idx_organo_nivel1 (organo_nivel1),
    INDEX idx_fecha_fin_solicitud (fecha_fin_solicitud),
    INDEX idx_sectores_gin (sectores) USING GIN,
    INDEX idx_tipos_beneficiarios_gin (tipos_beneficiarios) USING GIN,
    INDEX idx_regiones_gin (regiones) USING GIN
);
3. pdf_extractions (PDF-Only Fields)
CREATE TABLE pdf_extractions (
    id SERIAL PRIMARY KEY,
    convocatoria_id INTEGER NOT NULL REFERENCES convocatorias(id) ON DELETE CASCADE,

    -- Campos críticos (solo en PDF)
    gastos_subvencionables TEXT,  -- Lista detallada
    actividades_elegibles TEXT,
    garantias_requeridas TEXT,
    compatibilidad_otras_ayudas TEXT,
    reglas_subcontratacion TEXT,

    -- Plazos (diferentes de plazos de solicitud)
    plazo_ejecucion_proyecto TEXT,
    plazo_justificacion TEXT,

    -- Procedimiento
    forma_pago TEXT,
    forma_justificacion TEXT,
    requisitos_publicidad TEXT,
    modificaciones_permitidas TEXT,

    -- Información económica adicional
    cuantia_individual TEXT,  -- En resoluciones
    presupuesto_min_proyecto DECIMAL(15,2),
    presupuesto_max_proyecto DECIMAL(15,2),
    aplicacion_presupuestaria VARCHAR(50),

    -- Administrativa
    beneficiario_especifico TEXT,  -- Nombre + CIF (en resoluciones)
    csv_verificacion VARCHAR(100),
    firmantes TEXT,
    finalidad_detallada TEXT,

    -- Metadata
    original_language VARCHAR(10),  -- 'es', 'ca', 'eu', 'gl'
    extraction_confidence DECIMAL(3,2),  -- 0.0-1.0

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_convocatoria_id (convocatoria_id)
);
4. embeddings (Vectors + Summaries)
CREATE TABLE embeddings (
    id SERIAL PRIMARY KEY,
    convocatoria_id INTEGER NOT NULL REFERENCES convocatorias(id) ON DELETE CASCADE,

    -- Summary
    summary_text TEXT NOT NULL,  -- 200-250 words in Spanish
    summary_language VARCHAR(10) DEFAULT 'es',

    -- Vector
    embedding vector(1536) NOT NULL,  -- OpenAI text-embedding-3-small dimension

    -- Combined metadata for search context (denormalized for speed)
    metadata JSONB,
    /* Example structure:
    {
        "numero_convocatoria": "871838",
        "descripcion": "...",
        "organo_nivel1": "ESTADO",
        "organo_nivel2": "MINISTERIO DE CULTURA",
        "sectores": ["R - Actividades artísticas"],
        "tipos_beneficiarios": ["PYMES"],
        "regiones": ["ES300 - Madrid"],
        "presupuesto_total": 50000.00,
        "fecha_fin_solicitud": "2025-12-31",
        "abierto": true,
        "pdf_url": "https://...",
        "sede_electronica": "https://..."
    }
    */

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_convocatoria_id (convocatoria_id),
    INDEX idx_metadata_gin (metadata) USING GIN
);

-- Create vector similarity search index (HNSW for speed)
CREATE INDEX ON embeddings USING hnsw (embedding vector_cosine_ops);
API Endpoints
Base URL: https://www.infosubvenciones.es/bdnstrans/api

1. Search Convocatorias (Paginated)
Finalidad 11 (Cultura):

GET /convocatorias/busqueda?abierto=true&finalidad=11&tiposBeneficiario=3,2&page={page}&size=100
Finalidad 14 (Comercio):

GET /convocatorias/busqueda?abierto=true&finalidad=14&tiposBeneficiario=3,2&page={page}&size=100
Response Structure:

{
  "content": [
    {
      "id": 1073399,
      "numeroConvocatoria": "871838",
      "descripcion": "...",
      "nivel1": "ESTADO",
      "nivel2": "MINISTERIO DE CULTURA",
      "nivel3": "DIRECCIÓN GENERAL...",
      "fechaRecepcion": "2025-11-28",
      "mrr": false,
      "codigoInvente": null
    }
  ],
  "totalElements": 105139,
  "totalPages": 1052,
  "size": 100,
  "number": 0
}
Parameters:

abierto: true (only open convocatorias)
finalidad: 11 (Cultura) or 14 (Comercio)
tiposBeneficiario: 3,2 (PYMES y autónomos)
page: 0-indexed page number
size: Items per page (max tested: 100, can try up to 500)
Total Scope:

Finalidad 11: 105,139 convocatorias
Finalidad 14: 31,781 convocatorias
Total: 136,920 convocatorias
2. Get Convocatoria Detail
GET /convocatorias?numConv={numeroConvocatoria}
Response: Full metadata object with all fields from api_fields_complete_classification.md

Example fields:

{
  "id": 1073399,
  "numeroConvocatoria": "871838",
  "descripcion": "...",
  "descripcionLeng": null,
  "codigoBDNS": "...",
  "organo": {
    "nivel1": "ESTADO",
    "nivel2": "MINISTERIO DE CULTURA",
    "nivel3": "DIRECCIÓN GENERAL..."
  },
  "sectores": [{"codigo": "R", "descripcion": "Actividades artísticas..."}],
  "tiposBeneficiarios": [{"descripcion": "Pequeñas y medianas empresas"}],
  "regiones": [{"descripcion": "ES300 - Madrid"}],
  "fondos": [],
  "instrumentos": [{"descripcion": "Subvención"}],
  "objetivos": [],
  "presupuestoTotal": 50000.00,
  "fechaInicioSolicitud": "2025-01-01",
  "fechaFinSolicitud": "2025-12-31",
  "abierto": true,
  "documentos": [
    {
      "id": 12345,
      "descripcion": "Convocatoria",
      "nombreFic": "documento.pdf",
      "long": 123456,
      "datMod": "2025-11-28",
      "datPublicacion": "2025-11-28"
    }
  ],
  "sedeElectronica": "https://...",
  "urlBasesReguladoras": "https://...",
  ...
}
3. Download PDF Document
GET /convocatorias/documentos?idDocumento={idDocumento}
Returns: Binary PDF file

Alternative (Generated full PDF):

GET /convocatorias/pdf?id={idConvocatoria}&vpd=GE
Technology Stack
Core Technologies
Python: 3.11+
PostgreSQL: 15+ with pgvector extension
Redis: 7+ (Celery broker)
Celery: 5+ (distributed task queue)
Libraries
PDF Processing:

pymupdf>=1.23.0  # Fast PDF to text/markdown
marker-pdf>=0.2.0  # Fallback for complex PDFs
LLM & Embeddings:

google-generativeai>=0.3.0  # Gemini 2.0 Flash
openai>=1.0.0  # Embeddings
Database:

psycopg2-binary>=2.9.0
pgvector>=0.2.0
sqlalchemy>=2.0.0
alembic>=1.12.0  # Migrations
Task Queue:

celery>=5.3.0
redis>=5.0.0
Utilities:

requests>=2.31.0
python-dotenv>=1.0.0
pydantic>=2.0.0  # Data validation
tenacity>=8.2.0  # Retry logic
Development:

pytest>=7.4.0
pytest-cov>=4.1.0
black>=23.0.0
ruff>=0.1.0
Project Structure
infosubvenciones-api/
├── Ingestion/                          # NEW standalone ingestion system
│   ├── README.md                       # Quick start guide
│   ├── requirements.txt                # Python dependencies
│   ├── .env.example                    # Environment template
│   ├── .env                           # Local config (gitignored)
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py                # Central configuration
│   │   ├── database.py                # SQLAlchemy setup
│   │   └── celery_app.py              # Celery configuration
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── staging.py                 # StagingItem model
│   │   ├── convocatoria.py            # Convocatoria model
│   │   ├── pdf_extraction.py          # PDFExtraction model
│   │   └── embedding.py               # Embedding model
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── api_response.py            # Pydantic models for API
│   │   ├── pdf_fields.py              # PDF extraction schema
│   │   └── metadata.py                # Embedding metadata schema
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── api_client.py              # InfoSubvenciones API client
│   │   ├── pdf_processor.py           # PDF download & conversion
│   │   ├── llm_service.py             # Gemini integration
│   │   ├── embedding_service.py       # OpenAI embeddings
│   │   └── deduplication.py           # Hash checking
│   │
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── fetcher.py                 # Celery: Fetch from API
│   │   ├── processor.py               # Celery: Process PDFs
│   │   ├── embedder.py                # Celery: Generate embeddings
│   │   └── retry_handler.py           # Celery: Retry failed items
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logging_config.py          # Structured logging
│   │   ├── hash_utils.py              # SHA256 hashing
│   │   ├── retry_utils.py             # Exponential backoff
│   │   └── validators.py              # Data validation
│   │
│   ├── scripts/
│   │   ├── init_db.py                 # Create database schema
│   │   ├── run_ingestion.py           # Main orchestrator
│   │   ├── test_pipeline.py           # Test with N items
│   │   ├── retry_failed.py            # Manually retry failed items
│   │   └── export_stats.py            # Progress reporting
│   │
│   ├── migrations/                     # Alembic migrations
│   │   ├── env.py
│   │   └── versions/
│   │
│   ├── data/                          # Local file storage
│   │   ├── pdfs/                      # Downloaded PDFs
│   │   └── markdown/                  # Converted markdown
│   │
│   └── tests/
│       ├── __init__.py
│       ├── test_api_client.py
│       ├── test_pdf_processor.py
│       ├── test_llm_service.py
│       ├── test_embedding_service.py
│       └── test_end_to_end.py
│
├── docs/
│   ├── ingestion_strategy.md          # THIS FILE
│   └── ...
│
└── info/
    ├── api_fields_complete_classification.md
    ├── customer_needs.md
    └── ...
Processing Pipeline
Task Definitions
Task 1: fetch_convocatorias (Celery Task)
Input: finalidad (11 or 14), batch_id

Process:

Call API with pagination: /convocatorias/busqueda?abierto=true&finalidad={finalidad}&tiposBeneficiario=3,2&page={page}&size=100
For each item in response:
Check if numero_convocatoria exists in staging_items → Skip if exists
Insert into staging_items (status='pending')
Call API detail: /convocatorias?numConv={numeroConvocatoria}
Insert into convocatorias table
Extract PDF URLs from documentos array
Queue process_pdf task for each PDF
Continue pagination until page >= totalPages
Error Handling:

API timeout: Retry with exponential backoff (max 3 attempts)
429 Rate Limit: Wait 60s, retry
5xx errors: Retry
4xx errors (except 429): Log and skip
Output: Number of new items queued

Task 2: process_pdf (Celery Task)
Input: staging_item_id, pdf_document (from API response)

Process:

Update status: staging_items.status = 'processing_pdf'

Download PDF:

GET /convocatorias/documentos?idDocumento={pdf_document.id}
Save to data/pdfs/{numero_convocatoria}_{doc_id}.pdf
Calculate hash: SHA256 of PDF bytes

Check duplicate:

Query: SELECT id FROM staging_items WHERE pdf_hash = {hash} AND status = 'completed'
If exists → Copy embeddings, mark completed, skip processing
Convert to Markdown:

Try pymupdf (fast): fitz.open() → page.get_text("markdown")
If fails → Try marker-pdf (robust)
If both fail → Mark as error_type='pdf_conversion_failed', queue retry
Save to data/markdown/{numero_convocatoria}_{doc_id}.md
LLM Processing (Gemini 2.0 Flash):

Prompt Template:

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
Schema (from schemas/pdf_fields.py):

{
  "gastos_subvencionables": str | null,
  "actividades_elegibles": str | null,
  "garantias_requeridas": str | null,
  "compatibilidad_otras_ayudas": str | null,
  "reglas_subcontratacion": str | null,
  "plazo_ejecucion_proyecto": str | null,
  "plazo_justificacion": str | null,
  "forma_pago": str | null,
  "forma_justificacion": str | null,
  "requisitos_publicidad": str | null,
  "modificaciones_permitidas": str | null,
  "cuantia_individual": str | null,
  "presupuesto_min_proyecto": float | null,
  "presupuesto_max_proyecto": float | null,
  "aplicacion_presupuestaria": str | null,
  "beneficiario_especifico": str | null,
  "csv_verificacion": str | null,
  "firmantes": str | null,
  "finalidad_detallada": str | null,
  "original_language": str  # 'es', 'ca', 'eu', 'gl'
}
Response Parsing:

Extract summary text
Parse JSON fields
Validate with Pydantic schema
Save to DB:

Insert into pdf_extractions (all extracted fields)
Update staging_items: markdown_path, pdf_local_path, pdf_hash
Queue embedding: Call generate_embedding task

Error Handling:

Download fails: Retry (max 3), mark error_type='pdf_download_failed'
Conversion fails: Try fallback converter, then mark error_type='pdf_conversion_failed'
LLM fails: Retry with smaller chunk if > token limit, mark error_type='llm_failed'
Rate limit (Gemini): Wait 60s, retry
Output: pdf_extraction_id

Task 3: generate_embedding (Celery Task)
Input: staging_item_id, summary_text

Process:

Update status: staging_items.status = 'embedding'
Call OpenAI:
response = openai.embeddings.create(
    model="text-embedding-3-small",
    input=summary_text,
    encoding_format="float"
)
vector = response.data[0].embedding  # 1536 dimensions
Build metadata JSON:
Join convocatorias + pdf_extractions
Extract key fields for search context
metadata = {
    "numero_convocatoria": convocatoria.numero_convocatoria,
    "descripcion": convocatoria.descripcion,
    "organo_nivel1": convocatoria.organo_nivel1,
    "organo_nivel2": convocatoria.organo_nivel2,
    "sectores": [s["descripcion"] for s in convocatoria.sectores],
    "tipos_beneficiarios": [t["descripcion"] for t in convocatoria.tipos_beneficiarios],
    "regiones": [r["descripcion"] for r in convocatoria.regiones],
    "presupuesto_total": float(convocatoria.presupuesto_total),
    "fecha_fin_solicitud": convocatoria.fecha_fin_solicitud.isoformat(),
    "abierto": convocatoria.abierto,
    "pdf_url": pdf_url,
    "sede_electronica": convocatoria.sede_electronica
}
Insert to DB:
INSERT INTO embeddings (
    convocatoria_id,
    summary_text,
    embedding,
    metadata
) VALUES (?, ?, ?, ?)
Mark complete:
UPDATE staging_items
SET status = 'completed', completed_at = NOW()
WHERE id = ?
Error Handling:

Embedding API fails: Retry (max 3), mark error_type='embedding_failed'
Rate limit: Batch embeddings if possible, wait and retry
Output: embedding_id

Task 4: retry_failed_items (Scheduled Celery Beat)
Schedule: Every 30 minutes

Process:

Query:
SELECT * FROM staging_items
WHERE status = 'failed'
  AND retry_count < max_retries
  AND (last_attempt IS NULL OR last_attempt < NOW() - INTERVAL '5 minutes')
ORDER BY retry_count ASC, last_attempt ASC
LIMIT 100
For each item:
Increment retry_count
Reset status to 'pending'
Re-queue appropriate task based on error_type:
api_error, pdf_download_failed → process_pdf
pdf_conversion_failed → process_pdf (tries fallback)
llm_failed → process_pdf
embedding_failed → generate_embedding
Exponential Backoff:

Retry 1: Immediate
Retry 2: Wait 5 minutes
Retry 3: Wait 30 minutes
Error Handling & Recovery
Error Categories
Error Type	Cause	Recovery Strategy	Max Retries
api_error	InfoSubvenciones API down/timeout	Exponential backoff, retry	3
pdf_download_failed	PDF URL broken, network issue	Retry different endpoint, wait	3
pdf_conversion_failed	Corrupted PDF, unsupported format	Try fallback converter (marker)	2
llm_failed	Gemini rate limit, token limit	Wait, reduce chunk size	3
embedding_failed	OpenAI rate limit, network	Wait, batch process	3
db_error	Constraint violation, connection	Check data integrity, retry	2
Retry Logic
Implementation (using tenacity):

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError))
)
def download_pdf(url):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.content
Manual Recovery
Script: scripts/retry_failed.py

Usage:

# Retry all failed items
python scripts/retry_failed.py --all

# Retry specific error type
python scripts/retry_failed.py --error-type pdf_conversion_failed

# Retry specific batch
python scripts/retry_failed.py --batch-id batch_2025_11_30

# Reset retry counter (force retry even if max reached)
python scripts/retry_failed.py --reset-retries --error-type llm_failed
Data Integrity Checks
Pre-flight checks (in scripts/init_db.py):

PostgreSQL version >= 15
pgvector extension installed
Redis connection alive
Required environment variables set
Disk space available (estimate 50GB for 136k PDFs)
Post-processing validation:

-- Check for orphaned records
SELECT COUNT(*) FROM pdf_extractions
WHERE convocatoria_id NOT IN (SELECT id FROM convocatorias);

-- Check for missing embeddings
SELECT COUNT(*) FROM convocatorias c
LEFT JOIN embeddings e ON c.id = e.convocatoria_id
WHERE e.id IS NULL AND EXISTS (
    SELECT 1 FROM staging_items WHERE convocatoria_id = c.id AND status = 'completed'
);

-- Check for stuck items (processing > 1 hour)
SELECT * FROM staging_items
WHERE status IN ('processing_pdf', 'embedding')
  AND last_attempt < NOW() - INTERVAL '1 hour';
Cost & Performance Estimates
Volume
Total convocatorias: 136,920
Average PDFs per convocatoria: 1.5 (estimate)
Total PDFs to process: ~205,000
LLM Costs (Gemini 2.0 Flash)
Pricing (as of 2025):

Input: $0.075 per 1M tokens
Output: $0.30 per 1M tokens
Estimate per PDF:

Input (markdown): ~3,000 tokens
Output (summary + fields): ~400 tokens
Total:

Input: 205,000 × 3,000 = 615M tokens → $46.13
Output: 205,000 × 400 = 82M tokens → $24.60
Gemini Total: ~$70.73
Free Tier: Gemini 2.0 Flash has generous free tier (~2M tokens/min). May be able to process significant portion for free if spread over time.

Embedding Costs (OpenAI)
Pricing:

text-embedding-3-small: $0.02 per 1M tokens
Estimate per summary:

Summary: ~300 tokens
Total:

205,000 × 300 = 61.5M tokens → $1.23
Infrastructure
Redis: Free (self-hosted or Redis Cloud free tier) PostgreSQL: Free (self-hosted or Supabase free tier up to 500MB) Storage: ~50GB for PDFs + markdown (S3: ~$1.15/month)

Total Estimated Cost: ~$72-75 (one-time processing)
Time Estimates
With optimized batching:

Task	Rate Limit	Throughput	Time for 205k
API fetching	No limit	1000/min	~3.5 hours
PDF download	Network bound	500/min	~7 hours
PDF conversion	CPU bound	300/min	~11.5 hours
Gemini processing	2M tokens/min	~666/min	~5 hours
OpenAI embedding	3M tokens/min	~10k/min	~20 min
Critical path: PDF conversion (11.5 hours if sequential)

With parallelization (10 Celery workers):

PDF conversion: ~1.2 hours
Total pipeline: ~3-4 hours (for full 205k PDFs)
For testing batches:

10 items: ~2 minutes
100 items: ~15 minutes
1,000 items: ~2 hours
Environment Setup
Prerequisites
PostgreSQL 15+ with pgvector
Redis 7+
Python 3.11+
Installation
1. PostgreSQL + pgvector
Ubuntu/Debian:

# Install PostgreSQL
sudo apt update
sudo apt install postgresql-15 postgresql-contrib-15

# Install pgvector
sudo apt install postgresql-15-pgvector

# Or compile from source:
cd /tmp
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
macOS (Homebrew):

brew install postgresql@15
brew install pgvector
Docker (easiest):

docker run -d \
  --name infosubvenciones-db \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=infosubvenciones \
  -p 5432:5432 \
  -v pgdata:/var/lib/postgresql/data \
  ankane/pgvector:latest
Enable pgvector:

psql -U postgres -d infosubvenciones
CREATE EXTENSION vector;
2. Redis
Ubuntu/Debian:

sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
macOS:

brew install redis
brew services start redis
Docker:

docker run -d \
  --name infosubvenciones-redis \
  -p 6379:6379 \
  redis:7-alpine
3. Python Environment
cd infosubvenciones-api/Ingestion

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
Environment Variables
File: Ingestion/.env

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/infosubvenciones

# Redis (Celery Broker)
REDIS_URL=redis://localhost:6379/0

# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# InfoSubvenciones API
API_BASE_URL=https://www.infosubvenciones.es/bdnstrans/api
API_TIMEOUT=30
API_MAX_RETRIES=3

# Processing
BATCH_SIZE=100
MAX_WORKERS=10
PDF_STORAGE_PATH=./data/pdfs
MARKDOWN_STORAGE_PATH=./data/markdown

# LLM Settings
GEMINI_MODEL=gemini-2.5-flash-lite
GEMINI_TEMPERATURE=0.1
GEMINI_MAX_TOKENS=8192
SUMMARY_MIN_WORDS=200
SUMMARY_MAX_WORDS=250

# Embedding Settings
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536

# Retry Logic
MAX_RETRIES=3
RETRY_BACKOFF_MULTIPLIER=2
RETRY_MIN_WAIT=4
RETRY_MAX_WAIT=60

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/ingestion.log

# Testing
TEST_MODE=false
TEST_LIMIT=10
Database Initialization
# Create tables
python scripts/init_db.py

# Run migrations (if using Alembic)
alembic upgrade head
Celery Workers
Start workers (in separate terminals):

# Worker 1: Fetcher tasks
celery -A config.celery_app worker \
  --loglevel=info \
  --queues=fetcher \
  --concurrency=4 \
  --hostname=fetcher@%h

# Worker 2: Processor tasks (CPU intensive)
celery -A config.celery_app worker \
  --loglevel=info \
  --queues=processor \
  --concurrency=8 \
  --hostname=processor@%h

# Worker 3: Embedder tasks
celery -A config.celery_app worker \
  --loglevel=info \
  --queues=embedder \
  --concurrency=4 \
  --hostname=embedder@%h

# Celery Beat (scheduled tasks)
celery -A config.celery_app beat \
  --loglevel=info
Production (use Supervisor or systemd):

# Example systemd service
sudo nano /etc/systemd/system/celery-infosubvenciones.service
Implementation Phases
Phase 1: Foundation (Week 1)
Goals:

Set up project structure
Configure database + models
Implement API client
Basic Celery tasks (fetcher only)
Deliverables:

✅ Database schema created
✅ Can fetch convocatorias from API
✅ Data stored in convocatorias table
✅ staging_items tracking works
Test: Ingest 100 convocatorias (metadata only, no PDFs)

Phase 2: PDF Processing (Week 2)
Goals:

PDF download + conversion
Gemini integration
Field extraction
Deliverables:

✅ PDF → Markdown conversion works
✅ Gemini generates summaries (Spanish)
✅ Structured field extraction
✅ Data in pdf_extractions table
Test: Process 100 PDFs end-to-end (no embeddings)

Phase 3: Embeddings (Week 2-3)
Goals:

OpenAI embedding integration
Vector storage
Metadata assembly
Deliverables:

✅ Embeddings generated
✅ Stored in pgvector
✅ Metadata JSON correct
✅ Full pipeline works
Test: 1,000 items end-to-end, verify search works

Phase 4: Error Handling & Scale (Week 3)
Goals:

Retry logic
Monitoring
Performance optimization
Deliverables:

✅ Failed items retry automatically
✅ Dashboard/stats script
✅ Batching optimized
✅ Can handle full 136k scale
Test: Run 10k items, verify <5% failure rate

Phase 5: Production Run (Week 4)
Goals:

Process all 136,920 convocatorias
Validate data quality
Integration with ARTISTING
Deliverables:

✅ All data ingested
✅ Quality checks pass
✅ ARTISTING can query embeddings
✅ Documentation complete
Testing Strategy
Unit Tests
Coverage targets:

services/: 80%+
tasks/: 70%+
models/: 90%+
Key tests:

# tests/test_api_client.py
def test_fetch_convocatorias_pagination()
def test_handle_api_timeout()
def test_parse_response_structure()

# tests/test_pdf_processor.py
def test_download_pdf()
def test_convert_pdf_to_markdown()
def test_fallback_converter()

# tests/test_llm_service.py
def test_generate_summary()
def test_extract_fields()
def test_handle_non_spanish_content()

# tests/test_embedding_service.py
def test_generate_embedding()
def test_metadata_assembly()
Integration Tests
# tests/test_end_to_end.py
def test_full_pipeline_single_item():
    """
    1. Fetch convocatoria from API
    2. Download PDF
    3. Generate summary + extract fields
    4. Create embedding
    5. Verify all data in DB
    """
    pass

def test_duplicate_detection():
    """Process same PDF twice, verify deduplication"""
    pass

def test_retry_mechanism():
    """Simulate failure, verify retry logic"""
    pass
Test Data
Use production data samples:

# Test with 10 real items
python scripts/test_pipeline.py --limit 10 --finalidad 11

# Test specific convocatoria
python scripts/test_pipeline.py --numero-convocatoria 871838

# Test batch
python scripts/test_pipeline.py --limit 100 --batch-id test_batch_1
Validation Scripts
# scripts/validate_data.py

# Check summary quality
- Word count 200-250
- Language is Spanish
- Contains key information

# Check field extraction
- Required fields populated
- JSON schema valid
- No hallucinations (compare to PDF)

# Check embeddings
- Vector dimension = 1536
- Metadata complete
- No null vectors

# Check referential integrity
- All convocatorias have staging_items
- All completed items have embeddings
- No orphaned records
Monitoring & Observability
Metrics to Track
Progress Metrics:

-- Overall progress
SELECT
    status,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM staging_items), 2) as percentage
FROM staging_items
GROUP BY status;

-- Processing rate (items/hour)
SELECT
    DATE_TRUNC('hour', completed_at) as hour,
    COUNT(*) as completed
FROM staging_items
WHERE status = 'completed'
GROUP BY hour
ORDER BY hour DESC
LIMIT 24;

-- Error distribution
SELECT
    error_type,
    COUNT(*) as count
FROM staging_items
WHERE status = 'failed'
GROUP BY error_type
ORDER BY count DESC;

-- Retry statistics
SELECT
    retry_count,
    COUNT(*) as count
FROM staging_items
WHERE retry_count > 0
GROUP BY retry_count
ORDER BY retry_count;
Quality Metrics:

-- Summary word count distribution
SELECT
    CASE
        WHEN array_length(regexp_split_to_array(summary_text, '\s+'), 1) < 200 THEN 'too_short'
        WHEN array_length(regexp_split_to_array(summary_text, '\s+'), 1) > 250 THEN 'too_long'
        ELSE 'ok'
    END as length_category,
    COUNT(*)
FROM embeddings
GROUP BY length_category;

-- Field extraction completeness
SELECT
    COUNT(*) as total,
    COUNT(gastos_subvencionables) as has_gastos,
    COUNT(plazo_justificacion) as has_plazo,
    ROUND(100.0 * COUNT(gastos_subvencionables) / COUNT(*), 2) as gastos_pct
FROM pdf_extractions;
Logging
Structured logging (JSON format):

import structlog

logger = structlog.get_logger()

logger.info(
    "pdf_processed",
    staging_item_id=123,
    numero_convocatoria="871838",
    pdf_size_kb=456,
    conversion_time_ms=1234,
    summary_words=225,
    fields_extracted=15
)
Log levels:

DEBUG: Individual API calls, file operations
INFO: Task start/complete, milestones
WARNING: Retries, missing optional fields
ERROR: Task failures, data issues
CRITICAL: System failures, data corruption
Dashboard (Optional)
Tools:

Grafana + PostgreSQL datasource
Celery Flower (real-time task monitoring)
Key visualizations:

Processing rate (items/hour) - line chart
Status distribution - pie chart
Error types - bar chart
Queue depth - gauge
Worker utilization - heatmap
Script alternative (scripts/export_stats.py):

# Print progress report
python scripts/export_stats.py

# Example output:
# ==========================================
# Ingestion Progress Report
# ==========================================
# Total items: 136,920
# Completed: 85,432 (62.4%)
# Processing: 1,245 (0.9%)
# Failed: 3,421 (2.5%)
# Pending: 46,822 (34.2%)
#
# Estimated time remaining: 4.2 hours
# Current rate: 2,340 items/hour
# ==========================================
Appendix: Key Decisions & Rationale
Why Standalone System?
Separation of concerns: Ingestion is batch, ARTISTING is real-time
Independent scaling: Can run ingestion on powerful batch machine
Simpler debugging: Isolated from user-facing app
Flexible scheduling: Run weekly/monthly without affecting ARTISTING
Why Celery + Redis?
Compatibility: ARTISTING already uses this stack
Proven: Battle-tested for distributed task queues
Monitoring: Celery Flower provides great observability
Retry logic: Built-in, configurable
Why pymupdf + marker fallback?
Speed: pymupdf is 10x faster than alternatives
Quality: marker excels at complex layouts (tables, multi-column)
Cost: Both open-source, no API costs
Fallback: Best of both worlds
Why Gemini 2.0 Flash over GPT-4o-mini?
Cost: Free tier available, ~3x cheaper if paid
Speed: Faster response times
Quality: Comparable for summarization tasks
Rate limits: 2M tokens/min (very generous)
Why OpenAI embeddings over open-source?
Quality: Better retrieval performance than open models
Cost: $0.02/1M tokens (~$1 total) is negligible
Dimension: 1536 is standard, well-supported
Speed: Fast API, reliable
Why denormalize metadata in embeddings table?
Query speed: Avoid JOINs during vector search
Simplicity: ARTISTING gets everything in one query
Trade-off: Slightly larger storage vs. much faster reads
pgvector limitation: Can't efficiently join during similarity search
Next Steps
Once this strategy is approved:

Create project structure: Ingestion/ folder with all subfolders
Implement core modules:
config/settings.py - Load environment, validate
models/*.py - SQLAlchemy models
services/api_client.py - InfoSubvenciones client
Database setup: Run scripts/init_db.py
Test Phase 1: Fetch 100 convocatorias (metadata only)
Iterate through Phases 2-5 (see Implementation Phases)
First code to write:

Database models (models/)
API client (services/api_client.py)
Init script (scripts/init_db.py)
Ready to begin implementation when you give the go-ahead.

Document Version: 1.0 Last Updated: 2025-11-30 Author: Claude (Anthropic) Status: Ready for Review
