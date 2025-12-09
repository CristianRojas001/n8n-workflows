# Search Findings

## 2025-12-09 ƒ?" Holistic20 search run (GrantSearchEngine.hybrid_search direct)
- Context: ran via Django services (no HTTP) using new Gemini key; pgvector extension missing so semantic search fell back to Python cosine.
- Dataset: Holistic20 batch + existing DB test rows (e.g., `TEST-PDF-001`, `872177`), which pollute rankings.

| Case | Query / Filters | Expected IDs | Top returned (first 5) | Issue |
| --- | --- | --- | --- | --- |
| 1 | "alicante fiestas" | 865440, 865736 | 865440, 870193, 870393, 870434, 866901 | 865736 down at #9; heavy noise (fiestas nouns pulling other nominativas). |
| 2 | "cultura catalana salou" | 868801 | 868801, 872177, 866901, 870393, 868377 | Expected #1, but noisy tail. |
| 3 | regiones = ["ES213 - Bizkaia"] | 868306, 869544, 870439 | — | Filter returned 0 (likely regiones array mismatch/empty). |
| 4 | "torneos futbol" | 869156 | 869156, 870439, TEST-PDF-001, 870393, 868377 | Expected #1; noise. |
| 5 | "belenes manises" | 870193 | 870193, TEST-PDF-001, 872186, 872187, 872188 | Expected #1; strong noise. |
| 6 | "corrida de toros" | 870393 | 870393, TEST-PDF-001, 866011, 872177, 868377 | Expected #1; noise. |
| 7 | "DANA infraestructura" | 865268 | 865268, TEST-PDF-001, 872177, 872187, 872188 | Expected #1; noise. |
| 8 | "playmobil dioramas" | 867418 | 867418, TEST-PDF-001, 865268, 870440, 870431 | Expected #1; noise. |
| 9 | "ordenanza general subvenciones El Rosario" | 868847 | 868847, TEST-PDF-001, 870438, 872177, 866011 | Expected #1; noise. |
| 10 | "subvención nominativa Castelló convenio" | 865496 | TEST-PDF-001, 865496, 872177, 868801, 868377 | Expected at #2; noisy top. |
| 11 | "convenio celanova comadres" | 866011 | 865496, TEST-PDF-001, 866011, 870436, 865736 | Expected at #3; wrong item #1. |
| 12 | ambito = "Nacional" | 870202, 867308, 870439 | 870202, 867308, 870439 | Filter OK. |
| 13 | "cultura internacional ministerio" | 870202 | TEST-PDF-001, 866901, 870202, 870421, 872177 | Expected at #3; noise dominates. |
| 14 | "obras torre telégrafo" | 867823 | TEST-PDF-001, 870436, 870393, 872186, 870434 | Missed expected entirely (recall fail). |
| 15 | "convenio gümar banda de tambores" | 866867 | TEST-PDF-001, 866867, 870431, 870436, 865496 | Expected at #2; noise. |

**Key takeaways**
- Semantic scoring works but is dominated by noisy test/other grants; need to exclude test rows (`TEST-PDF-001`, `872177`, etc.) from search.
- Region filter for `regiones=["ES213 - Bizkaia"]` returns zero -> likely data mismatch (array values not matching strings) or missing regiones in DB.
- Some queries (e.g., torre telégrafo) lose recall entirely despite relevant record existing.
- pgvector extension absent on Supabase; search uses slow Python fallback and logs exceptions. Enabling pgvector should improve recall/ranking stability.

## 2025-12-09 ƒ?" Holistic20 rerun after deleting test rows + enabling pgvector
- Context: DB cleaned (`TEST-PDF-001`, `872177` removed) and pgvector enabled; reran GrantSearchEngine.hybrid_search directly (no HTTP).
- Dataset now totals 35 rows; semantic uses pgvector without Python fallback.

| Case | Query / Filters | Expected | Top returned (first 5) | Issue/Note |
| --- | --- | --- | --- | --- |
| 1 | "alicante fiestas" | 865440, 865736 | 865440, 870193, 870393, 870434, 866901 | 865736 at #8; residual fiesta noise. |
| 2 | "cultura catalana salou" | 868801 | 868801, 866901, 870393, 868377, 870202 | Expected #1, but some tail noise. |
| 3 | regiones=["ES213 - Bizkaia"] | 868306, 869544, 870439 | — | Still 0 results; regiones filter likely mismatched values. |
| 4 | "torneos futbol" | 869156 | 869156, 870439, 870393, 868377, 867418 | Expected #1; moderate noise. |
| 5 | "belenes manises" | 870193 | 870193, 872186, 872187, 872188, 866011 | Expected #1; some noise. |
| 6 | "corrida de toros" | 870393 | 870393, 866011, 868377, 870434, 870436 | Expected #1; some noise. |
| 7 | "DANA infraestructura" | 865268 | 865268, 872187, 872188, 872186, 867308 | Expected #1; some noise. |
| 8 | "playmobil dioramas" | 867418 | 867418, 865268, 870440, 870431, 870436 | Expected #1; some noise. |
| 9 | "ordenanza general subvenciones El Rosario" | 868847 | 868847, 870438, 866011, 869156, 869544 | Expected #1; mild noise. |
| 10 | "subvención nominativa Castelló convenio" | 865496 | 865496, 868801, 868377, 870438, 866011 | Expected #1; noise follows. |
| 11 | "convenio celanova comadres" | 866011 | 865496, 866011, 870436, 865736, 870438 | Expected at #2; top-1 wrong. |
| 12 | ambito="Nacional" | 870202, 867308, 870439 | 870202, 867308, 870439 | Filter OK. |
| 13 | "cultura internacional ministerio" | 870202 | 866901, 870202, 870421, 870426, 870424 | Expected at #2; noisy top. |
| 14 | "obras torre telégrafo" | 867823 | 870436, 870393, 872186, 870434, 872187 | Missed target entirely (recall fail). |
| 15 | "convenio gümar banda de tambores" | 866867 | 866867, 870431, 870436, 865736, 868377 | Expected #1; noise after. |

**Key takeaways (post-cleanup)**
- Removing test rows reduced some noise but rankings are still loose; need tighter semantic/keyword weighting and maybe field boosts.
- `regiones` filter still broken for Bizkaia -> check stored values vs. strings; ensure array overlap uses matching codes/text.
- Specific recall gap remains for case 14 (torre telégrafo) and minor ranking errors for cases 1, 11, 13.
