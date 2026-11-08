# ADR-0006: Motor de riesgo determinista con 4 niveles y estados de comprobación

**Fecha**: 2026-11-08
**Estado**: accepted (D-26, D-29)
**Decisores**: usuario · Claude Code (propuesta)

## Contexto
D-14 exige BAJO / MEDIO / ALTO / NO CONCLUYENTE sin porcentajes, y que un error nunca dé BAJO. La política inicial (`13` §6.1) trataba igual una comprobación **no configurada** que una **fallida**, de modo que sin RDAP/reputación cualquier enlace no oficial acababa en NO CONCLUYENTE (también en mensajes legítimos). Además, un dominio aparentemente oficial que pide OTP se clasificaba como NO CONCLUYENTE.

## Decisión
1. La decisión final la toma un **motor determinista** (`risk`); el LLM solo aporta evidencias con citas verificadas.
2. Cada comprobación tiene estado **`done` | `failed` | `not_configured`** (además de `skipped`/`not_applicable`). Solo las **obligatorias** que han **fallado** generan incertidumbre que impide BAJO. Las `not_configured` se declaran en «lo que no se pudo comprobar», pero **no fuerzan NO CONCLUYENTE**.
3. Comprobaciones obligatorias del MVP: filtro por reglas, análisis pasivo de todas las URLs y análisis IA cuando el filtro escala. RDAP y reputación son complementarias.
4. **Una petición de credenciales, contraseñas, PIN, códigos OTP o datos de tarjeta nunca se considera segura por proceder aparentemente de un dominio oficial**: nivel **mínimo MEDIO** (ALTO si se suma otra evidencia crítica), con la recomendación de verificar por el canal oficial del directorio.
5. Errores → NO CONCLUYENTE o el nivel que justifiquen las evidencias existentes, **nunca BAJO**; análisis parcial declarado.

## Alternativas consideradas
### Puntuación numérica / probabilidad
- **Por qué no**: sin datos de calibración (D-14).
### Decisión final del LLM
- **Por qué no**: vulnerable a prompt injection y no reproducible.

## Consecuencias
### Positivas
- Clasificación reproducible, testeable con tabla de decisión y explicable al jurado.
### Negativas
- Las reglas requieren ajuste manual (solo con el conjunto dev).
### Riesgos
- Falsos positivos en legítimos urgentes → casos legítimos en el banco de evaluación y ensayo de los 3 casos de demo.
