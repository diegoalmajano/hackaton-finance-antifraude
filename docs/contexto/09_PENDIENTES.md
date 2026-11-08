# 09 — Pendientes, dudas, riesgos y contradicciones

> Adaptado (sesión 5) del documento homónimo de la memoria original: solo lo vigente para el asistente antifraude (las preguntas y riesgos de la idea fiscal son históricos y se omiten). Identificadores originales conservados. Cerrar una entrada = anotarlo aquí con fecha y fuente.

## 1. Bloqueantes para empezar a programar
- B-01 **Aprobación** del MVP, de los ADR (`13` §12) y del plan (`14`) (D-25).
- B-02 (actualizado sesión 5) Repositorio: ✅ creado e independiente (D-23). ~~Traslado~~ ✅ hecho y verificado (sesión 6, 2026-11-08) · remoto ✅ comprobado (accesible, vacío) · primer commit ✅ local (sesión 6). Pendiente: **primer push** (con autorización).
- B-03 **Hora exacta de cierre** (no publicada; preguntar a BEST UC3M) = Q-01.
- B-04 Cuenta **Gmail de pruebas** (+ cuenta emisora) y proyecto **Google Cloud** (consentimiento OAuth External/Testing, usuarios de prueba, cliente «Desktop»); conectar solo con autorización.

## 2. Decisiones técnicas abiertas
- T-01 Stack de UI: React/TS (Vite) vs htmx · T-02 resultado del spike pywebview/pystray/win11toast · T-03 versión de Python común (3.12/3.13; la máquina tiene 3.14) · T-04 reputación: Web Risk (¿facturación GCP?) vs Safe Browsing v5 · T-05 retención inicial (propuesta 30 días, sin cuerpo completo) · T-06 presupuesto de API y límite de gasto · T-07 segundo canal (Telegram bot recomendado, P2) · T-08 empaquetado (venv + README vs PyInstaller) · T-09 ¿test sellado dentro del repo o fuera? · T-10 bancos del directorio inicial y quién verifica sus dominios.
- **T-11 (sesión 5) Modelo de Claude para el análisis profundo: `claude-opus-5-5` vs `claude-sonnet-5-5`** según calidad (detección y evidencias en dev), coste por análisis y finalidad (también refusals, V-17). Decide el usuario (D-24).
- **T-12 (sesión 5)** ¿Quiénes trabajan en este repositorio independiente? ¿Sigue vigente el reparto P1–P5 de `14` §1?
- A-07 Nombre del producto.

## 3. Preguntas a la organización (BEST UC3M)
- Q-01 **Fecha y hora de cierre** y URL del formulario.
- Q-02 Duración de la presentación y formato de preguntas.
- Q-03 Datos/APIs/claves/créditos que ofrece el hackatón.
- Q-04 ¿Qué variable valora más el jurado (errores evitados, tiempo, experiencia)?
- Q-05 Confirmar datos 💬 del evento (`01` §2).

## 4. Información y accesos
- Q-25 Claves de Anthropic y créditos (nunca en el repo). · Q-27 ¿Python/navegador disponibles en las máquinas del equipo y en la de la demo?

## 5. Verificaciones técnicas (⏳)
- V-03 Telegram Business: ¿requiere Premium? · V-05 competidores en español y si alertan proactivamente (para afirmar diferenciación) · V-07 balance oficial INCIBE 2025 antes de citar cifras · V-08 marco jurídico (RGPD: rol, base jurídica, EIPD; AI Act).
- V-10 `Authentication-Results` en `payload.headers` de Gmail · V-11 caducidad de 7 días del refresh token en Testing (doc. OAuth principal) · V-12 Python 3.14 con pythonnet/pywebview · V-13 licencia de pystray · V-14 términos oficiales de Anthropic sobre entrenamiento/retención · V-15 si enviar fragmentos de Gmail a Anthropic cuenta como «transmisión» para Google + política de Uso Limitado · V-16 Web Risk: requisitos de facturación · V-17 refusals del modelo elegido con contenido de phishing (medir en dev).

## 6. Contradicciones
| ID | Contradicción | Tratamiento |
|---|---|---|
| C-01 | PDF: «diapositivas opcionales» vs PowerPoint como entregable | Entregar PPTX siempre (P-04) |
| C-02 | El PDF no fija fecha; el 12-nov procede del equipo | Marcar 💬; confirmar (Q-01) |
| C-16 (sesión 5) | P-13 proponía Opus 5.5 por defecto; ADR 007 proponía Sonnet 5.5 | **Resuelta como pendiente explícita** (D-24); `13` y `14` actualizados |
| C-17 (sesión 5) | `12` §1 y §3 contemplan una demo con audio sintético y ElevenLabs | **Prevalece D-12** (voz en fase 2); `12` §5bis ya lo indica |
| C-18 (sesión 5) | La memoria original hablaba de un «repositorio compartido no clonado» | **Superada por D-23** (repositorio propio e independiente) |

## 7. Riesgos
- R-20 Novedad frente a competidores consolidados (30 %). · R-21 Prometer canales imposibles (`12` §1). · R-22 Porcentajes sin calibrar (prohibidos, D-14). · R-23 Prompt injection. · R-24 Privacidad de mensajes enviados a la nube. · R-25 Alcance vs 4 días. · R-26 Banco de pruebas circular (IA que escribe y detecta). · R-27 Demo dependiente de red/APIs → modo sin IA real etiquetado. · R-28 Correos de prueba en SPAM.
- Registro completo con mitigaciones: `14` §7 (incluye la posible pérdida de puntos de IA frontera por no usar audio, aceptada).
