# Clasificación Completa de Campos - InfoSubvenciones API + PDFs

## Resumen Ejecutivo
Esta tabla clasifica TODOS los campos disponibles según su origen: API directa, API inferida, o solo disponible en PDFs.

---

## TABLA RESUMEN COMPLETA

| Requisito del Cliente | Disponibilidad | Fuente | Campo/Lógica | Notas |
|----------------------|----------------|--------|--------------|-------|
| **ORGANISMO CONVOCANTE** |||||
| Organismo - nombre completo | ✅ DIRECTO | API | `organo.nivel1`, `organo.nivel2`, `organo.nivel3` | 3 niveles jerárquicos |
| Organismo - tipo (estatal/autonómico/provincial/municipal) | 🔄 INFERIDO | API | `organo.nivel1` + `organo.nivel2` → clasificar | Requiere lógica |
| **SECTOR ECONÓMICO** |||||
| Sector CNAE - código | ✅ DIRECTO | API | `sectores[].codigo` | Ej: "R", "C", "G" |
| Sector CNAE - descripción | ✅ DIRECTO | API | `sectores[].descripcion` | Texto completo |
| Sector - categoría agrupada | 🔄 INFERIDO | API | `sectores[].codigo` → mapear | cultura/i+d/industria/turismo/comercio |
| Finalidad - descripción | ✅ DIRECTO | API | `descripcionFinalidad` | "Cultura", "Comercio, Turismo y Pymes" |
| Finalidad - código | 🔄 INFERIDO | API | `descripcionFinalidad` → mapear | 11=Cultura, 14=Comercio |
| **TIPO DE AYUDA** |||||
| Instrumento financiero | ✅ DIRECTO | API | `instrumentos[].descripcion` | Texto descriptivo |
| Tipo de convocatoria | ✅ DIRECTO | API | `tipoConvocatoria` | Concesión directa / Concurrencia competitiva |
| Tipo ayuda - clasificación | 🔄 INFERIDO | API | `instrumentos[].descripcion` → clasificar | subvención/préstamo/beca/bonificación/premio |
| **GASTOS Y REQUISITOS (SOLO PDF)** |||||
| Gastos subvencionables detallados | ❌ PDF | PDF | Sección "Gastos o partidas subvencionables" | Lista detallada de conceptos elegibles |
| Actividades elegibles específicas | ❌ PDF | PDF | Texto del PDF | Descripción completa de qué se puede financiar |
| Garantías requeridas | ❌ PDF | PDF | Sección "Exigencia de garantía" | Si requiere avales o garantías |
| Compatibilidad con otras ayudas | ❌ PDF | PDF | Sección "Compatibilidad/incompatibilidad" | Si se puede combinar con otros fondos |
| Reglas de subcontratación | ❌ PDF | PDF | Sección "Subcontratación" | Porcentajes y condiciones |
| **ORIGEN DE LOS FONDOS** |||||
| Fondos - descripción | ✅ DIRECTO | API | `fondos[].descripcion` | FEDER, FSE, Next Generation, etc. |
| Fondos - origen (UE/nacional) | 🔄 INFERIDO | API | `len(fondos)` > 0 → europeo, else nacional | Booleano |
| Fondos - tipo específico | 🔄 INFERIDO | API | `fondos[].descripcion` → extraer | FEDER/FSE/Next Gen |
| **BENEFICIARIOS** |||||
| Tipos de beneficiarios | ✅ DIRECTO | API | `tiposBeneficiarios[].descripcion` | PYMES, personas físicas, etc. |
| Códigos de beneficiarios | 🔄 INFERIDO | API | `tiposBeneficiarios[].descripcion` → mapear | 1/2/3/4 |
| Beneficiario específico (nombre y CIF) | ❌ PDF | PDF | Sección "Beneficiario y CIF" | Solo en resoluciones de concesión |
| **ÁMBITO GEOGRÁFICO** |||||
| Regiones - NUTS completo | ✅ DIRECTO | API | `regiones[].descripcion` | "ES300 - Madrid" |
| Comunidad autónoma (sin código) | 🔄 INFERIDO | API | `regiones[].descripcion` → parsear | Solo nombre |
| Código postal | ❌ N/A | N/A | No disponible | Ni en API ni en PDF |
| **INFORMACIÓN ECONÓMICA** |||||
| Presupuesto total de la convocatoria | ✅ DIRECTO | API | `presupuestoTotal` | En euros |
| Cuantía individual concedida | ❌ PDF | PDF | Sección "Cuantía de la subvención" | Solo en resoluciones |
| Presupuesto mínimo/máximo del proyecto | ❌ PDF | PDF | Texto del PDF (si especifica) | Límites por proyecto |
| Aplicación presupuestaria | ❌ PDF | PDF | "24.05.333A.485.48" | Partida contable |
| **PLAZOS Y FECHAS** |||||
| Estado - abierto/cerrado | ✅ DIRECTO | API | `abierto` | Boolean |
| Fecha inicio solicitudes | ✅ DIRECTO | API | `fechaInicioSolicitud` | YYYY-MM-DD |
| Fecha fin solicitudes | ✅ DIRECTO | API | `fechaFinSolicitud` | YYYY-MM-DD |
| Fecha recepción BDNS | ✅ DIRECTO | API | `fechaRecepcion` | YYYY-MM-DD |
| Texto inicio/fin | ✅ DIRECTO | API | `textInicio`, `textFin` | Descripción textual |
| Plazo ejecución del proyecto | ❌ PDF | PDF | "del 1 de enero al 31 de diciembre de 2025" | Diferente del plazo de solicitud |
| Plazo de justificación | ❌ PDF | PDF | "Hasta el 31 de marzo de 2026" | Deadline para reportes |
| **DESCRIPCIÓN Y BASES** |||||
| Descripción de la convocatoria | ✅ DIRECTO | API | `descripcion` | Resumen |
| Descripción en lengua cooficial | ✅ DIRECTO | API | `descripcionLeng` | Si aplica |
| Finalidad detallada | ❌ PDF | PDF | Sección "Finalidad" | Objetivo específico del gasto |
| Bases reguladoras - nombre | ✅ DIRECTO | API | `descripcionBasesReguladoras` | Nombre normativa |
| Bases reguladoras - URL | ✅ DIRECTO | API | `urlBasesReguladoras` | Link a BOE/BOJA |
| Ayudas de Estado - referencia | ✅ DIRECTO | API | `ayudaEstado` | Código |
| Ayudas de Estado - URL | ✅ DIRECTO | API | `urlAyudaEstado` | Link |
| **OBJETIVOS** |||||
| Objetivos de política de gasto | ✅ DIRECTO | API | `objetivos[].descripcion` | Array |
| **PROCEDIMIENTO Y CUMPLIMIENTO** |||||
| Forma de pago | ❌ PDF | PDF | "libramiento único, anticipado" | Timing y método |
| Forma de justificación | ❌ PDF | PDF | Lista detallada de documentos | Memoria, auditoría, etc. |
| Requisitos de publicidad | ❌ PDF | PDF | "incluir imagen institucional" | Branding obligatorio |
| Modificaciones permitidas | ❌ PDF | PDF | Procedimiento de cambios | Cómo solicitar cambios |
| **DOCUMENTACIÓN** |||||
| Documentos - ID | ✅ DIRECTO | API | `documentos[].id` | Identificador |
| Documentos - descripción | ✅ DIRECTO | API | `documentos[].descripcion` | Tipo de documento |
| Documentos - nombre archivo | ✅ DIRECTO | API | `documentos[].nombreFic` | Filename |
| Documentos - tamaño | ✅ DIRECTO | API | `documentos[].long` | Bytes |
| Documentos - fecha modificación | ✅ DIRECTO | API | `documentos[].datMod` | YYYY-MM-DD |
| Documentos - fecha publicación | ✅ DIRECTO | API | `documentos[].datPublicacion` | YYYY-MM-DD |
| Documento - CSV verificación | ❌ PDF | PDF | "GEN-2a03-7401-17a4..." | Código de autenticidad |
| **METADATOS TÉCNICOS** |||||
| ID interno | ✅ DIRECTO | API | `id` | Número |
| Número de convocatoria | ✅ DIRECTO | API | `numeroConvocatoria` | Identificador principal |
| Código BDNS | ✅ DIRECTO | API | `codigoBDNS` | Código oficial |
| Sede electrónica | ✅ DIRECTO | API | `sedeElectronica` | URL |
| Publicado en diario oficial | ✅ DIRECTO | API | `sePublicaDiarioOficial` | Boolean |
| MRR (Mecanismo Recuperación) | ✅ DIRECTO | API | `mrr` | Boolean |
| Reglamento aplicable | ✅ DIRECTO | API | `reglamento` | Referencia |
| Código INVENTE | ✅ DIRECTO | API | `codigoInvente` | Si aplica |
| Sectores de productos | ✅ DIRECTO | API | `sectoresProductos[]` | Raramente poblado |
| Anuncios relacionados | ✅ DIRECTO | API | `anuncios[]` | Modificaciones |
| Advertencia legal | ✅ DIRECTO | API | `advertencia` | Texto legal |
| Firmantes y autoridad | ❌ PDF | PDF | Nombre y cargo del firmante | Solo en resoluciones |
| **GESTIÓN (FANDIT INTERNO)** |||||
| Gestores asignados | ❌ N/A | Fandit | Sistema interno de Fandit | No en API ni PDF oficial |

---

## ESTADÍSTICAS

| Categoría | Cantidad | Porcentaje |
|-----------|----------|------------|
| ✅ Campos directos API | 35 | 53% |
| 🔄 Campos inferidos API | 7 | 11% |
| ❌ Solo en PDFs | 22 | 33% |
| ❌ No disponible | 2 | 3% |
| **TOTAL** | **66** | **100%** |

---

## DESGLOSE POR CRITICIDAD

### 🔴 CRÍTICO - Solo en PDF (necesario para aplicar)
1. Gastos subvencionables detallados
2. Forma de justificación
3. Plazo de justificación
4. Compatibilidad con otras ayudas
5. Garantías requeridas
6. Plazo de ejecución del proyecto
7. Forma de pago
8. Requisitos de publicidad

### 🟡 IMPORTANTE - Solo en PDF (útil para planificar)
1. Finalidad detallada
2. Actividades elegibles específicas
3. Cuantía individual (en resoluciones)
4. Presupuesto min/max del proyecto
5. Reglas de subcontratación
6. Modificaciones permitidas
7. Aplicación presupuestaria

### 🟢 OPCIONAL - Solo en PDF
1. Beneficiario específico (nombre/CIF)
2. CSV de verificación
3. Firmantes

---

## IMPLICACIONES PARA EL SISTEMA

### Para búsqueda y filtrado: ✅ API suficiente
- Filtrar por organismo, sector, tipo, beneficiarios, región, fechas
- Mostrar resultados con datos básicos

### Para consultas detalladas: ❌ PDFs necesarios
**Preguntas que requieren PDFs:**
- "¿Qué gastos puedo incluir?"
- "¿Cuándo tengo que justificar?"
- "¿Qué documentos necesito presentar?"
- "¿Puedo combinar con otras ayudas?"
- "¿Cómo me pagarán?"
- "¿Necesito presentar garantías?"

**Preguntas que responde la API:**
- "¿Qué ayudas hay abiertas para PYMES?"
- "¿Cuál es el presupuesto total?"
- "¿Quién convoca esto?"
- "¿Hasta cuándo puedo aplicar?"
- "¿Qué sectores cubre?"

---

## ARQUITECTURA RECOMENDADA

```
┌─────────────────────────────────────────────────┐
│          CAPA DE BÚSQUEDA Y FILTRADO            │
│              (API InfoSubvenciones)             │
│  - Filtros por organismo, sector, beneficiario  │
│  - Fechas, presupuesto, región                  │
│  - Resultados paginados                         │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│          CAPA DE DETALLE ESTRUCTURADO           │
│              (API + Inferencias)                │
│  - Metadatos completos                          │
│  - Clasificaciones automáticas                  │
│  - Links a bases reguladoras                    │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│     CAPA DE CONTENIDO DETALLADO (PDFs)          │
│         (Descarga + Parsing + RAG)              │
│  - Gastos subvencionables                       │
│  - Requisitos de justificación                  │
│  - Plazos de ejecución                          │
│  - Procedimientos                               │
│  - Búsqueda semántica en texto completo         │
└─────────────────────────────────────────────────┘
```

---

## ENDPOINTS DE LA API

```
BASE: https://www.infosubvenciones.es/bdnstrans/api

1. Búsqueda
GET /convocatorias/busqueda?abierto=true&finalidad=11&tiposBeneficiario=3,2&page=0&size=100

2. Detalle
GET /convocatorias?numConv={numeroConvocatoria}

3. Documento PDF
GET /convocatorias/documentos?idDocumento={idDocumento}

4. PDF completo generado
GET /convocatorias/pdf?id={idConvocatoria}&vpd=GE
```

---

**Última actualización**: 2025-11-30  
**Proyecto**: D:\IT workspace\infosubvenciones-api  
**Ubicación**: D:\IT workspace\infosubvenciones-api\info\api_fields_complete_classification.md
