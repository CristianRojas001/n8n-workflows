# Necesidades del cliente (Artisting)
- Alcance de datos: convocatorias vigentes a nivel nacional (plazo abierto) para Cultura (finalidad=11) y Comercio (finalidad=14).
- Beneficiarios: PYMES y autónomos/personas físicas con actividad económica (tiposBeneficiario=3,2).
- Fuentes: API oficial de InfoSubvenciones (convocatorias, detalle por `numConv`, documentos/PDF asociados).
- Contenido a extraer: campos estructurados (objeto, beneficiarios, cuantía, plazos, ámbito geográfico, requisitos/procedimiento) y texto principal de cada convocatoria (PDF/bases).
- Consultas: responder preguntas tipo “¿qué ayudas hay para autónomos de artes escénicas de Madrid?” mediante filtros + búsqueda (RAG/misGPT) con citas a la convocatoria/PDF.
- Outputs operativos: tabla/base de datos filtrable (beneficiario, sector, territorio, fechas, cuantía), PDFs descargados, resúmenes breves por convocatoria, embeddings para búsqueda semántica.
- Alcance geográfico: nacional (sin filtro fijo a Madrid), pero debe permitir filtrar por región/sector en consultas.

## Web y API
- Portal: https://www.infosubvenciones.es/bdnstrans/
- API base: https://www.infosubvenciones.es/bdnstrans/api
- Endpoints clave:
  - `convocatorias/busqueda?abierto=true&finalidad=11|14&tiposBeneficiario=3,2&page=..&size=..` — listado filtrado.
  - `convocatorias?numConv=<numeroConvocatoria>` — detalle con metadatos y documentos.
  - `convocatorias/documentos?idDocumento=<idDocumento>` — descarga de anexos/bases.
  - `convocatorias/pdf?id=<idConvocatoria>&vpd=GE` — PDF completo de la convocatoria.

## Resumen del proyecto
- Ingestar convocatorias vigentes de Cultura/Comercio para PYMES/autónomos desde la API oficial, descargar PDFs y extraer campos clave.
- Generar resúmenes breves por convocatoria para alimentar una capa de búsqueda semántica (embeddings) y responder consultas con citas.
- Proveer base filtrable y servir PDFs completos bajo demanda para verificación y detalle.
