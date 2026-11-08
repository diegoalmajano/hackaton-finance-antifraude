# ADR-0005: Enlaces — análisis estrictamente pasivo

**Fecha**: 2026-11-08
**Estado**: accepted (D-26, D-31)
**Decisores**: usuario · Claude Code (propuesta)

## Contexto
D-11 y D-21 prohíben abrir enlaces sospechosos sin aislamiento robusto, que no se puede garantizar en el plazo.

## Decisión
Análisis **estrictamente pasivo**: normalización, dominio registrable con Public Suffix List **local**, subdominios con marca, punycode/confusables, similitud con dominios oficiales del directorio, discrepancia texto visible/`href`, acortadores, IP literal, puerto no estándar. **No se visita ninguna URL, no se resuelven por DNS los dominios sospechosos y no se siguen acortadores** (destino desconocido = incertidumbre). RDAP (consulta al registro, no a la web) y reputación son **complementarios** y nunca bloquean la clasificación (ADR-0006, ADR-0009).

## Alternativas consideradas
### Inspección activa en sandbox
- **Por qué no**: exige aislamiento SSRF/DNS rebinding robusto; queda en P2.
### Resolver DNS para obtener IP/ASN
- **Por qué no**: la consulta llega a infraestructura controlada por el atacante y puede alertarle.

## Consecuencias
### Positivas
- Cero contacto con la infraestructura del atacante; resultados reproducibles y testeables sin red.
### Negativas
- No se conoce el destino real de acortadores ni el contenido de la página.
### Riesgos
- Menor detección en enlaces «limpios» → lo compensa el análisis de contenido con IA y la correlación.

## Pendiente de verificar (⏳)
- Disponibilidad de **RDAP para dominios `.es`** (V-18).
