# Interface Requirements

## Objetivo
Crear una interfaz web ligera (light mode) que actúe como chat con un agente en n8n para consultar convocatorias de subvenciones (Cultura/Comercio, PYMES/Autónomos) y permitir ver/descargar PDFs.

## Arquitectura
- Frontend delgado: muestra UI, envía POST al webhook de n8n y renderiza respuesta.
- Backend/Agente: n8n realiza filtrado, búsqueda, generación, citas, PDFs y contexto. Contexto guardado en n8n con TTL 24–72h.
- Auth: Google Sign-In en frontend. Webhook protegido con Basic Auth + validación de token. CORS restringido al dominio interno.

## API (POST único)
- Request: `{ sessionId, message, filters: { region?, beneficiario?, finalidad?, fechaDesde?, fechaHasta?, cuantiaMin?, cuantiaMax? }, topK?, includeSources? }`
- Response: `{ answer, citations: [{ snippet, articulo?, page?, pdfUrl }], convocatorias: [{ id, titulo, region, beneficiario, deadline, cuantia, pdfUrl, sourceUrl }], appliedFilters, trace?, error? }`
- Errores: `{ error: { code, message, stage } }` con HTTP 400/429/500.

## Flujo de usuario
1) Usuario escribe pregunta + aplica filtros (chips/presets).
2) Frontend envía POST al webhook con sessionId y filtros.
3) UI muestra barra de estado (Filtrando ? Búsqueda semántica ? Recuperando ? Generando) y badge de modelo/latencia/última actualización.
4) Respuesta: burbuja con texto + “Filtros aplicados”. Bajo la respuesta, lista compacta de 3–5 convocatorias con acciones `Ver PDF` (viewer) y `Descargar` (link directo).
5) PDF: panel/drawer derecho (desktop) o full-screen sheet (mobile) con navegación de páginas, zoom y botón fijo `Descargar`. Si CORS bloquea, mostrar mensaje y link directo. Citaciones saltan a página si hay hint.
6) “Resetear chat” limpia contexto (sessionId nuevo o clear en n8n).

## Diseño (light, moderno, limpio)
- Layout: escritorio dos columnas (chat+filtros izquierda, visor PDF derecha). Móvil: chat full-width, PDF en sheet.
- Colores: fondo `#F8FAFC`, texto `#0F172A`, cards `#FFFFFF`, borde `#E2E8F0`, primario `#2563EB` (hover `#1D4ED8`), info `#0EA5E9`, warning `#F59E0B`, success `#22C55E`.
- Tipografía: Manrope/Inter Tight; 20/24 headings, 16/18 cuerpo, 13/14 meta; mono para IDs.
- Componentes: burbujas con citas en chips; lista de resultados con título, ID, deadline, región, beneficiario, cuantía, relevancia; botones `Ver PDF` (primario) y `Descargar` (ghost); chips de filtros + presets (Autónomos, PYMES, Cultura, Comercio, Próximos 30 días); barra de estado pipeline; badge modelo+latencia+últ. actualización; input pegado abajo; botón “Resetear chat”.
- Microinteracciones: drawer con slide suave, hover/active states, skeleton en resultados, focus rings `#2563EB`.
- Vacíos/errores: "Sin resultados, prueba relajando plazos o región"; errores amistosos en español con retry.

## PDFs
- Preferir `pdfUrl` directo (convocatorias/pdf?id=... o documentos?idDocumento=...).
- Si CORS impide previsualizar, n8n devuelve URL proxificada para viewer y link directo para descarga.
- Mostrar dominio fuente y tamaño si se conoce.

## Límites y timeouts
- Rate limit suave: 3–5 req / 10s por usuario/session; devolver 429 con `retryAfter`.
- Timeouts por etapa: búsqueda ~3s, recuperación ~5s, generación ~20s; si expira, responder breve y `error.stage`.

## Observabilidad
- Logs: sessionId, userId/email, filtros, modelo, latencia por etapa, errores.
- Trazas de pasos: filtrar ? buscar ? recuperar ? generar.
- Alerta por picos de error.

## Localización y formato
- Idioma español, fechas DD/MM/AAAA, moneda en euros con locale `es-ES`.

## Roles y acceso
- Un solo rol (lector). Acceso interno (SSO/IAP) y Basic Auth en webhook.

## Historial (optativo si es fácil)
- Guardar últimas N consultas por usuario en n8n; permitir “Reusar consulta”.
