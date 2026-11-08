# ADR-0012: Interfaz HTML + Jinja + htmx

**Fecha**: 2026-11-08
**Estado**: accepted (D-26, D-35; resuelve T-01)
**Decisores**: usuario · Claude Code (propuesta)

## Contexto
Un solo desarrollador; la UI debe ser accesible para personas mayores (D-22) y ejecutarse desde el ZIP sin pasos de compilación.

## Decisión
UI renderizada en servidor con **plantillas Jinja2** y **htmx** para interacciones parciales y SSE. htmx (y su extensión SSE cuando haga falta) se **incluye como archivo local versionado** en el repo (sin CDN), con licencia verificada. Sin Node ni compilación. HTML semántico, `lang="es"`, foco visible, navegación por teclado, alto contraste, texto y botones grandes, riesgo con **texto + icono**.

## Alternativas consideradas
### React + TypeScript (Vite)
- **Contras**: segundo lenguaje, compilación, generación de tipos. **Por qué no**: coste para un solo desarrollador.

## Consecuencias
### Positivas
- Todo en Python; menos piezas; buena base de accesibilidad con HTML semántico.
### Negativas
- Interactividad rica más limitada que en un SPA.
### Riesgos
- Scripts en línea incompatibles con CSP estricta (ADR-0013) → sin JS en línea; configuración de htmx por atributos/archivo local.
