# ADR-0010: Voz aplazada; `InputAdapter` común

**Fecha**: 2026-11-08
**Estado**: accepted (D-26)
**Decisores**: usuario · Claude Code (propuesta)

## Contexto
D-12: voz, llamadas y audio son fase 2, sin código ni dependencias.

## Decisión
Solo existe una interfaz `InputAdapter` común a los conectores (manual, simulado, Gmail) y el valor reservado `voice_transcript` en `Channel`. **No se construye nada más** relacionado con voz.

## Alternativas consideradas
### Prototipo de voz
- **Por qué no**: fuera de alcance (D-12); el riesgo en el criterio de IA frontera está aceptado.

## Consecuencias
### Positivas
- Un futuro módulo de voz reutiliza el motor sin rehacerlo.
### Negativas
- El 15 % de IA frontera se defiende sin audio (riesgo aceptado).
### Riesgos
- Ninguno técnico relevante.
