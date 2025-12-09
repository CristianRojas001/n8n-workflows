# Search Cases — Holistic20 Batch (expected DB results)

Base endpoint: `POST /api/v1/grants/search/` (no auth noted in docs). Use these queries/filters and compare returned `numero_convocatoria` + order to the expected list below.

| Case | Query / Filters | Expected `numero_convocatoria` (order by relevance) | Notes |
| --- | --- | --- | --- |
| 1 | Query: "alicante fiestas" | [865440, 865736] | Both are Alicante fiesta nominative aids. |
| 2 | Query: "cultura catalana salou" | [868801] | Salou capital de la cultura catalana. |
| 3 | Filter: `regiones=["ES213 - Bizkaia"]` | [868306, 869544, 870439] | All Bizkaia-scope grants. |
| 4 | Query: "torneos futbol" | [869156] | Torneos de fútbol (Cáceres). |
| 5 | Query: "belenes manises" | [870193] | Concurso de belenes Manises. |
| 6 | Query: "corrida de toros" | [870393] | Nominativa corrida de toros Berja. |
| 7 | Query: "DANA infraestructura" | [865268] | Dotación crédito Circuito del Motor (DANA). |
| 8 | Query: "playmobil dioramas" | [867418] | Concurso Dioramas Playmobil/Legos. |
| 9 | Query: "ordenanza general subvenciones El Rosario" | [868847] | Ordenanza general El Rosario. |
| 10 | Query: "subvención nominativa Castelló convenio" | [865496] | Subvención nominativa Castelló. |
| 11 | Query: "convenio celanova comadres" | [866011] | Nominativa Concello de Celanova. |
| 12 | Filter: `ambito="Nacional"` | [870202, 867308, 870439] | National-scope items; order may vary by relevance. |
| 13 | Query: "cultura internacional ministerio" | [870202] | Real Decreto 663/2025 (cultura, nacional). |
| 14 | Query: "obras torre telégrafo" | [867823] | Obra rehabilitación Torre telégrafo (Palencia). |
| 15 | Query: "convenio güímar banda de tambores" | [866867] | Convenio nominativo Güímar. |

Execution: Run each case via the search API, capture returned IDs/order, and log deviations in `findings_search.md` (precision/recall@k, order, filter correctness).***
