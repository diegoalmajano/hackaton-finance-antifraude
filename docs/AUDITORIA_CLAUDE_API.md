# Auditoría de la integración con la API de Claude (2026-11-08)

> Revisión **estática** de `backend/antifraude/ai/{claude,prompt,base}.py` frente a la documentación oficial incluida en la skill `claude-api` (referencias Python y compartidas, caché de 2026-10-06). **No se ha hecho ninguna llamada real** (sin SDK instalado ni presupuesto aprobado). Lo que depende de una llamada real queda **pendiente de verificar**.

## Conforme con la documentación
| Punto | Implementación |
|---|---|
| SDK oficial, no HTTP propio | `sdk_transport` usa `anthropic.Anthropic(...).beta.messages.create`; import diferido. Si no está instalado → IA «no configurada» |
| Salida estructurada | `output_config.format = {"type": "json_schema", "schema": …}`, todos los objetos con `additionalProperties: false` y todos los campos en `required` |
| Esquema solo con construcciones soportadas | tipos básicos, `enum`, `anyOf` con `null` (corregido en esta auditoría); sin `minLength`/`maxLength`/`minimum` (los límites se aplican al validar con Pydantic) |
| Parámetros prohibidos en Opus 5.5 / Sonnet 5.5 | no se envían `temperature`, `top_p`, `top_k`, `thinking: disabled`, `budget_tokens` ni `tool_choice` forzado |
| Esfuerzo | `output_config.effort = "low"` explícito (Opus 5.5 usa `medium` por defecto); se ajustará con la comparativa medida |
| Rechazos | `stop_reason == "refusal"` se comprueba antes de leer el contenido → `failed/refusal`, nunca BAJO |
| `max_tokens` | `stop_reason == "max_tokens"` → `failed/invalid_output`. Límite subido de 4 000 a 16 000 (el razonamiento consume salida) |
| Fallback ante rechazos | `fallbacks: "default"` + beta `server-side-fallback-2026-07-01`; se registra `response.model` (el modelo que respondió realmente) |
| Contenido de la respuesta | solo se leen bloques `text` (se ignoran `thinking` y `fallback`) |
| Errores y tiempo de espera | `anthropic.APITimeoutError` → `timeout`; cualquier otra excepción → `api_error`; nunca se registra contenido |
| Clave | se lee de `ANTHROPIC_API_KEY` (SecretStr), no aparece en reprs ni errores |
| Defensas de prompt injection | instrucciones solo en `system`; mensaje como datos con delimitador aleatorio; sin herramientas ni red para el modelo; citas verificadas como subcadena; decisión final determinista |

## Pendiente de verificar con el SDK instalado y una llamada real (V-19)
1. Que el SDK de Python acepte `fallbacks="default"` como argumento de `beta.messages.create`. La documentación muestra la forma de lista. Si no lo acepta, el código reintenta enviándolo en `extra_body`.
2. Que el esquema con `anyOf` + `null` compile sin errores. La primera petición tiene un coste de compilación; después queda en caché 24 h.
3. **Caché del prompt:** el *system prompt* (unos 600 tokens) podría estar **por debajo del mínimo cacheable** del modelo (entre 512 y 4096 tokens según el modelo). En ese caso no se cachea, y lo indicaría `usage.cache_read_input_tokens = 0`. Es una mejora de coste, no de corrección.
4. Rechazos reales con contenido de phishing (V-17), latencia y coste por mensaje (D-32): solo con presupuesto autorizado.
5. Términos de retención y uso de datos de Anthropic (V-14) antes de afirmarlos en la presentación.

## Cómo activarla cuando se autorice
1. Instalar el SDK oficial (versión fijada en `requirements.txt` y licencia registrada en `docs/DEPENDENCIAS.md`).
2. En la consola:
   ```powershell
   $env:ANTHROPIC_API_KEY = Read-Host "Clave" -MaskInput
   $env:CLAUDE_MODEL = "claude-sonnet-5-5"   # o claude-opus-5-5
   ```
3. Ejecutar primero la comparativa sobre el conjunto de desarrollo, con límite de gasto en la consola de Anthropic.
