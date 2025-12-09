# Holistic Testing TODO

This file tracks the progress of the holistic testing plan.

## Workstreams

- [x] 1. DB vs PDF (ingestion accuracy)
  - [x] Select and list 20 PDFs; create entries in `ground_truth/selection.md`.
  - [x] Ingest the same 20; record `staging_items` status and hashes in `db_exports/ingestion_log.md`. (All 20 ingested with embeddings; LLM processed for all 20 after rerunning 866867.)
  - [ ] Extract ground truth fields per `field_matrix.md` into `ground_truth/*.md`.
  - [ ] Export DB rows (`convocatorias`, `pdf_extractions`) for those IDs into `db_exports/*.csv|md`.
  - [ ] Run diffs; log issues in `findings_ingestion.md`.

- [ ] 2. DB vs Search UI (relevance + filters)
  - [ ] Define a fixed query set (10–15).
  - [ ] For each query, derive expected set/order from DB.
  - [ ] Drive UI with same queries/filters.
  - [ ] Evaluate precision/recall, filter correctness.
  - [ ] Log findings in `findings_search.md`.

- [ ] 3. DB vs RAG chat (grounded QA)
  - [ ] Build a question set.
  - [ ] Run chat with fixed prompts.
  - [ ] Grade against DB for factual accuracy, citations, etc.
  - [ ] Log findings in `findings_chat.md`.
