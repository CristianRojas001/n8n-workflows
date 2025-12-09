# Holistic Testing Change Log (manual edits)

2025-12-08
- Updated `ground_truth/870202.md` with total credit (6.820.600,00 €), per-entity grant ranges (15.000–200.000 €), and notes on direct nominative grants.
- Updated `ground_truth/868377.md` with beneficiary requirements and application/presentation details (concello de Neda call).
- Re-ran comparison against completed ground truth; generated `db_exports/db_vs_truth.csv` and refreshed `findings_ingestion.md` with final discrepancy summary and tagged root causes.
- Recreated `findings_ingestion.md` to reflect latest diff (49.08% match across 38 fields × 20 items) and recommendations for backfill/normalization/extraction improvements.
- Backfilled `convocatorias` organismo/ambito/importe_* from `pdf_extractions` for the 20-item batch; added `db_exports/conv_vs_truth.csv` (51.45% match after backfill). Updated `findings_ingestion.md` accordingly.
- Generated DB vs PDF key-field diff after backfill: `db_exports/db_vs_pdf_current.csv` (6 fields × 20 → 120 comparisons; 74.17% match). Added summary to `findings_ingestion.md`.

- Added search case definitions for the Holistic20 batch in `search_cases/holistic20.md` (queries/filters with expected IDs from DB).

2025-12-09
- Updated backend `.env` `GEMINI_API_KEY` to new valid key and re-ran `test_gemini_api.py`; gemini-2.5-flash-lite now responds successfully.
- Ran Holistic20 search cases via `GrantSearchEngine.hybrid_search`; logged outcomes/noise in `findings_search.md` (test rows pollute rankings; Bizkaia region filter returns 0; pgvector missing so Python fallback used).
- Re-ran Holistic20 search cases after deleting test rows and enabling pgvector; updated `findings_search.md` (noise reduced but still ranking issues, Bizkaia filter still broken, one recall miss).
