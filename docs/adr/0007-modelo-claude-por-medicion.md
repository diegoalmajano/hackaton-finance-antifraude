# ADR-0007: Modelo de Claude elegido por medición (pendiente)

**Fecha**: 2026-11-08
**Estado**: accepted (D-26, D-32) — **la elección del modelo sigue PENDIENTE (D-24)**
**Decisores**: usuario · Claude Code (propuesta)

## Contexto
D-24 deja pendiente la elección entre `claude-opus-5-5` y `claude-sonnet-5-5`. Hace falta un procedimiento para decidir sin fijar ninguno antes de tiempo.

## Decisión
- El identificador del modelo es **configuración** (sin valor por defecto decidido en código ni documentos).
- Durante el desarrollo se usa un **cliente Claude simulado** (mocks).
- La elección se hará con una **prueba comparativa** sobre un subconjunto del conjunto dev con ambos modelos, midiendo **calidad** (detección, evidencias, citas válidas, refusals), **coste** (`usage`) y **latencia** (p50/p95), **solo con presupuesto autorizado** por el usuario. Decide el usuario.
- El filtro es por reglas; Haiku 5.5 solo si se mide valor.

## Alternativas consideradas
### Fijar Sonnet u Opus ahora
- **Por qué no**: contradice D-24; sin datos.

## Consecuencias
### Positivas
- Decisión basada en datos y argumentable en la presentación (coste por análisis para el modelo B2B).
### Negativas
- Requiere un gasto pequeño de API y tiempo de medición.
### Riesgos
- Refusals con contenido de phishing → `ai_status=failed`, nunca BAJO (ADR-0006, ADR-0015).

## Pendiente de verificar (⏳)
- Parámetros actuales de la API (salida estructurada, `stop_reason: "refusal"`, *fallbacks*, temperatura, `effort`, caché de prompts) en la documentación oficial al implementar (V-19) · términos de retención/entrenamiento de Anthropic (V-14) · refusals medidos (V-17).
