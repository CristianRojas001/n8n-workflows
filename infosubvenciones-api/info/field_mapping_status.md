# InfoSubvenciones Field Mapping Status

| Category | Field (per classification doc) | Status | Notes / Storage |
| --- | --- | --- | --- |
| Organismo | Organismo nombre completo | **Stored** | `convocatorias.organismo` and `raw_api_response.organo.*` |
|  | Organismo tipo (estatal/autonómico…) | **Needs derivation** | Could derive from `tipo_administracion`/`nivel_administracion`; no dedicated column |
| Sector económico | Sector CNAE código/descr. | **Stored** | Raw array in `convocatorias.sectores` (strings) |
|  | Sector categoría agrupada | **Needs derivation** | Requires mapping logic |
|  | Finalidad descripción/código | **Stored** | `convocatorias.finalidad`, `finalidad_descripcion` |
| Tipo de ayuda | Instrumento financiero | **Stored (raw JSON)** | Present inside `convocatorias.raw_api_response->'instrumentos'`; not normalized |
|  | Tipo de convocatoria | **Stored** | `convocatorias.tipo_convocatoria` |
|  | Tipo de ayuda (clasificación) | **Needs derivation** | Would derive from `instrumentos[].descripcion` |
| Gastos / requisitos PDF | Gastos subvencionables, actividades elegibles, compatibilidades, garantías, subcontratación, forma de pago/justificación, plazos de ejecución/justificación, obligaciones, publicidad, modificaciones, documentación | **Stored** | Dedicated columns in `pdf_extractions` |
| Fondos | Fondos descripción/origen/tipo | **Stored (raw JSON)** | Only in `raw_api_response.fondos`; no normalized columns |
| Beneficiarios | Tipos beneficiarios | **Stored** | `convocatorias.tipos_beneficiario` |
|  | Códigos beneficiarios (1/2/3/4) | **Needs derivation** | Requires mapping from descriptions |
|  | Beneficiario específico (nombre/CIF) | **Stored** | `pdf_extractions.beneficiario_nombre`, `beneficiario_cif` |
| Ámbito geográfico | Regiones NUTS | **Stored** | `convocatorias.regiones` |
|  | Comunidad autónoma “limpia” | **Needs derivation** | Parse `regiones` strings |
|  | Código postal | **Missing** | Not provided by API/PDF |
| Información económica | Presupuesto total, importe min/max, % financiación | **Stored** | `convocatorias` columns |
|  | Cuantía individual, presupuesto min/max proyecto, aplicación presupuestaria | **Stored / Missing** | `pdf_extractions.cuantia_*` capture amounts; application budget still missing |
| Plazos | Estado abierto/cerrado, fechas solicitud/recepción, textos | **Stored** | `convocatorias.*` |
|  | Plazo de ejecución / justificación | **Stored** | `pdf_extractions.plazo_ejecucion`, `plazo_justificacion` |
| Descripción / bases | Descripción, bases, ayudas de estado | **Stored** | `convocatorias.descripcion`, `descripcion_bases_reguladoras`, `url_bases_reguladoras`, `ayuda_estado`, `url_ayuda_estado` |
|  | Finalidad detallada | **Captured in summary** | LLM summary in `pdf_extractions.extracted_summary`; no dedicated column |
| Objetivos | Objetivos política gasto | **Stored (raw JSON)** | Only in `raw_api_response.objetivos` |
| Procedimiento | Forma pago/justificación, publicidad, modificaciones | **Stored** | `pdf_extractions` columns |
| Documentación | Document IDs, nombres, tamaños, fechas | **Stored** | `convocatorias.documentos` JSONB |
|  | CSV verificación, firmantes | **Missing** | Not extracted |
| Metadatos | id, numeroConvocatoria, codigoBDNS, sede, sePublica, MRR, reglamento, anuncios, advertencia | **Stored / Stored (raw JSON)** | Basic columns exist; `mrr`, `reglamento`, `anuncios`, `advertencia`, `codigoInvente`, `sectoresProductos` live only in `raw_api_response` |
| Gestión interna | Gestores asignados | **Not applicable** | Managed outside InfoSubvenciones |

_Last updated: 2025-12-03_
