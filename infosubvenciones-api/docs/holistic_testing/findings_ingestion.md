# Ingestion Findings (Holistic20 batch: holistic20_20251207_112524)

Source artifacts:
- DB snapshots: `db_exports/convocatorias_snapshot.csv`, `db_exports/pdf_extractions_snapshot.csv`
- Diffs: `db_exports/db_vs_truth.csv` (pdf_extractions vs ground truth), `db_exports/conv_vs_truth.csv` (convocatorias vs ground truth, after backfill)
- Ground truth: `ground_truth/*.md` (manual fills + PDF-based fills)

Summary (pdf_extractions vs ground truth):
- 760 comparisons (38 fields ? 20): 373 matches (49.08%), 387 mismatches.
- Key-field mismatches (org/ambito/amounts): 51 total ? `cuantia_min` 18, `intensidad_ayuda` 18, `cuantia_max` 11, `importe_total_pdf` 2, `cuantia_subvencion` 2.
- Top mismatch fields overall: `plazo_resolucion` (20), `subcontratacion` (19), `cuantia_min` (18), `intensidad_ayuda` (18), `criterios_valoracion` (18), `sistema_evaluacion` (17), `requisitos_tecnicos` (17), `pago_anticipado` (16), `url_tramite_pdf` (15), `plazo_ejecucion` (15).
- Per-grant mismatches (sample): 870202 (32), 868377 (29), 868847 (29), 869544 (25), 865496 (24), 865440 (23); lowest: 869156 (8), 866867 (9), 867308 (10).

After convocatorias backfill (conv_vs_truth):
- Backfilled conv.organismo/ambito/importe_* from pdf_extractions when conv fields were null. New diff: 760 comps ? 391 matches (51.45%), 369 mismatches.
- Remaining conv mismatches: descriptive/procedural fields not modeled or empty in conv (titulo/finalidad/normativa, cuantia_subvencion prose vs numeric, bases_reguladoras, obligaciones, forma_solicitud, etc.).

Notable gaps (truth has values; DB missing/different):
- 870202: total 6.820.600,00 ?; individual grants 15.000?200.000 ?; DB lacks amounts/intensity.
- 865268: organism/ambito/importe_total missing; PDF ? Generalitat Valenciana / Comunitat Valenciana / 7.000.000 ?.
- 865440: organism/ambito/importe_total missing; PDF ? Excmo. Ayto. Alicante (Servicio de Fiestas) / Alicante / ~124.000 ?.
- 865496: organism/ambito/importe_total missing; PDF ? Ajuntament de Castell? / Castell? / ~18.200 ? (min 1.000 ?, max 5.800 ?).
- 866011: organism/importe_total missing; PDF ? Concello de Celanova / 1.200 ?.
- 868377: total 16.000 ? split (10.000 + 6.000); procedural fields largely empty.
- 868847: ordinance; amounts not specified (expected null), but procedural fields missing in DB.

Root-cause tags for Claude:
- API missing: conv-side nulls for organism/ambito/amounts.
- Normalization: prose/aggregate amounts not parsed into `cuantia_min/max` and `importe_total`; `intensidad_ayuda` left blank.
- Extraction coverage: procedural fields (`plazo_*`, `subcontratacion`, `criterios_valoracion`, `documentos_fase_solicitud`, `requisitos_tecnicos`, `pago_anticipado`) often null.
- Comparison strictness: null vs empty string counts as mismatch; treat null==null as OK, but fill when ground truth has data.

Recommendations:
- Keep backfilling conv.organismo/ambito/importe_* when conv is null (applied for this batch).
- Improve amount parsing (prose/ranges) to populate cuantia_min/max, importe_total, intensidad_ayuda; align cuantia_subvencion when prose.
- Enhance extraction/prompts for procedural fields (plazo_resolucion/ejecucion/justificacion, subcontratacion, criterios_valoracion, documentos_fase_solicitud, requisitos_tecnicos, pago_anticipado).
- Adjust diff logic to treat null==null as pass, but still flag when ground truth is populated and DB is missing.

DB vs PDF (convocatorias vs pdf_extractions) after backfill:
- Comparison file: `db_exports/db_vs_pdf_current.csv` (6 key fields ? 20 ? 120 comparisons)
- Result: 89 matches, 31 mismatches (74.17% match).
- Mismatches: `importe_total` (18), `importe_maximo` (9), `importe_minimo` (2), `titulo` (2).
- Typical cause: conv normalized numeric vs PDF prose (e.g., 7.000.000,00 ? vs text; multi-sum totals like 100.000 + 24.000; prose amounts 18.200,00 ?), and long titles differing in wording.
