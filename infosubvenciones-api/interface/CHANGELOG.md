# Changelog - Interface

## [2025-11-25] - Rediseño Completo

### Added
- **Diseño minimalista moderno**: Inspirado en referencias de diseño limpio y profesional
- **Layout vertical mejorado**: Stack de Filtros → Chat → PDF para mejor aprovechamiento del espacio
- **Filtros organizados por secciones**:
  - Header con título "Filtros de búsqueda" y descripción
  - Sección "Filtros básicos" (Región, Beneficiario, Sector)
  - Sección "Plazo de solicitud" con explicación de uso
  - Sección "Cuantía de la ayuda" en euros
  - Sección "Atajos rápidos" con chips predefinidos
  - Box destacado mostrando filtros activos
- **Labels y descripciones claras**: Cada input tiene label descriptivo y placeholders útiles
- **Branding "Artisting"**: Texto "Diseñado para Artisting" en header superior derecho
- **Footer con créditos**: "Desarrollado por cristianjrojas@gmail.com"
- **Backups de diseño anterior**: Archivos `.backup` para recuperar diseño previo

### Changed
- **Paleta de colores**: De gradiente púrpura-azul a diseño minimalista gris/blanco/negro
- **Tipografía**: Mayor énfasis en jerarquía visual con diferentes tamaños y pesos
- **Posición del botón "Resetear chat"**: Movido de header a esquina inferior izquierda del chat
- **Layout de mensajes**: User messages (negro, derecha), Assistant messages (gris claro, izquierda)
- **Altura del chat**: Definida entre 400-600px con scroll
- **PDF Viewer**: Aumentado a 700px de altura, full-width

### Fixed
- **Encoding de caracteres**: Corregida codificación UTF-8 en App.tsx para mostrar correctamente caracteres españoles (é, á, ñ, etc.)
- **Legibilidad**: Mejores contrastes, tamaños de fuente más grandes, mejor espaciado

### Technical
- **Dependencies**: Instalado @types/uuid para TypeScript
- **Development server**: Configurado en puerto 5173 con --host
- **CSS Grid layout**: Implementado para composer (reset button, textarea, send button)
- **Responsive design**: Breakpoints en 1024px y 640px

## Estructura de archivos

```
interface/
├── src/
│   ├── App.tsx              # Componente principal con nueva estructura
│   ├── App.tsx.backup       # Backup del diseño anterior
│   ├── styles.css           # Estilos minimalistas actuales
│   ├── styles.css.backup    # Backup de estilos anteriores
│   ├── types.ts             # Definiciones de TypeScript
│   ├── config.ts            # Configuración de entorno
│   └── main.tsx             # Entry point
├── TODO.md                  # Tareas completadas y pendientes (actualizado)
├── CHANGELOG.md             # Este archivo
├── README.md                # Documentación de uso
└── package.json             # Dependencies con @types/uuid
```

## Cómo restaurar el diseño anterior

Si necesitas volver al diseño con gradiente púrpura-azul:

```bash
cd interface/src
cp App.tsx.backup App.tsx
cp styles.css.backup styles.css
```

El servidor de desarrollo recargará automáticamente los cambios.
