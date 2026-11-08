# Control de costes de la API de Claude

> Estado (2026-11-08): **implementado y probado solo con clientes simulados**. Gasto real de la aplicación en la API de Anthropic: **0 USD** (no se ha hecho ninguna llamada). Gasto **autorizado** por el usuario: **0 USD**.

## 1. Qué impide gastar sin querer
| Control | Cómo funciona | Por defecto |
|---|---|---|
| IA desactivada | Sin `AI_ENABLED=1` no se envía nada | Desactivada |
| Modelo explícito | `CLAUDE_MODEL` debe ser `claude-sonnet-5-5` o `claude-opus-5-5`; no hay modelo por defecto | Ninguno |
| Opus bloqueado | `claude-opus-5-5` exige además `AI_ALLOW_OPUS=1` | Bloqueado |
| Sin *fallback* a otros modelos | No se envía `fallbacks`. Un *fallback* repetiría la petición con otro modelo y se facturaría a su tarifa | Desactivado (sin opción para activarlo) |
| Sin reintentos automáticos | SDK con `max_retries=0` y la aplicación no reintenta. Un reintento podría pagar dos veces | 0 reintentos |
| Presupuesto autorizado | `AI_BUDGET_USD`. Con 0 la IA no se usa. Tope duro de 10 USD contra errores de tecleo | **0 USD** |
| Presupuesto **previsto** | 0,50 USD para las primeras pruebas con Sonnet (`PLANNED_INITIAL_BUDGET_USD`). **No está autorizado**: es solo una referencia | — |
| Límite de entrada | `AI_MAX_INPUT_TOKENS`. Si la estimación lo supera, no se envía y el análisis queda «parcial» | 6 000 |
| Límite de salida | `AI_MAX_OUTPUT_TOKENS` → `max_tokens` de la petición | 4 000 |
| Solicitudes por sesión | `AI_MAX_REQUESTS`, contadas por **instancia** del analizador. La aplicación y el ejecutor de la evaluación cuentan por separado: el tope común es el presupuesto del libro | 20 |
| Razonamiento | `AI_THINKING=adaptive` (con `AI_EFFORT=low`, recomendado por la documentación) u `off` (`between_tools`, solo Sonnet 5.5: sin razonamiento extendido, menos tokens de salida) | adaptive + low |
| Una solicitud a la vez | Cerrojo en el proceso más archivo `gasto_ia.lock` entre procesos (por ejemplo, la app y la evaluación a la vez) | Activo |
| Mismo mensaje, un solo pago | Memoria de resultados por instancia (HMAC con clave aleatoria, sin guardar el texto), consultada bajo el mismo cerrojo que el envío | Activa |

## 2. Antes y después de cada solicitud
1. **Estimación previa, por exceso:**
   - Entrada: el mayor de «caracteres / 2,5» y «bytes UTF-8 / 2» (cubre emojis y otros alfabetos), más 400 tokens de sobrecarga, sin llamar a la API de conteo. Sigue siendo una estimación: si el texto real ocupa más tokens, el coste real puede superar la reserva de esa solicitud. Por eso la liquidación usa el `usage` real.
   - **Peor caso:** toda la entrada a precio de escritura en caché y la salida completa (`max_tokens`).
2. **Reserva:** si `gastado + peor caso > presupuesto`, la solicitud **no se envía**. Si cabe, el peor caso se apunta como «en curso» en el libro de gasto.
3. **Liquidación:** se sustituye la reserva por el coste calculado con el `usage` real de la respuesta: entrada, salida, escritura y lectura de caché.
   - **Sin `usage`, tiempo agotado, error de red o error 5xx:** se mantiene el cargo pesimista, porque pudo facturarse.
   - **Errores 400, 401, 403, 404, 413, 422 y 429:** la API rechaza sin generar, así que se apunta 0. Un 408 o un 409 mantienen el cargo pesimista.
   - **Si el proceso muere a mitad:** el cargo pesimista se queda apuntado.
4. **Respuesta incompleta** (`max_tokens`, `pause_turn` u otro `stop_reason` distinto de `end_turn`) o JSON inválido: la salida no se usa y el análisis se declara parcial. El gasto sí se registra.

Precios usados (USD por millón de tokens), según la página oficial de precios consultada el 2026-11-08 (https://platform.claude.com/docs/en/about-claude/pricing):

| Modelo | Entrada | Escritura caché 5 min | Lectura caché | Salida |
|---|---|---|---|---|
| Sonnet 5.5 | 2,00 | 2,50 | 0,10 | 10,00 |
| Opus 5.5 | 4,00 | 5,00 | 0,20 | 20,00 |

Peor caso por solicitud con los valores por defecto (Sonnet 5.5, 6 000 tokens de entrada y 4 000 de salida): ≈ 0,055 USD. Con 0,50 USD caben al menos 9 solicitudes en el peor caso. El coste **real** por solicitud no se ha medido.

## 3. Libro de gasto
- Ruta: `%LOCALAPPDATA%\antifraude\gasto_ia.json`, configurable con `AI_LEDGER_PATH`. **Siempre fuera del repositorio:** una ruta dentro del repositorio bloquea la IA.
- Copia `gasto_ia.json.bak`: si falta uno de los dos archivos, vale el otro; si están los dos, el de mayor gasto. Borrar solo el libro no reinicia el presupuesto.
- Si el libro desaparece durante una solicitud, el coste se vuelve a apuntar al liquidar. Valores negativos o no finitos se tratan como libro dañado: no se gasta.
- Guarda: modelo, fecha, estado, tokens, coste reservado y coste final.
- **No guarda** texto de mensajes, citas, remitentes ni claves. Los registros (`logging`) tampoco.
- Si el archivo está dañado, la IA **no se usa** y el archivo no se sobrescribe: hay que revisarlo a mano.
- Para empezar una campaña de pruebas desde cero, archive el JSON con otro nombre. No lo borre sin revisarlo.

## 4. Límite preventivo local frente a límite de facturación
- **Este control es un límite preventivo local.**
  - Vive en el ordenador.
  - Solo cubre las solicitudes hechas por esta aplicación con este libro de gasto.
  - Calcula el coste con la tarifa publicada.
  - No es la factura.
- **El límite efectivo de facturación** lo fija Anthropic en la organización: límites de gasto o crédito prepagado en Anthropic Console. Es lo único que impide de verdad que se cobre más.
  - **Recomendación:** antes de autorizar gasto, fijar en Console un límite mensual bajo y usar una clave **exclusiva** para este proyecto.
- **Posibles sobrecostes respecto al límite local:**
  1. **Solicitudes en curso:** una solicitud ya enviada se factura aunque después se supere el presupuesto. Se mitiga reservando el peor caso **antes** de enviar y permitiendo una sola solicitud a la vez. Por eso el exceso máximo teórico es el de una solicitud.
  2. **Tiempo agotado en el cliente:** la API puede haber terminado y facturado. Se cuenta el peor caso.
  3. **Diferencias de cálculo:** cambios de tarifa, redondeos, multiplicadores (residencia de datos ×1,1, que no usamos) o tokens que añade el servidor (por ejemplo, el esquema de salida estructurada). La estimación es por exceso, pero **no es una garantía**.
  4. **Otros usos de la misma clave** (otra aplicación, la consola o Claude Code con clave de API): no pasan por este libro.
  5. **Varios libros o libro borrado:** si se cambia `AI_LEDGER_PATH`, o se borran el libro y su copia, el contador empieza de cero. Es un control local, no una garantía frente a quien maneja el ordenador.
  6. **Liquidación fallida tras un pago** (por ejemplo, disco lleno): se usa la respuesta ya pagada y el cargo pesimista reservado sigue en el libro.
- **Claude Code**, la herramienta de desarrollo, **no** usa este control.
  - En esta sesión, Claude Code se autentica con las credenciales OAuth de su propio inicio de sesión (no hay `ANTHROPIC_API_KEY` ni `apiKeyHelper` configurados). Por eso es **probable** que no consuma los créditos de la Console del proyecto.
  - No se ha podido verificar desde aquí cómo factura cada cuenta.

## 5. Cómo activar la IA cuando se autorice (no hacerlo antes)
```powershell
# Requiere antes: autorizar e instalar el SDK oficial «anthropic» y fijar un límite en Anthropic Console.
$env:AI_ENABLED = "1"
$env:CLAUDE_MODEL = "claude-sonnet-5-5"
$env:AI_BUDGET_USD = "0.50"          # solo cuando el usuario lo apruebe expresamente
$env:AI_MAX_REQUESTS = "20"
$env:ANTHROPIC_API_KEY = Read-Host "Clave de Anthropic" -MaskInput   # PowerShell 7; ver docs/CONFIGURACION.md
```
Las pruebas de integración real están en `tests/integracion_real/` y se saltan salvo que se active `ANTIFRAUDE_PRUEBAS_REALES=1` (ver `docs/PRUEBAS_INTEGRACION_REAL.md`).
