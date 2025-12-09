# Holistic Testing Plan (Grants Chat / RAG)

Purpose: validate end-to-end quality across ingestion, database, search UI, and RAG chat. Start with 20 PDFs from `D:\IT workspace\relevant_pdfs`, expand to 100 later. No main code changes; reuse/extend testing scripts only.

## Scope & Outcomes
- Verify DB content vs source PDFs/API (ingestion correctness, normalization).
- Verify DB content vs Search UI (relevance, filters, result coverage).
- Verify DB content vs RAG chat answers (grounded, non-hallucinated, responsive).
- Produce reusable checklists, datasets, and metrics to scale from 20 ƒÆ' 100 PDFs.

## Workstreams

1) DB vs PDF (ingestion accuracy)
- Sample 20 PDFs randomly from `D:\IT workspace\relevant_pdfs` (ensure mix: page counts, tables, scanned/OCR, multi-program docs).
- Run ingestion on the same 20 (record `numero_convocatoria`, `staging_id`, `convocatoria_id`, `pdf_hash`).
- Manually/assisted extract ground truth for fields in `field_matrix.md` into `holistic_testing/ground_truth/*.md`.
- Pull DB values from `convocatorias` + `pdf_extractions` for the same IDs; store snapshots in `holistic_testing/db_exports/*.md` or `.csv`.
- Compare field-by-field; log deltas in `holistic_testing/findings_ingestion.md`.
- Checks: field accuracy, completeness (nonnull when present in PDF), normalization (dates, numbers, arrays), summary length (200–250 words), PDF linkage (`pdf_hash`, `pdf_url`, `pdf_nombre`).
- Metrics: field-level accuracy %, completeness %, summary length distribution, schema conformance (types), PDF-to-record linkage success %.

2) DB vs Search UI (relevance + filters)
- Define a fixed query set (10–15) covering: general intent, beneficiary types, regions, sectors, deadlines, amounts, and edge cases (zero results, closed grants).
- For each query, derive expected set/order from DB (SQL on `convocatorias` + embeddings/metadata) and store in `holistic_testing/search_cases/*.md`.
- Drive UI (manual or existing Playwright tests) with same queries/filters; capture returned grant IDs/order.
- Evaluate: precision@k, recall@k, NDCG@k (if order matters), filter correctness (each filter toggled individually and in combination), zero-result correctness, latency p50/p95 (if observable).
- Log findings in `holistic_testing/findings_search.md`; flag mismatches between UI and DB expectations.

3) DB vs RAG chat (grounded QA)
- Build a question set per selected grant plus cross-grant questions (e.g., compare amounts, deadlines, eligibility). Store in `holistic_testing/chat_cases/*.md` with expected facts from DB.
- Run chat with fixed prompts; capture tool calls and responses (session IDs, timestamps). Save transcripts to `holistic_testing/chat_runs/`.
- Grade against DB: factual accuracy, citation to correct `numero_convocatoria`, hallucination rate (unsupported claims), omission rate (missed key fields), answer completeness, latency to first token/finish, tool success rate.
- Metrics: grounded accuracy %, hallucination rate %, context recall %, citation coverage %, latency p50/p95, tool success %.

## Artifacts & Folder Layout
- `holistic_testing/field_matrix.md` – canonical field list, source (API vs PDF), DB column, comparison notes.
- `holistic_testing/ground_truth/` – manual extracts for each PDF (20 now, expandable to 100).
- `holistic_testing/db_exports/` – snapshots from DB for compared records.
- `holistic_testing/search_cases/` – query/filter definitions + expected DB results.
- `holistic_testing/chat_cases/` – question sets + expected factual anchors.
- `holistic_testing/chat_runs/` – captured chat transcripts/tool traces.
- `holistic_testing/findings_ingestion.md` – discrepancies DB vs PDF.
- `holistic_testing/findings_search.md` – UI search vs DB relevance/filter issues.
- `holistic_testing/findings_chat.md` – RAG chat quality issues and metrics.
- `holistic_testing/todo.md` – running checklist per workstream.

## Sampling Plan (20 ƒÆ' 100 PDFs)
- Randomly pick 20 from `D:\IT workspace\relevant_pdfs` (document selection script/seed for reproducibility).
- Tag each with: file name, detected `numero_convocatoria` (from file name or PDF content), page count, OCR flag, domain (sector/region), ingestion batch ID.
- Ensure diversity: multi-column, tables, scanned images, mixed languages (es/ca/eu/gl), long vs short, multiple beneficiaries.
- For 100-PDF scale-up, reuse selection script to add 80 more with the same stratification.

## Execution Steps (initial cycle)
1. Select and list 20 PDFs; create entries in `ground_truth/selection.md`.
2. Ingest the same 20; record `staging_items` status and hashes in `db_exports/ingestion_log.md`.
3. Extract ground truth fields per `field_matrix.md` into `ground_truth/*.md`.
4. Export DB rows (`convocatorias`, `pdf_extractions`) for those IDs into `db_exports/*.csv|md`.
5. Run diffs; log issues in `findings_ingestion.md` with severity and root-cause guess (API vs LLM vs normalization).
6. Execute search queries/filters; log expected vs actual in `findings_search.md` with precision/recall@k.
7. Run chat question set; log per-turn grading in `findings_chat.md` with hallucination/grounding metrics.
8. Summarize pass/fail and blockers in `todo.md`; plan fixes (testing-script changes only).

## Metric Recommendations
- Ingestion: field-level accuracy %, completeness %, normalized date/amount correctness %, summary length compliance %, PDF linkage success %.
- Search UI: precision@5/10, recall@5/10, NDCG@5/10, filter correctness %, zero-result correctness %, latency p50/p95.
- RAG chat: grounded accuracy %, hallucination rate %, omission rate %, citation coverage %, context recall %, latency p50/p95, tool success %.

## Guardrails
- Do not modify main code; only testing scripts and docs.
- Reuse existing scripts/loggers where possible (e.g., DB export helpers, ingestion trackers).
- Keep everything reproducible: record seeds, timestamps, DB queries, and model/version parameters used.
