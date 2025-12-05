# 📚 Documentación del Proyecto InfoSubvenciones API

## 📍 Ubicación del Proyecto
```
D:\IT workspace\infosubvenciones-api
```

---

## 📁 Estructura de Documentación

### 🔵 Documentos de Análisis de Campos API

| Documento | Ubicación | Descripción |
|-----------|-----------|-------------|
| **Clasificación Completa** | `info/api_fields_complete_classification.md` | ✅ **PRINCIPAL** - Tabla completa con API + PDF fields, fuentes, y clasificación |
| **Necesidades Cliente** | `info/customer_needs.md` | Requisitos originales de Artisting |
| **Estimación Tokens** | `info/TOKEN_ESTIMATION_SUMMARY.md` | Análisis de costos y tokens |

### 🔵 Scripts de Extracción

| Script | Ubicación | Propósito |
|--------|-----------|-----------|
| **Download PDFs** | `download_main_pdfs.py` | Descarga PDFs principales de convocatorias |
| **Export to Excel** | `export_to_excel.py` | Exporta resultados a Excel |
| **Summarize & Embed** | `summarize_and_embed.py` | Genera resúmenes y embeddings |
| **Calculate Tokens** | `calculate_token_estimate.py` | Estima costos de procesamiento |

### 🔵 Análisis de Costos

| Documento | Ubicación | Descripción |
|-----------|-----------|-------------|
| **Final Cost Analysis** | `FINAL_COST_ANALYSIS.md` | Análisis final de costos |
| **Model Cost Comparison** | `MODEL_COST_COMPARISON.md` | Comparación entre modelos LLM |
| **Calculation Verification** | `CALCULATION_VERIFICATION.md` | Verificación de cálculos |

### 🔵 Resultados y Outputs

| Carpeta/Archivo | Ubicación | Contenido |
|----------------|-----------|-----------|
| **Outputs** | `outputs/` | JSONs con embeddings y resúmenes |
| **Downloads** | `downloads/` | PDFs descargados (vacío actualmente) |
| **Sample PDFs** | Raíz del proyecto | `sample_871838_1362058.pdf` (ejemplo) |

---

## 🎯 Documento Principal: Clasificación Completa de Campos

**Ubicación**: [`info/api_fields_complete_classification.md`](./api_fields_complete_classification.md)

### ¿Qué contiene?

1. **Tabla Completa de 66+ campos** clasificados por:
   - ✅ **Campos directos API** (35 campos)
   - 🔄 **Campos inferidos API** (7 campos)
   - ❌ **Solo disponibles en PDFs** (22 campos)
   - ❌ **No disponibles** (2 campos)

2. **Columnas de la tabla**:
   - Requisito del Cliente
   - Disponibilidad (directo/inferido/PDF/N/A)
   - Fuente (API/PDF/otro)
   - Campo/Lógica (nombre del campo API o lógica de inferencia)
   - Notas

3. **Secciones organizadas por**:
   - Organismo convocante
   - Sector económico
   - Tipo de ayuda
   - Gastos y requisitos
   - Fondos
   - Beneficiarios
   - Ámbito geográfico
   - Información económica
   - Plazos y fechas
   - Descripción y bases
   - Objetivos
   - Procedimiento y cumplimiento
   - Documentación
   - Metadatos técnicos

4. **Estadísticas y desglose por criticidad**

5. **Arquitectura recomendada** para implementación

6. **Endpoints de la API** documentados

---

## 🔍 Campos Descubiertos en la API

### Campos Directos (extraídos de la API)

```json
{
  "id": 1073399,
  "organo": {
    "nivel1": "ESTADO",
    "nivel2": "MINISTERIO DE CULTURA",
    "nivel3": "DIRECCIÓN GENERAL DE PATRIMONIO CULTURAL Y BELLAS ARTES"
  },
  "numeroConvocatoria": "871838",
  "codigoBDNS": "871838",
  "fechaRecepcion": "2025-11-28",
  "instrumentos": [{"descripcion": "SUBVENCIÓN Y ENTREGA DINERARIA..."}],
  "tipoConvocatoria": "Concesión directa - instrumental",
  "presupuestoTotal": 653000,
  "descripcion": "SUBVENCIÓN DIRECTA A LA REAL ACADEMIA...",
  "tiposBeneficiarios": [{"descripcion": "PERSONAS JURÍDICAS..."}],
  "sectores": [{"codigo": "R", "descripcion": "ACTIVIDADES ARTÍSTICAS..."}],
  "regiones": [{"descripcion": "ES300 - Madrid"}],
  "descripcionFinalidad": "Cultura",
  "urlBasesReguladoras": "https://www.boe.es/...",
  "abierto": false,
  "fechaInicioSolicitud": "2025-07-24",
  "fechaFinSolicitud": "2025-08-14",
  "fondos": [{"descripcion": "FEDER..."}],
  "objetivos": [{"descripcion": "..."}],
  "documentos": [{
    "id": 1362058,
    "descripcion": "RESOLUCIÓN...",
    "nombreFic": "report_RESOLUCION.pdf",
    "long": 279827,
    "datMod": "2025-11-28"
  }]
}
```

### Campos Solo en PDFs (requieren parsing)

**Críticos para aplicar**:
- Gastos subvencionables detallados
- Forma de justificación
- Plazo de justificación
- Compatibilidad con otras ayudas
- Garantías requeridas
- Plazo de ejecución del proyecto
- Forma de pago
- Requisitos de publicidad

---

## 📡 Endpoints de la API

### Base URL
```
https://www.infosubvenciones.es/bdnstrans/api
```

### 1. Búsqueda de convocatorias
```
GET /convocatorias/busqueda

Parámetros:
- abierto: true/false
- finalidad: 11 (Cultura), 14 (Comercio)
- tiposBeneficiario: 2,3 (personas físicas, PYMES)
- page: 0
- size: 100
```

### 2. Detalle de convocatoria
```
GET /convocatorias?numConv={numeroConvocatoria}
```

### 3. Descargar documento
```
GET /convocatorias/documentos?idDocumento={idDocumento}
```

### 4. PDF completo generado
```
GET /convocatorias/pdf?id={idConvocatoria}&vpd=GE
```

---

## 🎨 Interface/Frontend

**Ubicación**: `interface/`

Proyecto React/Vite con componentes para visualización de subvenciones.

Ver: `interface/README.md`

---

## 📊 Datos de Ejemplo

### Convocatoria de prueba descargada
- **Número**: 871838
- **PDF**: `sample_871838_1362058.pdf` (273 KB)
- **Tipo**: Resolución de concesión
- **Organismo**: MINISTERIO DE CULTURA
- **Beneficiario**: REAL ACADEMIA DE BELLAS ARTES DE SAN FERNANDO
- **Cuantía**: 653.000 €

---

## 🔗 Referencias Útiles

- **Portal InfoSubvenciones**: https://www.infosubvenciones.es/bdnstrans/
- **API Base**: https://www.infosubvenciones.es/bdnstrans/api
- **Fandit (competidor)**: Análisis en `Fandit.pdf`

---

## 📝 Próximos Pasos

1. ✅ Análisis completo de campos API vs PDF
2. ⏳ Implementar parsing de PDFs para extraer campos críticos
3. ⏳ Crear sistema RAG para búsqueda semántica
4. ⏳ Integrar con interfaz de usuario

---

**Última actualización**: 2025-11-30
