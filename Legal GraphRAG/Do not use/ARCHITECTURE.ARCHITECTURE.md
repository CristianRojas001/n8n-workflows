# Artisting Legal Assistant – High-Level Architecture

## 1. Overview

The Artisting Legal Assistant is a domain-specific legal system focused on:

- **Normativa**: core laws and regulations (Spain + EU)
- **Jurisprudencia**: case law (CENDOJ, TJUE, TEDH, TEAC/TEAR)
- **Doctrina administrativa / soft law**: DGT, AEAT, TGSS/INSS, ICAA, ministerial guides and FAQs

The **single source of truth** for “what we care about” is the Excel file `corpus_normativo_artisting_enriched`, which is loaded into a database table called `corpus_sources`.  
Everything else in the system is driven by this catalog.

---

## 2. Goals

- Provide **grounded, explainable answers** for cultural, fiscal, labour and IP questions.
- Respect the **hierarchy of sources**: law → admin doctrine → jurisprudence.
- Implement **phased coverage** using the `Prioridad` field (P1 / P2 / P3).
- Make sources and coverage **configurable** from the corpus catalog, not hardcoded.

---

## 3. Core Model

The catalog (`corpus_sources`) encodes each source along three main dimensions:

1. **Nature of the source**
   - `Normativa` (hard law)
   - `Jurisprudencia`
   - `Doctrina_admin`
   - `Soft_law / Guía`

2. **Domain / area**
   - Fiscal (IVA, IRPF, IS, mecenazgo, etc.)
   - Contabilidad / entities
   - Laboral / Seguridad Social / artistas
   - Propiedad intelectual / audiovisual / digital / plataformas
   - Subvenciones / cultura
   - Consumo, protección de datos, etc.

3. **Priority**
   - `P1`: core for MVP
   - `P2`: important, second wave
   - `P3`: long tail / edge cases

The catalog also contains:

- Legal form (`Tipo`), territorial scope (`Ámbito`)
- Official identifiers (`id_oficial`, `url_oficial`)
- Intended role (`Función en ARTISTING`)
- Flags for “specific instrument” vs “corpus/bucket”.

This catalog is **Layer 1** and controls ingestion, indexing and retrieval.

---

## 4. Layers and Components

### 4.1. Layer 1 – Corpus Catalog & Governance

- Table `corpus_sources` loaded from the Excel file.
- Fields include: `prioridad`, `naturaleza`, `area_principal`, `tipo`, `ambito`, `funcion_en_artisting`, `id_oficial`, `url_oficial`, `capa_modelo`, `es_corpus`, `regla_seleccion`, `estado`.
- Used by:
  - Ingestion scheduler (to decide *what* to fetch and *how*).
  - Retrieval planner (to decide *what* to query and *in what order*).

### 4.2. Layer 2 – Ingestion & Normalization

**Connectors** (per technical source):

- BOE (Spanish legislation)
- DOUE / EUR-Lex (EU law)
- CENDOJ (TS, AN, TSJ)
- DGT / PETETE (tax consultations)
- AEAT (criteria, FAQs, internal guidance)
- INSS / TGSS (bulletins, criteria)
- ICAA / Ministry of Culture (guides, criteria)
- TJUE / TEDH / TEAC / TEAR (supranational and economic-administrative bodies)

**Normalizer**:

- Converts each raw document into a canonical JSON structure:
  - `doc_id`, `source_id` (link to `corpus_sources`)
  - `capa_modelo`, `naturaleza`, `tipo`, `ambito`, `area_principal`, `prioridad`
  - Publication and validity dates
  - Structural units (articles, sections, fundamentos, contestación, etc.)

**Citation Extractor**:

- Identifies legal references inside documents:
  - Norms and articles (BOE-A / ELI + article numbers)
  - ECLI (case law)
  - DGT consultation IDs (Vxxxx-yy)
- Emits relations like:
  - CASE → NORM (CITES, INTERPRETS)
  - CONSULTA → NORM (APPLIES_CRITERION)
  - NORM → NORM (MODIFIES, DEROGATES, TRANSPONES, etc.)

### 4.3. Layer 3 – Storage & Graph

- **Document Store**: canonical JSON + plain text spans per document.
- **Metadata DB** (e.g. Postgres):
  - `docs(doc_id, source_id, capa_modelo, naturaleza, tipo, area_principal, prioridad, fechas, etc.)`
  - `doc_parts(part_id, doc_id, path, text, offsets, hashes, …)`
- **Graph Edges**:
  - `edges(from_part_id, to_part_id, relation_type, confidence, context)`  
  (e.g. `CITES`, `INTERPRETS`, `APPLIES_CRITERION`, `MODIFIES`, `TRANSPONES`).

### 4.4. Layer 4 – Indexing & Retrieval

- Three logical indexes (can be separate or unified with filters):
  - `norms_index` – normative texts (BOE, DOUE, autonómico/local)
  - `doctrine_index` – DGT, AEAT, TGSS/INSS, ICAA, guides and FAQs
  - `juris_index` – CENDOJ, TJUE, TEDH, TEAC/TEAR

Each index is **hybrid**:

- BM25 / lexical search for exact references.
- Vector search for semantic similarity.
- Optional reranker (cross-encoder or LLM).

**Query Planner**:

- Classifies the user query into:
  - `area_principal` (using labels similar to the catalog)
  - intent type (general rule vs case-specific vs subvención, etc.)
- Builds a retrieval plan based on `capa_modelo`, `prioridad`, `ambito` and date:
  - Norms P1 first, then doctrine P1, then jurisprudence P1/P2 if needed.
- Uses the graph to **expand around relevant articles**:
  - “Find cases and consultations that cite these articles.”

### 4.5. Layer 5 – Reasoning & Answer Composition

**Answer Composer**:

- Takes the retrieved spans (`norm_spans`, `doctrine_spans`, `juris_spans`) plus metadata.
- Uses an LLM to build a structured answer with this skeleton:

  1. Resumen ejecutivo
  2. Normativa aplicable (norms + articles + mini-explanation)
  3. Criterios administrativos relevantes (DGT, AEAT, SS, Cultura)
  4. Jurisprudencia relevante (si existe)
  5. Notas de alcance y límites (vigencia, ámbito, posibles cambios)

- All claims must be grounded in the retrieved text, with explicit references (artículos, ECLI, consultas).

### 4.6. Layer 6 – Evaluation & Monitoring

- Curated test questions per `area_principal` and `prioridad`.
- Metrics:
  - Retrieval quality (recall / precision against gold labels).
  - Grounding checks (is every assertion supported by cited spans?).
  - Coverage vs `Prioridad` (are P1 sources systematically used where expected?).
- Feedback loop into:
  - `corpus_sources` (add/remove sources, adjust priorities).
  - Ingestion configs (expand or narrow corpus rules).
  - Retrieval planner (tune routing decisions).

---

## 5. Data Flow Summary

1. **Legal/Product team** updates the Excel corpus → `corpus_sources`.
2. **Ingestion scheduler** reads `corpus_sources` and triggers source-specific connectors.
3. Connectors fetch raw documents → Normalizer → Citation Extractor.
4. Normalized docs and edges are stored in Document Store, Metadata DB, and Graph.
5. Indexers build / update hybrid indexes per pillar.
6. **At query time**:
   - Query Planner uses `corpus_sources` metadata to choose the right pillars and priorities.
   - Retrieval Layer performs hybrid search + graph expansion.
   - Answer Composer generates a layered, grounded legal answer.

This architecture keeps the **legal canon and priorities fully driven by the corpus Excel**, while giving engineering a clear set of layers and responsibilities to implement.  
