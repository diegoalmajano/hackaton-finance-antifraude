# Verificación independiente en Linux — 09-11-2026

> Verificación hecha por un compañero del equipo con Claude a partir del ZIP de `feat/fase-0` descargado de GitHub, en un entorno Linux temporal y separado. Sin llamadas a la API de Claude, sin claves, sin Gmail real y sin gasto (IA=0, presupuesto=0). No se cambió código del producto, reglas ni etiquetas.

## Entorno
- Linux x86_64, Python 3.12.3, entorno virtual nuevo con `requirements.lock` (26 paquetes; `colorama` se instala sin problema aunque solo se usa en Windows).
- Navegador: Chromium sin interfaz (Playwright), solo contra `127.0.0.1`.

## Resultados
| Comprobación | Resultado | Estado |
|---|---|---|
| Suite Python (`pytest`) | 877 passed, 4 skipped, 1 xfailed, 1 warning: coincide con lo declarado | **Probado** |
| Informe de desarrollo (`python -m antifraude.evaluation`) | 27/27 aceptables, latencia local p50 1 ms / p95 2 ms. Sigue siendo **desarrollo**, no evaluación | **Probado** |
| Arranque con `APP_DEMO_MODE=1` | Código de emparejamiento en consola y servidor solo en 127.0.0.1:8790 | **Probado** |
| Emparejamiento → panel | Correcto en navegador real | **Probado** |
| Ejemplos 1, 2 y 3 | BAJO, ALTO y ALTO (lo que dice `GUION_DEMO.md`) | **Probado** |
| Texto libre del guion | ALTO | **Probado** |
| `.eml` 01–04 | BAJO, ALTO, ALTO y NO CONCLUYENTE | **Probado** |
| Tiempo de respuesta en navegador | Unos 360–390 ms por análisis (incluye la petición htmx) | **Probado** |
| Reflujo a 320 px | Sin desbordamiento horizontal | **Probado** (automático) |
| Cerrar sesión → `/panel` | Protegido | **Probado** |
| Consola del navegador | Sin infracciones de CSP. Un único 401 esperado al pedir `/panel` tras cerrar sesión | **Probado** |
| Instrucciones nuevas de Linux en el README | Ejecutadas tal cual en una copia limpia: instalación y arranque correctos | **Probado** |
| macOS | — | **No probado** |
| Lector de pantalla, contraste elevado, teclado manual completo | — | **No probado** (sigue diferido) |

## Sondeo informal de generalización (no es evaluación)
Se pasaron 18 mensajes **nuevos**, que no están en el conjunto dev, redactados por Claude en esta sesión a partir de tipologías públicas de estafa en España. Mismo riesgo de circularidad que R-26: **no usar como métrica ante el jurado**, solo como orientación del equipo.

- Estafas con alerta (MEDIO/ALTO): **10 de 12**. Correos-aduanas, DGT, Hacienda, «hijo con número nuevo», falso soporte técnico, cripto, falso empleo, Amazon suplantado, cargo no reconocido con teléfono y «cuenta segura».
- Legítimos en BAJO: **5 de 5**. Cita médica, Bizum recibido, código OTP con aviso de no compartir, pedido enviado y aviso de la comunidad.
- Fallos, todos ya cubiertos por límites documentados y ninguno en BAJO salvo el último:
  - **Bizum inverso** («le hemos enviado una solicitud de Bizum para recibir el reembolso… acéptela»): NO CONCLUYENTE. Es una estafa muy común en España; el texto no pide claves ni lleva enlace. Candidata a regla de patrón, o a la IA. **Actualización del mismo día: resuelto con la regla `content.reverse_payment_request` (rules-0.3.4); ver `docs/LIMITACIONES_DETECCION.md`.**
  - **Corte de suministro con enlace acortado** (bit.ly): NO CONCLUYENTE, por diseño (no se abren acortadores).
  - **«¿Tienes un momento? Necesito un favor rápido»**: BAJO. Limitación ya documentada en `LIMITACIONES_DETECCION.md` (ingeniería social sin palabras clave).

Estos tres casos son buenos argumentos para la capa de IA: es justo lo que las reglas no resuelven sin falsas alarmas.

## Cambios aplicados
- `README.md`: requisitos y nueva subsección «Linux o macOS (alternativa)» con los comandos comprobados. Sin cambios de comportamiento.
- Este documento.
