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
| D-46 | 2026-11-08 (sesión 6) | F0-05 aprobada; commit local de restauración `28cdc3d` («feat: establish secure local backend foundation») en `feat/fase-0`, sin push. Autorizada **solo F0-06** (interfaz web accesible) | Usuario |
| D-47 | 2026-11-08 (sesión 6) | **Decisiones técnicas de F0-06** (propuestas por Claude Code dentro de la fase aprobada; revisables): htmx configurado por `<meta name="htmx-config">` con `includeIndicatorStyles=false`, `allowEval=false`, `allowScriptTags=false`, `historyEnabled=false`, `historyCacheSize=0`, `selfRequestsOnly=true` (compatibilidad con la CSP y nada de páginas en `sessionStorage`); el **token CSRF no se inserta en el HTML**: `app.js` lo pide a `GET /session` y lo guarda solo en memoria; `/pairing` y `/session/logout` añaden `HX-Redirect` (solo navegación, sin cambio de seguridad) cuando la petición viene de htmx | Claude Code (dentro de F0-06) |
| D-48 | 2026-11-08 (sesión 6) | **F0-06 aprobada** tras prueba manual del usuario en un navegador real (bienvenida, emparejamiento → panel, panel con funciones pendientes, cerrar sesión, `/panel` tras cerrar sesión → pantalla de emparejamiento). **Siguen pendientes** y no se declaran superadas: errores de CSP en consola, navegación completa con teclado, zoom al 200 % y contraste medido. Autorizada **solo F0-07** | Usuario |
| D-49 | 2026-11-08 (sesión 6) | **Correcciones de F0-07** (defectos documentados): (1) errores internos no controlados → respuesta genérica en español y registro solo de tipo, archivo:línea y ruta, **nunca el mensaje** (antes Uvicorn registraba la traza completa); (2) configuración inválida → mensaje en español sin valores y salida con código 2 (antes, traza de Python); (3) registros de Uvicorn y de la app con un **filtro de ocultación** (cookies, cabeceras sensibles, claves `sk-ant-…`, tokens de 43 caracteres, códigos de emparejamiento) que además elimina trazas de excepción. Sin carga de `.env` (sin dependencias nuevas) | Claude Code (dentro de F0-07) |
| D-50 | 2026-11-08 (sesión 6) | **F0-07 aprobada**. Verificado que `.env*` está ignorado y `.env.example` es versionable (sin cambios en `.gitignore`) y sin credenciales. Commit local de restauración «feat: complete secure antifraud interface and configuration» (F0-06 + F0-07), sin push. Autorizada **solo F0-08** (banco de evaluación + 3 casos sintéticos de demo) | Usuario |
| D-51 | 2026-11-08 (sesión 6) | **F0-08 (decisiones técnicas dentro de la fase):** formato de casos como contrato Pydantic `EvalCase` (`contracts/evaluation.py`, fuente única) en archivos JSONL; casos solo con **dominios reservados** (`.example`, `.test`…) y entidad ficticia «Banco Ficticio»; casos de IA marcados `synthetic_ai` y métricas separadas (R-26); `.gitignore` **reforzado** para impedir versionar el conjunto sellado (`eval/datasets/test_sealed/`, `eval/sealed/`, `*.sealed.jsonl`); el conjunto sellado **no se crea** (T-14) | Claude Code (dentro de F0-08) |
| D-52 | 2026-11-08 (sesión 6) | **F0-08 aprobada**; los 3 casos siguen **pendientes de revisión humana** del contenido completo. Observaciones: en `dev-0001` SPF/DKIM/DMARC son simulados y no equivalen por sí solos a legitimidad; todos los enlaces sintéticos usan dominios reservados y no se resuelven ni visitan; **no calcular métricas** todavía. Autorizada **solo F0-09** (directorio de entidades) | Usuario |
| D-53 | 2026-11-08 (sesión 6) | **F0-09 (decisiones técnicas dentro de la fase):** esquema `FinancialEntity` (`contracts/entities.py`) con estados `verified` / `pending_verification` / `fictitious`; **una entidad pendiente no puede tener dominios** y una verificada exige fuente https y fecha; las ficticias solo usan dominios reservados, su id empieza por `ficticio` y **no se cargan por defecto**; consultas en `intel/entities.py` con coincidencia **exacta** de host (o subdominio real solo si `include_subdomains`), sin parciales, sin no-ASCII, puertos ni comodines; nombres/alias por coincidencia exacta normalizada; Santander, BBVA, CaixaBank, Sabadell y Bankinter preparados **sin dominios** (pendientes, V-27) | Claude Code (dentro de F0-09) |
| D-54 | 2026-11-08 (sesión 6) | **F0-09 considerada aprobada** y **mandato de desarrollo autónomo** hasta el MVP (etapas A–F) sin aprobación por tarea menor, con límites: commits **solo locales**, sin push/PR, sin dependencias nuevas, sin APIs de pago sin presupuesto, sin datos reales, sin análisis activo, sin hooks/MCP desactivados, sin bucles ilimitados, sin acceso al test sellado; preguntar solo por seguridad/privacidad, arquitectura mayor, credenciales, instalaciones, gasto, publicación o acciones irreversibles. Seguimiento en `15_SEGUIMIENTO.md` | Usuario |
| D-55 | 2026-11-08 (sesión 6) | **Decisiones técnicas del desarrollo autónomo (D-54), revisables por el usuario:** (1) cliente de Claude **solo con el SDK oficial** `anthropic` (no instalado → IA «no configurada»; sin HTTP propio), con esfuerzo `low`, salida JSON estricta y `fallbacks: "default"` ante rechazos (se registra el modelo que respondió); (2) **modo demostración** `APP_DEMO_MODE` (off por defecto) que carga la entidad ficticia y 3 ejemplos etiquetados; (3) historial de sesión **sin texto** de los mensajes; (4) ALTO solo por combinaciones críticas (señuelo grave + corroboración, ADR-0006), nunca por acumulación; (5) la mención de un banco en el cuerpo desde otro dominio es señal **baja** (solo corrobora); (6) correcciones de 3 revisiones independientes (Python, seguridad, accesibilidad) con pruebas de regresión | Claude Code (D-54) |
| D-45 | 2026-11-08 (sesión 6) | **Parámetros de seguridad de F0-05**: código de 8 caracteres (`secrets`), un solo uso, 5 min; máx. 5 fallos con espera creciente y bloqueo hasta reiniciar; códigos nuevos limitados (no reinician los fallos); sesión con id aleatorio, cookie HttpOnly + SameSite=Strict, inactividad 30 min, máximo 8 h; Host/Origin/CSRF; sin CORS; SSE protegido; sin tokens en URLs ni en registros | Usuario |

## Superadas / revocadas (resumen)
- D-02 («la idea aún no está decidida») → **superada por D-09**.
- D-04 (límites de la inicialización de la sesión 1) → cumplida; sustituida por D-20.
- P-11 (índice 0–100) → **superada por D-14**. P-12 (MVP v1 con voz, BancoNova, Opus) → **superada por D-12/D-14 y P-14**.

| D-56 | 2026-11-08 (sesión 6, misión 2) | **Misión autónoma 2 (finalización del MVP sin credenciales ni pagos).** Decisiones técnicas tomadas dentro del mandato, revisables por el usuario:
(1) Cambios de etiquetas dev justificados y trazados en `eval/CAMBIOS_ETIQUETAS.md` (dev-0009, dev-0015, dev-0027). Los casos con nivel esperado NO CONCLUYENTE se informan aparte y no cuentan como falsos positivos.
(2) Reglas `rules-0.2.0` tras la prueba adversarial. La negación solo anula su propia cláusula. Los consejos de seguridad («nunca facilite…») no son peticiones. Teclear un OTP en el propio servicio no es compartirlo, salvo que sea en un enlace o una respuesta. «Hijo con número nuevo» es un señuelo grave.
(3) **No** se implementa «≥2 evidencias altas de fuentes distintas ⇒ ALTO», porque marcaba como ALTO a proveedores legítimos. El motor rebaja ALTO a MEDIO si no hay evidencia alta.
(4) Límite de 30 análisis por minuto y sesión.
(5) Las pruebas del `.gitignore` se hacen en un repositorio temporal, para que la suite pase desde el ZIP.
(6) El PDF se genera con Edge sin interfaz (perfil temporal, sin red de fondo) y el PPTX con PowerPoint COM; sin dependencias nuevas. |

| D-57 | 2026-11-08 (sesión 6, misión 3) | **Misión autónoma 3 (robustecimiento).** Decisiones dentro del mandato, revisables por el usuario:
(1) **Control de gasto de la IA:**
- IA desactivada por defecto y gasto **autorizado 0 USD** (el previsto, 0,50 USD, NO está autorizado).
- Sonnet 5.5 como modelo previsto para las primeras pruebas; Opus bloqueado salvo `AI_ALLOW_OPUS=1`. El modelo sigue siendo configuración sin valor por defecto; ADR-0007 no cambia.
- Sin *fallback* de modelo y sin reintentos.
- Reserva del peor caso en un libro de gasto fuera del repositorio; una solicitud a la vez.
(2) **Bancos reales:** dominios web del Registro de Entidades del Banco de España con **cobertura parcial**. Otro dominio con el nombre del banco produce incertidumbre (MEDIO), no imitación segura; un dominio oficial incrustado en otro sigue siendo crítico.
(3) **Reglas `rules-0.3.0`:**
- La urgencia sola es una señal leve, pero sigue corroborando señuelos.
- Las multas y deudas solo cuentan con enlace o teléfono.
- Un organismo público con enlace no verificable (salvo `.gob.es`) nunca da BAJO.
(4) **Contenido largo:** se revisan el principio y el final, y el análisis se declara parcial (`ingest.complete`).
(5) **Evaluación:** el ejecutor reproducible exige `--confirmar-gasto` para la IA. El modo sellado va fuera del repositorio, con huella y una sola ejecución.
(6) **Gmail:** máximo 40 mensajes por consulta, por la cuota; cola de pendientes sin pérdidas silenciosas. |

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
