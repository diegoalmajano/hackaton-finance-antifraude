# ADR-0009: Reputación de URLs opcional y complementaria

**Fecha**: 2026-11-08
**Estado**: accepted (D-26, D-31)
**Decisores**: usuario · Claude Code (propuesta)

## Contexto
Google Web Risk permite uso comercial pero probablemente exige facturación (V-16); Safe Browsing v5 es gratuito pero **solo no comercial**; el producto es B2B. VirusTotal público y urlscan no son aptos.

## Decisión
La reputación se implementa **detrás de una interfaz opcional**. La defensa principal es el análisis pasivo propio (ADR-0005) y el directorio de entidades. Si no hay proveedor configurado, la comprobación queda en `not_configured` y **no bloquea la clasificación** (ADR-0006). Si se configura en el prototipo: Web Risk si se habilita sin coste; si no, Safe Browsing v5 declarando su uso no comercial.

## Alternativas consideradas
### Reputación obligatoria
- **Por qué no**: la demo dependería de una clave externa y de facturación.
### VirusTotal / urlscan
- **Por qué no**: licencia y privacidad (`12`).

## Consecuencias
### Positivas
- La clasificación funciona sin servicios externos.
### Negativas
- Sin reputación, se pierden detecciones de URLs ya conocidas.
### Riesgos
- Afirmar en la presentación un uso comercial no permitido → declarar el uso no comercial del prototipo.

## Pendiente de verificar (⏳)
- Requisitos de facturación de Web Risk (V-16) · términos vigentes de Safe Browsing v5.
