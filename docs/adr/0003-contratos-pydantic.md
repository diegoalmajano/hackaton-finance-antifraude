# ADR-0003: Contratos Pydantic v2 como fuente única

**Fecha**: 2026-11-08
**Estado**: accepted (D-26)
**Decisores**: usuario · Claude Code (propuesta)

## Contexto
Varios paquetes intercambian mensajes, señales, evidencias y evaluaciones; las divergencias de formato son una fuente típica de fallos de integración.

## Decisión
Los modelos Pydantic v2 de `contracts` son la **única definición** de los datos (base: `docs/contexto/13` §4). Como la UI es HTML + Jinja + htmx (ADR-0012), **no se generan tipos TypeScript**. Para el MVP los contratos se reducen a lo necesario (`custom_rules`, `attachments_meta` y `ConsentContext` mínimos). `CheckResult.status` incluye `not_configured` (ADR-0006).

## Alternativas consideradas
### Dataclasses / dicts
- **Por qué no**: sin validación ni serialización robusta.
### TS generado desde OpenAPI
- **Por qué no**: innecesario sin frontend en TypeScript.

## Consecuencias
### Positivas
- Validación en las fronteras (también de la salida del LLM).
### Negativas
- Cambiar un contrato obliga a actualizar sus tests.
### Riesgos
- Contratos inflados → solo campos usados por la demo; ampliar después.
