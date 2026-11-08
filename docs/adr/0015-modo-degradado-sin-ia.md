# ADR-0015: Modo degradado etiquetado sin IA

**Fecha**: 2026-11-08
**Estado**: accepted (D-26, D-37)
**Decisores**: usuario · Claude Code (propuesta)

## Contexto
La demo puede sufrir caída de red, de la API de Anthropic, falta de clave o refusals. Nunca se puede presentar algo simulado o pregrabado como real.

## Decisión
Si la IA no está disponible (sin clave, error, timeout, refusal), el sistema sigue analizando con **reglas + análisis técnico de enlaces**, marca la comprobación IA como `failed` o `not_configured`, declara **«análisis parcial — IA no disponible»** de forma visible en la UI y en la evaluación, y aplica ADR-0006 (nunca BAJO por error). Los conectores simulados y los resultados de ejemplo se etiquetan siempre como **SIMULADO**. Nada pregrabado se presenta como ejecución real.

## Alternativas consideradas
### Respuestas de IA pregrabadas
- **Por qué no**: prohibido (presentar simulado como real).
### Bloquear el análisis sin IA
- **Por qué no**: el usuario se quedaría sin protección básica.

## Consecuencias
### Positivas
- La demo sobrevive a fallos externos de forma honesta.
### Negativas
- Menor capacidad de detección en modo degradado.
### Riesgos
- Que el usuario no note el modo degradado → etiqueta visible con texto + icono.
