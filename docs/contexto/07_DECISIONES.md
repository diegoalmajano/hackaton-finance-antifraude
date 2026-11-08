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
| D-25 | 2026-11-08 (sesión 5) | ~~La arquitectura técnica, los ADR 001–011 y el stack siguen siendo PROPUESTA~~ → **superada por D-26** (sesión 6). Sigue vigente el principio: nada se aprueba automáticamente | Usuario |
| D-26 | 2026-11-08 (sesión 6) | **Arquitectura aprobada**: ADR 0001–0011 con las modificaciones de la auditoría ECC + nuevos ADR 0012–0015, en `docs/adr/`. Los puntos ⏳ **no se consideran verificados** | Usuario |
| D-27 | 2026-11-08 (sesión 6) | **Stack base: Python 3.12 + FastAPI + Pydantic v2 + SQLite**. La app funciona primero como **web local en el navegador**; pywebview y bandeja solo después de comprobar el núcleo. Electron y Tauri descartados para el hackatón | Usuario |
| D-28 | 2026-11-08 (sesión 6) | **Orden de prioridad**: a) análisis manual · b) filtro por reglas y extracción segura de enlaces · c) motor determinista de riesgo y explicaciones · d) integración real con Claude · e) UI accesible en español y alertas · f) Gmail real · g) funciones de escritorio si queda tiempo | Usuario |
| D-29 | 2026-11-08 (sesión 6) | **Motor de riesgo**: estados de comprobación `done` / `failed` / `not_configured` diferenciados (solo las obligatorias fallidas impiden BAJO); **una petición de credenciales u OTP nunca es segura por venir de un dominio aparentemente oficial** (mínimo MEDIO) (ADR-0006) | Usuario |
| D-30 | 2026-11-08 (sesión 6) | **API local**: solo `127.0.0.1`; autenticación de sesión (cookie HttpOnly, SameSite=Strict); controles de Host, Origin y CSRF; **sin tokens sensibles en URLs**; SSE protegido; CSP estricta (ADR-0013) | Usuario |
| D-31 | 2026-11-08 (sesión 6) | **URLs estrictamente pasivas** (sin visitar, sin resolver DNS de dominios sospechosos, sin seguir acortadores); RDAP y reputación complementarias, no bloquean la clasificación si no están configuradas (ADR-0005, ADR-0009) | Usuario |
| D-32 | 2026-11-08 (sesión 6) | Reafirma D-24: **no elegir aún Sonnet/Opus**; decidir con pruebas comparativas de calidad, coste **y latencia**, con presupuesto autorizado (ADR-0007) | Usuario |
| D-33 | 2026-11-08 (sesión 6) | **Planificar para UN desarrollador** asistido por Claude Code y ECC (implementación independiente). Resuelve T-12; el reparto P1–P5 de `14` §1 queda histórico | Usuario |
| D-34 | 2026-11-08 (sesión 6) | **La demo principal no depende de Gmail**: se prioriza la integración real, pero el análisis manual y los conectores simulados **etiquetados** son el respaldo | Usuario |
| D-35 | 2026-11-08 (sesión 6) | **Interfaz HTML + Jinja + htmx** (htmx vendorizado, sin CDN ni Node). Resuelve T-01 (ADR-0012) | Usuario |
| D-36 | 2026-11-08 (sesión 6) | **Distribución reproducible**: venv + dependencias fijadas (`==`), sin PyInstaller. Resuelve T-08 (ADR-0014) | Usuario |
| D-37 | 2026-11-08 (sesión 6) | **Modo degradado sin IA** claramente etiquetado («análisis parcial — IA no disponible»); nada pregrabado como real (ADR-0015) | Usuario |
| D-38 | 2026-11-08 (sesión 6) | **Plan P-16 de la Fase 0 aprobado**, con ejecución **controlada por etapas** (primero F0-01/F0-02 y parada para revisión). Autorizados Python 3.12 y **solo** las dependencias de `14` §11.4, en versiones estables fijadas y licencias comprobadas. Trabajo en la rama **local** `feat/fase-0`; sin push | Usuario |
| D-39 | 2026-11-08 (sesión 6) | **T-13 → opción A**: emparejamiento manual inicial con **código aleatorio de un solo uso**, suficientemente robusto, **con caducidad y limitación de intentos**; sesión mediante **cookie segura** para el contexto local; **nunca tokens de sesión en URLs** (ADR-0013) | Usuario |
| D-40 | 2026-11-08 (sesión 6) | **T-09 → conjunto de evaluación final sellado FUERA del repositorio** de desarrollo y **no consultable por los agentes** durante la implementación; en el repo solo el procedimiento, metadatos no sensibles y su **huella SHA-256**. Los casos de **desarrollo** sí van en el repo. **No crear el conjunto final** hasta acordar su ubicación | Usuario |
| D-41 | 2026-11-08 (sesión 6) | Corrección de C-19 en `11`: arquitectura aprobada; la demo principal **no depende de Gmail**, aunque Gmail real sigue siendo integración prioritaria | Usuario |
| D-42 | 2026-11-08 (sesión 6) | **Puerto por defecto 8790**, configurable con `APP_PORT`; si está ocupado → **error claro en español** y salida con código 2; **nunca cerrar procesos ajenos ni cambiar de puerto en silencio** | Usuario |
| D-43 | 2026-11-08 (sesión 6) | F0-03 aprobada; autorizada **solo F0-04** (contratos Pydantic + `InputAdapter`). Los contratos de `backend/antifraude/contracts/` pasan a ser la fuente única (ADR-0003) | Usuario |
| D-44 | 2026-11-08 (sesión 6) | F0-04 aprobada. **Corrección de contratos**: una comprobación **opcional** no realizada (RDAP, reputación) **no impide BAJO** ni exige texto (se lista sola en `unverified_checks`); una **obligatoria** no completada bloquea BAJO y exige explicación. **Refuerzo**: BAJO imposible con evidencias de robo de credenciales, fraude de pago o toma de cuenta (cualquier severidad) o con categorías de fraude declaradas | Usuario |
| D-45 | 2026-11-08 (sesión 6) | **Parámetros de seguridad de F0-05**: código de 8 caracteres (`secrets`), un solo uso, 5 min; máx. 5 fallos con espera creciente y bloqueo hasta reiniciar; códigos nuevos limitados (no reinician los fallos); sesión con id aleatorio, cookie HttpOnly + SameSite=Strict, inactividad 30 min, máximo 8 h; Host/Origin/CSRF; sin CORS; SSE protegido; sin tokens en URLs ni en registros | Usuario |

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
| P-14 | 2026-11-08 | ~~ADR 001–011 de `13` §12~~ | **Superada por D-26** (aprobada con modificaciones; ver `docs/adr/`) |
| P-15 | 2026-11-08 | Plan de `14`: ~~reparto P1–P5~~ (superado por D-33), congelación miércoles, test sellado ejecutado una vez, Telegram bot como posible 2.º canal | Reparto superado; el resto sigue **pendiente**, ver plan para un desarrollador en `14` §11 |
| P-16 | 2026-11-08 (sesión 6) | **Plan de la Fase 0** reducido para un desarrollador (`14` §11) | **Aprobada → D-38** |
