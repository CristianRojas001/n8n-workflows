# Web Interface To-Do

## Completado
- [x] Estructura base Vite + React + TypeScript en `interface/` (package.json, tsconfig, vite.config, index.html).
- [x] UI principal: chat con filtros y presets, barra de estado por etapas, badges de modelo/latencia/última actualización, compositor fijo, chips de citas, lista de convocatorias con acciones `Ver PDF`/`Descargar`, panel/drawer de PDF, botón de reset de chat.
- [x] Tipos y config: `src/types.ts`, `src/config.ts` para contrato con n8n y lectura de env.
- [x] Estilos modernos en `src/styles.css` con diseño minimalista (colores, radios, sombras, responsivo).
- [x] Entorno y docs: `.env.example` y `README.md` con instrucciones de ejecución y nota de no abrir `index.html` por file://.
- [x] **Instalación de dependencias y servidor de desarrollo** - Dependencias instaladas y servidor corriendo en puerto 5173
- [x] **Rediseño completo de la interfaz** - Diseño minimalista inspirado en referencias modernas
- [x] **Mejora de filtros** - Filtros organizados por secciones con labels claros y descripciones
- [x] **Layout vertical mejorado** - Estructura: Filtros → Chat → PDF (stacked verticalmente para mejor uso del espacio)
- [x] **Branding** - Agregado "Diseñado para Artisting" en header superior derecho
- [x] **Reubicación del botón reset** - Movido a esquina inferior izquierda del chat
- [x] **Footer con créditos** - Agregado "Desarrollado por cristianjrojas@gmail.com"
- [x] **Backups de diseño** - Creados `App.tsx.backup` y `styles.css.backup` con diseño anterior

## Diseño actual (25/Nov/2025)

### Características del diseño
- **Paleta de colores**: Minimalista con fondo gris claro (#f5f5f5), paneles blancos, texto negro (#1a1a1a)
- **Layout**: Vertical stack (Filtros → Chat → PDF) en lugar de columnas side-by-side
- **Tipografía**: Manrope font, headers bold, texto limpio y legible
- **Filtros mejorados**:
  - Sección "Filtros básicos": Región, Beneficiario, Sector
  - Sección "Plazo de solicitud": Fechas con explicación clara
  - Sección "Cuantía de la ayuda": Mínimo y máximo en euros
  - Sección "Atajos rápidos": Chips predefinidos
  - Box destacado con filtros activos
- **Chat**:
  - Mensajes de usuario (negro) alineados a la derecha
  - Mensajes del asistente (gris claro) alineados a la izquierda
  - Altura scrollable: 400-600px
- **PDF Viewer**: 700px de altura, full-width
- **Responsivo**: Adapta a mobile con filtros en columna única

## Por hacer (ejecutar y conectar)
- [ ] Crear `.env.local` a partir de `.env.example` con `VITE_AGENT_ENDPOINT`, `VITE_AGENT_BASIC_AUTH_USER`, `VITE_AGENT_BASIC_AUTH_PASS`, `VITE_AGENT_TIMEOUT_MS`, `VITE_APP_LAST_UPDATED`.
- [ ] Probar round-trip contra n8n: envío de mensaje + filtros → respuesta con answer, citas y convocatorias; confirmar que los links `Ver PDF`/`Descargar` funcionan.

## Integración n8n y PDFs
- [ ] Configurar CORS en el webhook de n8n para el dominio del frontend.
- [ ] Asegurar Basic Auth en el webhook (coincide con env del frontend).
- [ ] Definir si n8n devuelve `pdfUrl` directo o proxificado para vista (si CORS bloquea embed); mantener link directo para descarga.
- [ ] Confirmar timeouts y códigos de error: 400/429/500 con payload `{ error: { code, message, stage, retryAfter? } }`.

## Autenticación y acceso
- [ ] (Opcional) Añadir Google Sign-In o proteger front-door con IAP/SSO; asegurar que el token o sesión sea compatible con el webhook.
- [ ] (Opcional) Limitar origen: bloquear acceso público si es solo interno.

## UX/fiabilidad
- [ ] Mejorar manejo de errores/avisos: toasts o mensajes claros para 429 y timeouts.
- [ ] (Opcional) Sustituir `<object>` por pdf.js para mejor navegación/resaltado.
- [ ] (Opcional) Mostrar historial si n8n expone últimas N consultas por usuario.
- [ ] (Opcional) Añadir skeletons/toasts adicionales según feedback de uso real.

## Validación
- [ ] Comprobar que los presets de filtros aplican correctamente (Autónomos, PYMES, Cultura 11, Comercio 14, Próx. 30 días).
- [ ] Revisar formatos: fechas DD/MM/AAAA, moneda en euros, textos en español.
- [ ] Verificar responsivo: mobile con layout apilado y filtros en columna única.

## Notas de desarrollo
- **Servidor de desarrollo**: `npm run dev -- --host --port 5173` en directorio `interface/`
- **Backups**: Diseños anteriores guardados en `src/App.tsx.backup` y `src/styles.css.backup`
- **Restaurar diseño anterior**: Copiar los archivos .backup sobre los originales
