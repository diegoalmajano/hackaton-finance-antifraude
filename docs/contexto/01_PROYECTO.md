# 01 — Proyecto: objetivo y contexto del evento

> Adaptado (sesión 5) del documento homónimo de la memoria original; solo contenido vigente. Leyenda de fiabilidad (todos los documentos): ✅ confirmado en documento oficial · 🟡 fuentes secundarias coherentes · 📢 declarado por un proveedor · 💬 afirmado solo por el usuario/chat · ❓ hipótesis · ⏳ pendiente de verificar · ⚖ valoración del asistente.

## 1. Qué es
Participación en el **Hackatón Finance** («Hackfinance») organizado por **BEST UC3M** con GPTadvisor, MyInvestor, Claude (Anthropic) y ElevenLabs como patrocinadores ✅ (banner del PDF oficial). Reto de **temática abierta** ✅.
Objetivo: construir un **producto de IA aplicado a finanzas** útil, técnicamente sólido, ejecutable y con demo convincente, que gane según la rúbrica (D-01, D-08). **No es necesario que sea para GPTadvisor** (D-08); no afirmar integración oficial con él.

## 2. Datos del evento (y su fiabilidad)
| Dato | Valor | Fiabilidad |
|---|---|---|
| Inicio | 8 nov 2026 (domingo), apertura en Leganés | 💬 |
| Presentación al jurado | **12 nov 2026 (jueves)** | 💬 — el PDF oficial no fija fecha |
| Hora de cierre de entrega | **No publicada** | ⏳ preguntar a BEST UC3M (Q-01) |
| Equipos | 4 a 6 personas | 💬 |
| Premios | hasta 500 € | 💬 |
| Jurado | 4 personas, 2 de GPTadvisor | 💬 |
| Rúbrica y entregables | ver `02` y `../referencia/rubrica_oficial_texto.md` | ✅ |

## 3. Producto (resumen; detalle en `11`)
**Asistente de IA para prevenir estafas financieras en mensajes y comunicaciones digitales escritas** (D-09, D-12). Proactivo sobre canales autorizados, alertas en dos fases, análisis pasivo de enlaces, riesgo explicado en 4 niveles, decisión siempre del usuario. Modelo **B2B** para bancos españoles con usuario final protegido (D-13). Windows primero (D-15); Gmail primera integración real (D-16). Voz: fase 2 (D-12).

## 4. Pilares de decisión
1. La **rúbrica oficial** manda: 30 % implementación, 30 % innovación/viabilidad.
2. Solución **acabada y ejecutable** > muchas funciones a medias.
3. Un detector «pega aquí tu mensaje» **no es novedad** (`12` §4): la diferenciación es proactividad, alertas en dos fases, explicación para mayores, personalización controlada y modelo B2B.
4. Demo con **datos sintéticos** o cuentas de prueba propias; nada de datos personales reales no autorizados.
5. Presentar solo lo **medido**; distinguir resultado observado / hipótesis / trabajo pendiente.

## 5. Equipo
5 personas con perfil Python/IA, 3–5 h/día cada una (D-19), reparto P1–P5 propuesto en `14` §1. ⏳ Confirmar quiénes trabajan en **este** repositorio independiente (T-12).

## 6. Independencia (D-23)
Este repositorio es **independiente** del de cualquier otro equipo o compañero: no se usa su repositorio, código ni decisiones técnicas como instrucciones. Toda la memoria necesaria vive en este repositorio (`CLAUDE.md` + `docs/`).
