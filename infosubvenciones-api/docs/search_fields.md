Reliable Search Fields
======================

- Tipo de ayuda (subvención/concesión/beneficio)
  - Field: `convocatorias.tipo_convocatoria`
  - Modality (if needed): `convocatorias.instrumentos` (JSON)

- Localización geográfica
  - Field: `convocatorias.regiones` (array of NUTS codes/labels)
  - Region codes: `convocatorias.region_nuts`
  - Admin hierarchy: `convocatorias.administracion` (JSON) and `admin_path_normalized`

- Beneficiarios (quién puede solicitar)
  - Primary: `convocatorias.tipos_beneficiario` (API array)
  - Normalized buckets: `convocatorias.beneficiarios_normalizados`
  - Raw detail: `convocatorias.tipos_beneficiarios_raw` (JSON) + `beneficiarios_descripcion`
  - Fallback/standardized (only if API empty): `pdf_extractions.tipos_beneficiario_normalized`

- Tipo de organismo
  - Fields: `convocatorias.organismo`, `organismo_id`
  - Admin path (normalized search): `admin_path_normalized`

- Fechas
  - Publicación: `convocatorias.fecha_publicacion` (falls back to API `fechaRecepcion`)
  - Cierre: `convocatorias.fecha_fin_solicitud`
  - Apertura (optional): `convocatorias.fecha_inicio_solicitud`
  - Estado abierto derivado: `convocatorias.is_open_now`

- Sector / CNAE
  - Primary: `convocatorias.sectores`
  - Normalized: `convocatorias.sectores_normalizados`
  - Raw products: `convocatorias.sectores_productos`
  - Fallback/inferred (if API empty): `pdf_extractions.sectores_inferidos`

- Presupuesto / importes
  - Budget: `convocatorias.presupuesto_total`
  - Other amounts: `importe_total`, `importe_maximo`, `importe_minimo`

- PDF y documento
  - PDF URL: `convocatorias.pdf_url` (with fallback synthesis)
  - Hash/dedup: `convocatorias.pdf_hash`

- Metadatos auxiliares útiles
  - Administración combinada: `convocatorias.administracion` (JSON)
  - Finalidad (código/desc): `convocatorias.finalidad`, `finalidad_descripcion`, `descripcion_finalidad`
  - Bases reguladoras: `url_bases_reguladoras`, `descripcion_bases_reguladoras`
