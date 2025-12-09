# Ingestion Log (Selected PDFs)

Track ingestion status for sampled PDFs.

Columns:
- numero_convocatoria
- staging_id
- convocatoria_id
- pdf_hash
- pdf_page_count / pdf_word_count
- status (pending/processing/completed/failed)
- error_message (if any)
- timestamps (created_at, updated_at, completed_at)

Entries:
- Batch `holistic20_20251207_112524` (2025-12-07 UTC) via InfoSubvenciones API detail -> staging -> `process_pdf` -> `process_with_llm` -> `generate_embedding`.

| numero_convocatoria | staging_id | convocatoria_id | pdf_hash | pdf_page_count / pdf_word_count | status | error_message | batch_id |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 865736 | 107 | 117 | e167bc4cd818dd153bc927191f3215c5ec4bba97cea0e44018b79726e9db7ddf | 11p / 5948w | COMPLETED |  | holistic20_20251207_112524 |
| 870202 | 108 | 118 | 44b2bfc0e21c689ce0cd6a3460e9258bf1f6132eb7bd507af49b6a69112bec5b | 28p / 18282w | COMPLETED |  | holistic20_20251207_112524 |
| 869544 | 109 | 119 | 54ec0e25bdc444835511dd851db1ec1184596ca0ca611ed4452a7480884c461c | 2p / 605w | COMPLETED |  | holistic20_20251207_112524 |
| 869156 | 110 | 120 | 58b8c08d4dc957f34190eda2e4af1695cdc35b7d97ce745ae1447599078250b5 | 11p / 4922w | COMPLETED |  | holistic20_20251207_112524 |
| 866011 | 111 | 121 | a4b8b251a881c8f2d05b9a00ae25cf19146cf6e2a7ff915ccc9ed0c6254355e4 | 18p / 8496w | COMPLETED |  | holistic20_20251207_112524 |
| 870439 | 87 | 97 | 5758d79344c182d1258e7016fcaf04f9ba1771ca17bfb17d0c3bd60e21b3cd65 | 3p / 731w | COMPLETED |  | holistic20_20251207_112524 |
| 865268 | 112 | 122 | fa25311f6313e10328ded93855c87aac7617ee6bbbb5076b3682b56d96ddd632 | 10p / 6175w | COMPLETED |  | holistic20_20251207_112524 |
| 867308 | 113 | 123 | ed97fcda903bd4b82802957fb4496d017cdc570f7a1e5367248c6e2aaacdb065 | 8p / 3523w | COMPLETED |  | holistic20_20251207_112524 |
| 867418 | 114 | 124 | 0afcef70fe0e3b05c2305df2f5da11ff351b8759436b081429122c59cff147cd | 5p / 1879w | COMPLETED |  | holistic20_20251207_112524 |
| 865496 | 115 | 125 | a455d5b3bcc834a4749bbfca53f57fabc141c4af23ac95faf23e09a542900080 | 3p / 750w | COMPLETED |  | holistic20_20251207_112524 |
| 866901 | 116 | 126 | 97cf5fba3af696a19b53a1beb2d85dd57d5cdf870c378ad97a6c27982c2a6762 | 3p / 1528w | COMPLETED |  | holistic20_20251207_112524 |
| 865440 | 117 | 127 | ff7ab2f641b84499a3d056b99f6ab169ccb721ff265a30088aed667f83185073 | 3p / 1301w | COMPLETED |  | holistic20_20251207_112524 |
| 870393 | 118 | 128 | 364532ee9f5e9311a40aabb9b5b3cf48156f0925296adcffd7b07d3a51ac8ee0 | 3p / 1224w | COMPLETED |  | holistic20_20251207_112524 |
| 870193 | 119 | 129 | 942685a2b077114f0654d24a9d1ec6cd4cebddd5fc885abcbf1f948af22bb978 | 6p / 2362w | COMPLETED |  | holistic20_20251207_112524 |
| 868847 | 120 | 130 | f2366faae4bd8618227056ffaab9a8f76bb694c68045ef92c15806d937fba8d9 | 58p / 27228w | COMPLETED |  | holistic20_20251207_112524 |
| 868377 | 121 | 131 | f4119c4c8f91ef54a54861874015901aca4072c05a9beac49bf06ac252a7cfde | 3p / 1019w | COMPLETED |  | holistic20_20251207_112524 |
| 868306 | 122 | 132 | 6d71b0a954336b0588fa443ca1ee986e87f62fb8787aee97bd3dc091848d108e | 9p / 4530w | COMPLETED |  | holistic20_20251207_112524 |
| 867823 | 123 | 133 | c715951555afd6020eaa17c9a28db538667e848258fbbffcf3f8cc39b7e45b56 | 3p / 1558w | COMPLETED |  | holistic20_20251207_112524 |
| 868801 | 124 | 134 | 2f1b1b2ea4045c1d14c3dc093788f3cf51aa117967437cb0dcc96207d5c7fc74 | 8p / 3548w | COMPLETED |  | holistic20_20251207_112524 |
| 866867 | 125 | 135 | 7cdaa282bb04f651abfbe7294cf0f80d049becf1986cb6b5c35906734f6e8adc | 16p / 6714w | COMPLETED |  | holistic20_20251207_112524 |

Notes:
- Built `pdf_url` from `pdf_id_documento` (Infosubvenciones documentos endpoint) and reprocessed; all 20 now have PDF extractions, embeddings, and staging status COMPLETED.
- LLM processed and populated fields for all 20 (reran 866867 with Gemini monetized).
