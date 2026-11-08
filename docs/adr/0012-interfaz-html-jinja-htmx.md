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

## Implementación F0-06 (2026-11-08)
htmx 2.0.11 desde `vendor/htmx/` (ruta `/vendor/htmx/htmx.min.js`). Incompatibilidades detectadas por inspección de `htmx.min.js` y neutralizadas con `<meta name="htmx-config">` (D-47): inserta un `<style>` en línea para los indicadores (`includeIndicatorStyles` → `false`; los indicadores se definen en `app.css`); usa `eval`/`new Function` para `hx-on`, `js:` y `hx-vars` (`allowEval` → `false`; esos atributos no se usan); guarda copias de página en `sessionStorage` para el historial (`historyEnabled` → `false`, `historyCacheSize` → `0`). Aún escribe en `sessionStorage` la clave `htmx-current-path-for-history` (solo la ruta, sin datos). **Pendiente:** confirmarlo en un navegador real (V-26).
