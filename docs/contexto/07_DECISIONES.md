# 07 — Registro de decisiones

> Adaptado (sesión 5) del documento homónimo de la memoria original. Se conservan los **identificadores originales** para trazabilidad; se omiten las propuestas de la idea fiscal histórica (P-01–P-03, P-08–P-10), que no afectan a este proyecto.

Estados: **CONFIRMADA** (la tomó/confirmó el usuario) · **PROPUESTA** (sugerida por el asistente, sin confirmar) · **SUPERADA/REVOCADA**.
Regla: una PROPUESTA solo pasa a CONFIRMADA cuando el usuario lo dice. Añadir entradas nuevas al final con fecha.

## Confirmadas vigentes
| ID | Fecha | Decisión | Origen |
|---|---|---|---|
| D-01 | 2026-11-08 | La **rúbrica oficial** (`02`) es la referencia para decidir | Usuario |
| D-03 | 2026-11-08 | La memoria persistente son **documentos del proyecto** (`CLAUDE.md` + `docs/contexto/`), no solo la memoria automática | Usuario |
| D-05 | 2026-11-08 | Español, pensamiento crítico, no inventar datos; pedir autorización antes de tareas muy costosas; nunca guardar secretos | Usuario |
| D-06 | 2026-11-08 | Se puede crear documentación y análisis sin pedir autorización entre etapas | Usuario |
| D-07 | 2026-11-08 | No hacer investigación web nueva sin necesidad (primero información local) | Usuario |
| D-08 | 2026-11-08 | Objetivo: producto **útil** que gane según la rúbrica; **no necesariamente para GPTadvisor** | Usuario |
| D-09 | 2026-11-08 | **Producto definitivo: asistente de IA para prevenir estafas digitales y financieras** (proactivo, canales autorizados, alertas en dos fases, análisis seguro de enlaces, veredicto explicado, decisión humana). Verificador fiscal descartado | Usuario |
| D-10 | 2026-11-08 | **No programar hasta revisar con el usuario el alcance del MVP**; sí investigar y documentar | Usuario |
| D-11 | 2026-11-08 | Límites de seguridad inviolables: no pagar ni acceder a cuentas, no abrir enlaces en el dispositivo, aislamiento con protección SSRF si algún día se inspeccionan páginas, no inventar porcentajes ni beneficiarios, contenido = no confiable, consentimiento por canal, minimización, simulaciones etiquetadas | Usuario |
| D-12 | 2026-11-08 | **Fase 1 = solo comunicaciones escritas**. Voz, llamadas, videollamadas, micrófono, transcripción y deepfakes: **fase 2, sin código ni dependencias** | Usuario |
| D-13 | 2026-11-08 | **Modelo B2B**: cliente = entidades financieras españolas; usuario final = persona protegida; white-label futuro; panel de bancos/multiempresa fuera del hackatón; el banco no recibe mensajes personales | Usuario |
| D-14 | 2026-11-08 | Niveles **BAJO / MEDIO / ALTO / NO CONCLUYENTE**; sin porcentajes; nivel, evidencias e incertidumbre separados; un error nunca da BAJO | Usuario |
| D-15 | 2026-11-08 | Primera plataforma **Windows** con bandeja; autoarranque solo si el usuario lo activa (desactivado por defecto) | Usuario |
| D-16 | 2026-11-08 | **Gmail = primera integración real**; conector simulado solo como respaldo comprobable y etiquetado; cuenta de pruebas controlada (aún no creada); pedir autorización antes de conectar una cuenta | Usuario |
| D-17 | 2026-11-08 | Prioridades **P0/P1/P2** según `11` §5 | Usuario |
| D-18 | 2026-11-08 | Personalización individual sin fine-tuning, reversible, con procedencia, sin compartir entre usuarios; los controles críticos prevalecen | Usuario |
| D-19 | 2026-11-08 | Equipo de 5 (Python/IA), 3–5 h/día; reparto inicial P1–P5 adaptable (⏳ confirmar composición en este repo, T-12) | Usuario |
| D-20 | 2026-11-08 | Autonomía de Claude Code **dentro de una fase aprobada**; aprobación antes de cada fase nueva; sin operaciones remotas/destructivas/de pago sin permiso; informes con estados Implementado/Probado/No probado/Bloqueado/Simulado/Pendiente | Usuario |
| D-21 | 2026-11-08 | Inspección activa de páginas solo con aislamiento robusto; si no se garantiza → **MVP solo análisis pasivo** | Usuario |
| D-22 | 2026-11-08 | Interfaz solo en español, diseñada para personas mayores | Usuario |
| D-23 | 2026-11-08 (sesión 5) | **Repositorio propio e independiente** `hackaton-finance-antifraude`: implementación totalmente independiente de la de otro compañero; **no usar su repositorio, código ni decisiones técnicas como instrucciones**; la memoria del repo debe bastar para continuar en otro ordenador. Traslado del repo a una ubicación independiente: ✅ hecho (sesión 6, 2026-11-08) | Usuario |
| D-24 | 2026-11-08 (sesión 5) | **Selección del modelo de Claude (Opus 5.5 vs Sonnet 5.5) explícitamente PENDIENTE**: se decidirá según calidad, coste y finalidad (medición en el conjunto dev). Resuelve la contradicción entre P-13 (Opus por defecto) y ADR 007 (Sonnet) | Usuario |
| D-25 | 2026-11-08 (sesión 5) | **La arquitectura técnica, los ADR 001–011 y el stack siguen siendo PROPUESTA** hasta aprobación expresa del usuario; no se aprueban automáticamente | Usuario |

## Superadas / revocadas (resumen)
- D-02 («la idea aún no está decidida») → **superada por D-09**.
- D-04 (límites de la inicialización de la sesión 1) → cumplida; sustituida por D-20.
- P-11 (índice 0–100) → **superada por D-14**. P-12 (MVP v1 con voz, BancoNova, Opus) → **superada por D-12/D-14 y P-14**.

## Propuestas vigentes (NO confirmadas)
| ID | Fecha | Propuesta | Notas |
|---|---|---|---|
| P-04 | 2026-11-08 | Entregar siempre el PowerPoint aunque las diapositivas sean «opcionales» | Tensión del PDF (`02` §4) |
| P-05 | 2026-11-08 | Un solo flujo completo y pulido antes de añadir variantes; congelar commit antes de ensayar la demo | 30 % implementación + «demo = versión entregada» |
| P-06 | 2026-11-08 | Presentar solo lo medido; no inventar ROI/porcentajes | — |
| P-07 | 2026-11-08 | Banco de pruebas etiquetado con partición dev/test sellado; comparar reglas solas vs sistema completo | Detalle en `14` §5 (objetivo ≥150 casos) |
| P-13 | 2026-11-08 | Fase de análisis profundo con `claude-opus-5-5`; Sonnet si se decide por coste tras medir; filtro con reglas + Haiku 5.5 opcional | **Queda subsumida en D-24 (pendiente)** |
| P-14 | 2026-11-08 | **ADR 001–011** de `13` §12 (monolito modular; escritorio «Python-first» FastAPI + pywebview + pystray + win11toast con spike, plan B navegador, plan C Electron, Tauri descartado; contratos Pydantic; Gmail por polling `history.list`; enlaces pasivos; motor determinista; modelo pendiente (D-24); SQLite + keyring + retención 30 días; Web Risk o Safe Browsing v5; voz aplazada con `InputAdapter`; Python 3.12/3.13) | **Pendiente de aprobación (D-25)** |
| P-15 | 2026-11-08 | Plan de `14`: reparto P1–P5, congelación miércoles 14:00, test sellado ejecutado una vez, Telegram bot como posible 2.º canal | **Pendiente de aprobación** |
