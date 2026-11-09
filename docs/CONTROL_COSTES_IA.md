# Control de costes de la API de Claude

> Estado (2026-11-09): **implementado y probado solo con clientes simulados; SDK Anthropic sin instalar**. Gasto real de la aplicación en la API de Anthropic: **0 USD** (no se ha hecho ninguna llamada). Gasto **autorizado** por el usuario: **0 USD**.

## 1. Qué impide gastar sin querer
| Control | Cómo funciona | Por defecto |
|---|---|---|
| IA desactivada | Sin `AI_ENABLED=1` no se envía nada | Desactivada |
| Modelo explícito | `CLAUDE_MODEL` debe ser `claude-sonnet-5-5` o `claude-opus-5-5`; no hay modelo por defecto | Ninguno |
| Opus bloqueado | `claude-opus-5-5` exige además `AI_ALLOW_OPUS=1` | Bloqueado |
| Sin *fallback* a otros modelos | No se envía `fallbacks`. Un *fallback* repetiría la petición con otro modelo y se facturaría a su tarifa | Desactivado (sin opción para activarlo) |
| Sin reintentos automáticos | SDK con `max_retries=0` y la aplicación no reintenta. Un reintento podría pagar dos veces | 0 reintentos |
| Presupuesto autorizado | `AI_BUDGET_USD`. Con 0 la IA no se usa. Tope duro de 10 USD contra errores de tecleo | **0 USD** |
| Presupuesto **previsto** | `PLANNED_INITIAL_BUDGET_USD=0.50` es una referencia histórica del código, no permiso. El piloto propuesto ahora es 0,20 USD para una única ejecución de hasta tres casos, según `PLAN_PILOTO_SONNET.md`; tampoco está autorizado | — |
| Límite de entrada | `AI_MAX_INPUT_TOKENS`. Si la estimación lo supera, no se envía y el análisis queda «parcial» | 6 000 |
| Límite de salida | `AI_MAX_OUTPUT_TOKENS` → `max_tokens` de la petición | 4 000 |
| Solicitudes por sesión | `AI_MAX_REQUESTS`, contadas por **instancia** del analizador. La aplicación y el ejecutor de la evaluación cuentan por separado: el tope común es el presupuesto del libro | 20 |
| Razonamiento | `AI_THINKING=adaptive` (con `AI_EFFORT=low`, recomendado por la documentación) u `off` (`between_tools`, solo Sonnet 5.5: sin razonamiento extendido, menos tokens de salida) | adaptive + low |
| Una solicitud a la vez | Cerrojo en el proceso más archivo `gasto_ia.lock` entre procesos (por ejemplo, la app y la evaluación a la vez) | Activo |
| Mismo mensaje, un solo pago | Memoria por instancia y usuario/contexto del prompt: HMAC con clave aleatoria, sin texto en las claves, consultada bajo el mismo cerrojo que el envío | Activa |

## 2. Antes y después de cada solicitud
1. **Estimación previa, por exceso:**
   - Entrada: el mayor de «caracteres / 2,5» y «bytes UTF-8 / 2» (cubre emojis y otros alfabetos), más 400 tokens de sobrecarga, sin llamar a la API de conteo. Sigue siendo una estimación: si el texto real ocupa más tokens, el coste real puede superar la reserva de esa solicitud. Por eso la liquidación usa el `usage` real.
   - **Peor caso:** toda la entrada a precio de escritura en caché y la salida completa (`max_tokens`).
2. **Reserva:** si `gastado + peor caso > presupuesto`, la solicitud **no se envía**. Si cabe, el peor caso se apunta como «en curso» en el libro de gasto.
3. **Liquidación:** se sustituye la reserva por el coste calculado con el `usage` real de la respuesta: entrada, salida, escritura y lectura de caché.
   - **Sin `usage`, consumo inválido, tiempo agotado, error de red o error 5xx:** se mantiene el cargo pesimista, porque pudo facturarse.
   - **Errores 400, 401, 403, 404, 413, 422 y 429:** la API rechaza sin generar, así que se apunta 0. Un 408 o un 409 mantienen el cargo pesimista.
   - **Si el proceso muere a mitad:** el cargo pesimista se queda apuntado.
4. **Respuesta incompleta** (`max_tokens`, `pause_turn` u otro `stop_reason` distinto de `end_turn`) o JSON inválido: la salida no se usa y el análisis se declara parcial. El gasto sí se registra.

Precios usados (USD por millón de tokens), según la [página oficial de precios](https://platform.claude.com/docs/en/about-claude/pricing), cotejada el 2026-11-09:

| Modelo | Entrada | Escritura caché 5 min | Lectura caché | Salida |
|---|---|---|---|---|
| Sonnet 5.5 | 2,00 | 2,50 | 0,10 | 10,00 |
| Opus 5.5 | 4,00 | 5,00 | 0,20 | 20,00 |

Peor caso por solicitud con los valores por defecto (Sonnet 5.5, 6 000 tokens de entrada y 4 000 de salida): ≈ 0,055 USD. La propuesta de un único piloto de hasta tres envíos reserva hasta 0,165 USD, frente al techo operativo propuesto de 0,20 USD. Ninguna cifra concede autorización ni garantiza la factura. El coste **real** por solicitud no se ha medido.

## 3. Libro de gasto
- Ruta: `%LOCALAPPDATA%\antifraude\gasto_ia.json`, configurable con `AI_LEDGER_PATH`. **Siempre fuera del repositorio:** una ruta dentro del repositorio bloquea la IA.
- Copia `gasto_ia.json.bak`: si falta uno de los dos archivos, vale el otro; si están los dos, el de mayor gasto. Borrar solo el libro no reinicia el presupuesto.
- Si el libro desaparece durante una solicitud, el coste se vuelve a apuntar al liquidar. Se validan versión 1, lista acotada de entradas, identificadores únicos, costes y reservas no negativos/finitos y acumulado no inferior a la suma de entradas conservadas. Una incoherencia bloquea antes de enviar y no sobrescribe el archivo.
- Guarda: modelo, fecha, estado, tokens, coste reservado y coste final.
- **No guarda** texto de mensajes, citas, remitentes ni claves. Los registros (`logging`) tampoco.
- Si el archivo está dañado, la IA **no se usa** y el archivo no se sobrescribe: hay que revisarlo a mano.
- El historial conserva hasta 500 entradas; al podarlas no se reinicia el acumulado. No archive, borre ni cambie de ruta el libro para recuperar cupo: antes de cualquier nueva autorización se concilian el libro, su copia y el gasto observado en Console.

## 4. Límite preventivo local frente a límite de facturación
- **Este control es un límite preventivo local.**
  - Vive en el ordenador.
  - Solo cubre las solicitudes hechas por esta aplicación con este libro de gasto.
  - Calcula el coste con la tarifa publicada.
  - No es la factura.
- **El límite efectivo de facturación** lo fija Anthropic en la organización: límites de gasto o crédito prepagado en Anthropic Console. Es lo único que impide de verdad que se cobre más.
  - **Recomendación:** antes de autorizar gasto, fijar en Console un límite mensual bajo y usar una clave **exclusiva** para este proyecto.
- **Posibles sobrecostes respecto al límite local:**
  1. **Solicitudes en curso:** una solicitud ya enviada se factura aunque después se supere el presupuesto. Se mitiga reservando el peor caso **antes** de enviar y permitiendo una sola solicitud a la vez. Esto limita a una solicitud en curso dentro del control común; no constituye una garantía matemática sobre el precio real ni cubre otros clientes.
  2. **Tiempo agotado en el cliente:** la API puede haber terminado y facturado. Se cuenta el peor caso.
  3. **Diferencias de cálculo:** cambios de tarifa, redondeos, multiplicadores (residencia de datos ×1,1, que no usamos) o tokens que añade el servidor (por ejemplo, el esquema de salida estructurada). La estimación es por exceso, pero **no es una garantía**.
  4. **Otros usos de la misma clave** (otra aplicación, la consola o Claude Code con clave de API): no pasan por este libro.
  5. **Varios libros o libro borrado:** si se cambia `AI_LEDGER_PATH`, o se borran/reemplazan coherentemente el libro y su copia, el control local puede empezar de cero. La validación detecta corrupción/incoherencias; no autentica archivos frente a quien controla el ordenador. El límite efectivo debe revisarse en Console.
  6. **Liquidación fallida tras un pago** (por ejemplo, disco lleno): se usa la respuesta ya pagada y el cargo pesimista reservado sigue en el libro.
- Las herramientas de desarrollo y otras aplicaciones no usan necesariamente este control. No se ejecutan Claude Code/ECC en la continuación actual ni se deduce su facturación de la del asistente. El acceso a Codex no concede crédito de API ni modifica el proveedor de la aplicación.

## 5. Piloto propuesto, todavía sin autorización

El plan vigente está en [PLAN_PILOTO_SONNET.md](PLAN_PILOTO_SONNET.md): modelo `claude-sonnet-5-5`, **una única ejecución** de los tres casos sintéticos existentes y propuesta de techo operativo **0,20 USD**. No se utiliza el presupuesto histórico de 0,50 ni el máximo general de 20 solicitudes como permiso.

El módulo `tests/integracion_real/test_claude_real.py` comparte un analizador con `max_requests=3`: limita esa ejecución, no futuras ejecuciones o reinicios. No se relanza tras fallo/interrupción, ni se sustituyen los tres casos por el banco de 27. Antes de cualquier nueva autorización se revisan el libro, cargos en curso/desconocidos y Console. No se exige desarrollar otro lanzador para este piloto acotado.

Instalación del SDK en un entorno temporal separado, clave exclusiva, política de retención, límites y gasto necesitan confirmación previa. Nada está instalado o activado por esta documentación. Las pruebas reales siguen bloqueadas; `AI_ENABLED=0`, `AI_BUDGET_USD=0`, `AI_ALLOW_OPUS=0` y ambos indicadores de integración real permanecen en cero.

## 6. Regresiones de seguridad añadidas el 09-11-2026

`tests/test_c_seguridad_final.py` añade **48 casos**, sin API ni red:

- Consumo: los contadores solo admiten enteros no negativos; bool, cadenas, fracciones, nulos y valores no finitos/desmesurados no se convierten en cero. La ausencia de campos opcionales de caché sí equivale a cero. Consumo desconocido conserva la reserva; una salida estructurada válida ya recibida puede aprovecharse sin inventar su coste.
- Libro: versión/estructura/costes/identificadores/coherencia inválidos bloquean sin enviar ni sobrescribir. La recuperación desde la copia y la poda de entradas válidas preservan el gasto acumulado.
- Caché: nombre/dominio del remitente, Reply-To, canal y usuario forman parte del material HMAC. Otro contexto o usuario no hereda la respuesta; la repetición equivalente sigue deduplicada.

Las 48 regresiones y las suites existentes de costes, IA y seguridad de misión 3 dieron **129 passed, 1 warning** en 7,51 s. No se añadieron saltos ni se ejecutó ninguna integración real. Son comprobaciones con transportes/datos simulados; el SDK Anthropic y el uso real siguen pendientes.
