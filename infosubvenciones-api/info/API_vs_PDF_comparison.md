# API vs PDF - Comparación Detallada del Campo "descripcion"

## 📊 Resumen Ejecutivo

| Fuente | Caracteres | Contenido |
|--------|-----------|-----------|
| **API - descripcion** | 247 | Solo título de la convocatoria |
| **PDF Completo** | 12,075 | Documento completo con todos los detalles |
| **Diferencia** | 11,828 (98%) | **Casi todo el contenido crítico está SOLO en el PDF** |

---

## 🔍 Qué Obtienes de Cada Fuente

### ✅ API - Campo `descripcion` (247 caracteres)

**Contenido exacto**:
```
SUBVENCIÓN DIRECTA A LA REAL ACADEMIA DE BELLAS ARTES DE SAN FERNANDO 
POR REAL DECRETO 662/2025, DE 22 DE JULIO, POR EL QUE SE REGULA LA 
CONCESIÓN DIRECTA DE SUBVENCIONES A ENTIDADES RELACIONADAS CON EL 
PATRIMONIO CULTURAL Y LAS BELLAS ARTES, 2O25
```

**Qué te dice**:
- Título de la convocatoria
- Beneficiario (en este caso específico, pero no siempre)
- Referencia legal (Real Decreto)
- Año

**Qué NO te dice**:
- ❌ Cuantía específica
- ❌ Gastos elegibles
- ❌ Plazos
- ❌ Requisitos
- ❌ Procedimientos
- ❌ Nada operativo

---

### ✅ PDF Completo (12,075 caracteres)

**Contenido que SOLO está en el PDF**:

#### 1. **Beneficiario Específico** ❌ NO en API
```
Beneficiario y CIF:
REAL ACADEMIA DE BELLAS ARTES DE SAN FERNANDO
Q-2868013-J
```

#### 2. **Aplicación Presupuestaria** ❌ NO en API
```
Aplicación presupuestaria:
24.05.333A.485.48
```

#### 3. **Finalidad Detallada** ❌ NO en API
```
Finalidad:
Financiar las actividades y gastos de funcionamiento de la institución.
```
- API solo tiene: "Cultura" (genérico)
- PDF tiene: propósito específico

#### 4. **Gastos Subvencionables Detallados** ❌ NO en API
```
Gastos o partidas subvencionables:
Se considerarán subvencionables las siguientes partidas:
- Servicio de vigilancia de seguridad y de control de accesos
- Servicio de atención a los visitantes y vigilancia de salas
- Gastos de mantenimiento ordinario de la climatización
- Gastos de iluminación del museo y salas de exposiciones
```
- **Crítico para aplicantes**: necesitan saber qué gastos pueden reclamar

#### 5. **Cuantía Exacta** ⚠️ Parcial en API
```
Cuantía de la subvención:
653.000,00 euros
```
- API tiene: `presupuestoTotal: 653000` ✅
- Pero en resoluciones, este es el monto concedido individual
- En convocatorias, `presupuestoTotal` es el total del programa

#### 6. **Forma de Pago** ❌ NO en API
```
Forma de realización del pago:
- Libramiento único
- Por el importe total
- Con carácter anticipado
- Mediante transferencia
```

#### 7. **Exigencia de Garantía** ❌ NO en API
```
Exigencia de garantía:
No procede
```

#### 8. **Compatibilidad con Otras Ayudas** ❌ NO en API
```
Compatibilidad/incompatibilidad:
- Es compatible con otras subvenciones
- Para la misma finalidad
- No puede superar el coste de la actividad
```

#### 9. **Plazo de Ejecución** ❌ NO en API
```
Plazo para la realización:
Del 1 de enero al 31 de diciembre de 2025
```
- API tiene: `fechaInicioSolicitud` y `fechaFinSolicitud` (para aplicar)
- PDF tiene: plazo de ejecución del proyecto (diferente)

#### 10. **Plazo de Justificación** ❌ NO en API
```
Plazo de justificación:
Hasta el 31 de marzo de 2026
```

#### 11. **Forma de Justificación** ❌ NO en API
```
Forma de justificación:
a) Memoria de actuación
b) Memoria económica abreviada
c) Informe de auditor de cuentas
d) Relación de medios de publicidad
e) Carta de pago de remanentes
f) Listado de otros ingresos
```
- **Crítico**: sin esto, no sabes qué documentos presentar

#### 12. **Requisitos de Publicidad** ❌ NO en API
```
Publicidad:
- Deberá indicar en página web, folletos, carteles
- Que se realiza en colaboración con Ministerio de Cultura
- Debe incluir imagen institucional
- Incumplimiento = causa de reintegro
```

#### 13. **Subcontratación** ❌ NO en API
```
Subcontratación:
Se aplicará lo dispuesto en el art. 29 de la Ley 38/2003
```

#### 14. **Modificaciones Permitidas** ❌ NO en API
```
Modificaciones al proyecto inicial:
- Con carácter excepcional
- Solicitar antes de finalizar plazo
- A través de sede electrónica
- No dañar derechos de terceros
```

#### 15. **Recursos Legales** ❌ NO en API
```
Recursos:
- Recurso contencioso-administrativo ante Audiencia Nacional
- Plazo: 2 meses desde notificación
- O recurso de reposición en 1 mes
```

---

## 📋 Campos Adicionales en API

Además de `descripcion`, la API proporciona:

### ✅ Campos que SÍ están en API (además de descripcion)

| Campo API | Qué proporciona |
|-----------|-----------------|
| `presupuestoTotal` | Presupuesto total (€653,000) |
| `organo.nivel1/2/3` | Organismo convocante |
| `fechaInicioSolicitud` | Inicio plazo solicitudes |
| `fechaFinSolicitud` | Fin plazo solicitudes |
| `abierto` | Estado abierto/cerrado |
| `tiposBeneficiarios` | Tipos permitidos (genérico) |
| `sectores` | Sectores CNAE |
| `regiones` | Ámbito geográfico |
| `fondos` | Fondos europeos (si aplica) |
| `descripcionBasesReguladoras` | Nombre de la norma |
| `urlBasesReguladoras` | Link al BOE/BOJA |
| `documentos[]` | Lista de PDFs disponibles |

---

## 🎯 Análisis: ¿Qué Porcentaje de Información Está en la API?

### Información Básica de Búsqueda: ✅ 100% en API
- Quién convoca
- Para qué sector
- Cuándo aplicar
- Dónde aplica (región)
- Cuánto presupuesto total

### Información para Decidir Aplicar: ⚠️ ~30% en API
- ✅ Presupuesto (en API)
- ❌ Gastos elegibles (solo en PDF)
- ❌ Requisitos específicos (solo en PDF)
- ⚠️ Beneficiarios (tipo en API, nombre específico en PDF)

### Información para Completar la Aplicación: ❌ ~5% en API
- ❌ Documentos requeridos (solo en PDF)
- ❌ Plazos de ejecución (solo en PDF)
- ❌ Forma de pago (solo en PDF)
- ❌ Garantías (solo en PDF)

### Información para Cumplimiento: ❌ 0% en API
- ❌ Cómo justificar (solo en PDF)
- ❌ Cuándo justificar (solo en PDF)
- ❌ Requisitos de publicidad (solo en PDF)
- ❌ Reglas de subcontratación (solo en PDF)
- ❌ Procedimiento de modificaciones (solo en PDF)

---

## 💡 Conclusión

### El campo `descripcion` de la API es:
✅ **Útil para**: Identificar la convocatoria, búsqueda inicial
❌ **Insuficiente para**: Cualquier decisión u operación real

### El PDF es:
✅ **Esencial para**: 
- Decidir si aplicas
- Completar la solicitud
- Saber qué gastos puedes reclamar
- Cumplir con requisitos
- Justificar la subvención

### Proporción de Información Crítica:

```
API descripcion:         2%  ███
API otros campos:       18%  ████████████████████
PDF exclusivo:          80%  ████████████████████████████████████████████████████████████████████
                            Total información operativa
```

---

## 🚀 Implicación para tu Sistema

**Para un sistema tipo Fandit, NECESITAS**:

1. ✅ **API para búsqueda y filtrado** (20% de la info)
   - Listar convocatorias
   - Filtrar por criterios
   - Datos básicos

2. ✅ **PDFs parseados para todo lo demás** (80% de la info)
   - Detalles de aplicación
   - Requisitos
   - Procedimientos
   - Cumplimiento

**No puedes construir un sistema útil solo con la API** - los usuarios necesitan la información del PDF para:
- Saber si califican
- Entender qué pueden financiar
- Completar la solicitud
- Cumplir con los requisitos
- Justificar después

---

**Recomendación**: Implementar extracción de PDFs (con OCR + LLM) es CRÍTICO, no opcional.

