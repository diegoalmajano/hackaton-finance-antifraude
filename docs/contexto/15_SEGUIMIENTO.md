# 15 — Seguimiento del desarrollo autónomo hacia el MVP (D-54, misión 2)

> Estado vigente de cierre, 10-11-2026: rules-0.3.5, 926 Python / 11 JS / 8 SDK Gmail simulados. Rama codex/cierre-mvp, base compartida c013f5b, sin publicación nueva. Evidencia y pendientes: [CIERRE_MVP_2026-11-10.md](../CIERRE_MVP_2026-11-10.md). Las secciones fechadas anteriores son históricas.

> Documento vivo para retomar el trabajo si se interrumpe la sesión. Actualizar al cerrar cada bloque.
> Estado vigente: Codex, rama `feat/fase-0`; publicación inicial completada. El registro de misiones anteriores se conserva como histórico; sus menciones a «sin push» no son bloqueos actuales.

## Cómo retomar
1. Leer `CLAUDE.md` → este archivo → `09_PENDIENTES.md`.
2. `git log --oneline -15` y `git status` (añadir archivos **solo por ruta explícita**; nunca `git add -A`).
3. `.\.venv\Scripts\python.exe -m pytest` → debe coincidir con el total registrado abajo.
4. Continuar por «Próxima acción».

## Estado por etapa (2026-11-08, cierre de la misión 2)
| Etapa | Estado | Resultado verificable |
|---|---|---|
| A — Cerrar Fase 0 (F0-10) | ✅ | README completo, `.gitattributes` (vendor intacto) |
| B — Motor de detección | ✅ | ingesta texto/.eml/HTML, minimización, enlaces pasivos, reglas `rules-0.2.0`, motor determinista, alertas en 2 fases; prueba adversarial aplicada |
| C — Integración de IA | ✅ (simulada) | cliente Claude auditado frente a la documentación oficial (`docs/AUDITORIA_CLAUDE_API.md`); **0 llamadas reales** |
| D — Experiencia de usuario | ✅ | `/analizar`, resultado explicado, modo demo etiquetado, límite de análisis por sesión |
| E — Gmail | 🟡 preparado y simulado / ⛔ real bloqueado | `GmailApiClient`, `GmailPoller`, guía `docs/GMAIL_CONFIGURACION.md`; `build_gmail_service` **no probado** (faltan librerías y OAuth) |
| F — Evaluación y entrega | 🟡 | etiquetas revisadas (`eval/CAMBIOS_ETIQUETAS.md`), metodología independiente (`eval/METODOLOGIA_INDEPENDIENTE.md`), PPTX y PDF generados, ZIP local probado desde carpeta limpia; **falta**: push (ZIP oficial), conjunto sellado y revisión humana |

## Registro de tareas
| Tarea | Responsable | Archivos principales | Pruebas | Estado / commit |
|---|---|---|---|---|
| Commit F0-08/F0-09 | Coordinador | eval/, backend/data/, contracts/entities.py, intel/entities.py | 286 ✅ | `71c55e2` |
| 24 casos dev sintéticos | **Agente de datos** (no leyó el detector) | eval/datasets/dev/casos_dev.jsonl | ✅ | `4c96eaa` |
| F0-10 + motor (B) | Coordinador | analysis/*, intel/urls.py, risk/engine.py, app/pipeline.py, evaluation.py | 334 ✅ | `4c96eaa` |
| Revisión Python del motor | **Agente python-reviewer** (solo lectura) | 12 hallazgos | — | `dcecc13` |
| IA (C) + interfaz (D) | Coordinador | ai/*, app/analysis_routes.py, templates | 391 ✅ | `dcecc13` |
| Gmail simulado (E) + métricas (F) | Coordinador | connectors/gmail.py, evaluation.py | 397 ✅ | `f6bc959` |
| Revisión de seguridad | **Agente security-reviewer** | 10 hallazgos | 30 regresiones | `409b1d2` |
| Revisión de accesibilidad | **Agente a11y-architect** | 12 hallazgos | 9 regresiones | `b46ffa4` |
| **M2** Auditoría API de Claude (sin llamadas) | Coordinador + documentación oficial | ai/prompt.py, ai/claude.py, docs/AUDITORIA_CLAUDE_API.md | +3 | `63c66cf` |
| **M2** Gmail preparado para OAuth | Coordinador | connectors/gmail_api.py | +7 (simuladas) | `03c3b02` |
| **M2** Revisión ciega de etiquetas + metodología independiente | **Agente revisor** (sin acceso al detector) + coordinador | eval/*, evaluation.py | ✅ | `ca7ce26` |
| **M2** Límite por sesión, aviso de idioma, ancho completo | Coordinador | app/*, analysis/* | 450 ✅ | `b4a2c92` |
| **M2** Prueba adversarial (caja blanca, ~140 casos) | **Agente probador** (solo lectura) | informe A1–A18, P1–P7 | — | — |
| **M2** Corrección adversarial + PPTX + ARQUITECTURA | Coordinador | rules.py, text.py, engine.py, tests/test_b_regresiones_adversariales.py, docs/entrega/* | 528 ✅ | `dfdbce7` |
| **M2** PDF de una cara | Coordinador | docs/entrega/resumen_una_cara.html → PDF | — | `2173992` |
| **M2** Prueba desde carpeta limpia (ZIP de `git archive`) | Coordinador | tests/conftest.py | 528 ✅ en repo y en copia limpia | `ea3c064` |

## Prueba adversarial: qué se corrigió y qué no
- **Corregido** (78 regresiones con las cadenas literales del informe): A1–A11, A14–A16, A18 (falsos negativos) y P1–P4 (consejos de seguridad, OTP que se teclea en el propio servicio, mención de la tarjeta sin pedirla, aviso de cargo que remite al canal oficial).
- **Decisión:** la regla «≥2 evidencias altas de fuentes distintas ⇒ ALTO» que prometía el docstring **no se implementó**, porque subía a ALTO la encuesta ambigua de un proveedor externo (dev-0027). Se corrigió el docstring. Además, el motor rebaja ALTO a MEDIO si no hay ninguna evidencia alta, en vez de romper el contrato.
- **Abierto (riesgo documentado):**
  - P5: un correo oficial con enlaces de terceros sale MEDIO.
  - P6: un tercero que menciona un banco y pone un enlace sale MEDIO.
  - P7: los mensajes informativos quedan en NO CONCLUYENTE sin IA.
  - A12: no se detectan imitaciones de bancos reales hasta verificar sus dominios.
  - A17: los enlaces a `.apk`/`.exe` no son señal propia; solo se cubren si el texto pide instalar la app.

## Métricas de DESARROLLO (no son evaluación; motor ajustado con estos casos; sin IA)
- 27 casos: 14 deben alertar, 10 legítimos y 3 ambiguos (se informan aparte).
- VP=14 FP=0 FN=0 VN=10. Recall 1,00 (IC95 % Wilson 0,78–1,00). Tasa FP 0,00 (IC95 % 0,00–0,28). Nivel aceptable 27/27.
- Latencia local p95 ≈ 1 ms. Coste: no medido.
- **No es una evaluación independiente:** el motor se ajustó con estos mismos casos, que son sintéticos.

## Incidencias
- `backend/_poc1.py` entró por error en `dcecc13` (`git add -A`); se retiró en `409b1d2`. Desde entonces solo se añaden rutas explícitas.
- Hay un intérprete Python 3.14 inactivo (PID 4208400, `pythoncore-3.14-64`, iniciado a las 19:32) que dejó un comando de shell mal construido. El clasificador denegó cerrarlo: **lo debe cerrar el usuario**.
- (M2) Desde el ZIP, 6 pruebas fallaban porque usaban `git check-ignore` y el ZIP no trae `.git`. Corregido en `ea3c064`.

## Bloqueos y autorizaciones pendientes del usuario
- **IA real:** instalar `anthropic` (SDK oficial) + clave + **presupuesto** para la comparativa Opus/Sonnet (D-24, D-32).
- **Gmail real:**
  - Proyecto GCP, cliente OAuth «Desktop» y cuenta de pruebas (B-04).
  - Instalar `google-auth-oauthlib`, `google-api-python-client` y `keyring`.
- **Dominios bancarios reales:** verificación en fuente oficial (V-27/T-10). Cierra A12.
- **Publicación:** push a GitHub (el ZIP oficial se descarga de GitHub).
- **Revisión humana** de los 27 casos sintéticos (R-47).
- Nombre del producto; hora de cierre del hackatón (Q-01); cerrar el proceso Python 3.14 inactivo.

## Total de pruebas (misión 2): **528**. Ver la sección de la misión 3 para el total vigente.

## Próxima acción
Esperar las autorizaciones del usuario (sección «Bloqueos»). Sin ellas, lo más útil es:
1. Revisión humana de los casos.
2. Prueba manual en navegador: teclado, zoom 200 %, consola CSP y lector de pantalla.
3. Corregir P5–P7.
4. Push y ZIP oficial cuando se autoricen.

## Misión 3 (robustecimiento) — registro vivo
| Tarea | Estado | Commit |
|---|---|---|
| A — Control de costes de la API (sin llamadas reales) | ✅ `ai/budget.py`, `docs/CONTROL_COSTES_IA.md`; 31 pruebas simuladas. **Gasto real: 0 USD** | `6dbfea3` |
| E — Gmail: duplicados acotados, fallos comunicados, keyring seguro, desconexión | ✅ (simulado) | `6dbfea3` |
| D — Revisión de seguridad (agente, solo lectura): 2 ALTOS, 3 MEDIOS, 4 BAJOS | ✅ corregidos: relleno → cabeza+cola y parcial; cabeceras CR/LF; límite antes de minimizar; nombre mostrado minimizado y dentro del bloque; citas ≥8 caracteres; contactos fuera del texto libre de la IA; frecuencia atómica; SSE revalidado; OSV: 0 vulnerabilidades | `86b22c0` |
| B — Ronda adversarial 3 (agente, ~245 casos) | ✅ `rules-0.3.0`; 66 regresiones + 1 `xfail` (limitación); `docs/LIMITACIONES_DETECCION.md` | `502337f` |
| C — Dominios bancarios reales | ✅ 5 webs del Registro de Entidades del Banco de España (05/11/2026), cobertura parcial; `docs/DOMINIOS_BANCARIOS.md`. Revisión humana pendiente | `34f2540` |
| E — Pruebas de integración real (Claude y Gmail) | ✅ preparadas y saltadas por defecto; `docs/PRUEBAS_INTEGRACION_REAL.md` | `5944318` |
| F — Evaluación reproducible (reglas frente a Claude; sellado) | ✅ `python -m antifraude.evaluation --modo/--sellado`; `eval/EJECUCION.md` | `5944318` |
| E — Gmail: mensajes por encima del máximo y errores transitorios se perdían | ✅ cola de pendientes; máximo 40 por consulta (cuota) | `5944318` |
| Revisión independiente del control de gasto (agente, solo lectura) | ✅ sin caminos que eviten el control. Corregidos: 2 ALTOS (libro borrado reiniciaba el presupuesto → copia `.bak` y re-apunte; gasto negativo o no finito aceptado → libro dañado) y MEDIOS (estimación por bytes UTF-8, `PermissionError` del bloqueo en Windows, pago duplicado entre hilos, carrera del bloqueo caducado, libro dentro del repositorio) y BAJOS (4xx no facturables explícitos, respuesta pagada conservada, marca del sellado previa, aviso de presupuesto insuficiente) | ver commit siguiente |

Total de pruebas (misión 3): **674** en verde + 4 de integración real saltadas + 1 `xfail`.


## Actualización de traspaso a Codex — 08-11-2026
- Publicación autorizada en esta solicitud: rama feat/fase-0 subida y verificada en el remoto privado (58bc5f9); el bloqueo histórico del primer push queda cerrado.
- Continuación con Codex según AGENTS.md y docs/TRASPASO_CODEX.md; ECC no se ejecuta ni se requiere.
- Verificación local: 674 pruebas correctas, 4 saltadas y 1 fallo esperado; Anthropic desactivado, presupuesto 0 USD, ninguna llamada real durante el traspaso.
- Las autorizaciones de IA/Gmail reales, revisión humana y evaluación independiente siguen pendientes. No se cambia el proveedor de IA de la aplicación.


## Continuación con Codex — accesibilidad parcial, 08-11-2026
- Git inicial: `feat/fase-0` limpia, HEAD y referencia local de origin en `71c5917`; no se consultó el remoto ni se publicó.
- Línea base repetida: **674 passed, 4 skipped, 1 xfailed, 1 warning**; IA y pruebas reales desactivadas, presupuesto cero.
- Siguiente pendiente concreto: **R-58/V-26**, accesibilidad del flujo local. Criterios y protocolo en [ACCESIBILIDAD_CODEX.md](../ACCESIBILIDAD_CODEX.md).
- Contraste calculado sobre la paleta CSS: pares de texto/bordes revisados superan los objetivos; foco sobre cabecera requiere comprobar el conjunto contorno/halo y colores forzados. R-43/R-58/V-26 siguen abiertos.
- No se ha operado un navegador ni lector de pantalla. Revisión humana R-47, integraciones reales y evaluación independiente siguen pendientes; conjunto sellado no leído.
- Solo documentación en este bloque; sin cambios de comportamiento, dependencias, proveedor, commit, push ni PR.


## Accesibilidad con Codex — navegador y correcciones, 08-11-2026
- Conservados los cinco documentos locales pendientes al inicio; rama `feat/fase-0`, HEAD `71c5917`, sin commit/push/PR.
- Corregidos A11Y-01 (anuncio de espera persistente tras fallos; cancelación de temporizadores) y A11Y-02 (asociar error al campo de conexión y selector de archivo). Cambios limitados a JS y dos plantillas, sin cambios de motor, proveedor ni seguridad.
- Navegador local: salto, emparejamiento, Tab/Shift+Tab, validación vacía, análisis de texto/ejemplo, foco de resultado, desplegable con Espacio, desconexión real controlada y cierre con /panel protegido. Reflujo parcial a 320 px sin desbordamiento de página.
- Python: **675 passed, 4 skipped, 1 xfailed, 1 warning**. JS opcional con Node ya instalado: **9 correctas**, DOM/temporizadores simulados (no lector de pantalla).
- R-58/V-26/R-43/V-25 siguen abiertos: zoom real 200 %, lector de pantalla, colores forzados, cobertura completa de contraste, .eml en navegador/prioridad y cabeceras reales. El envío automatizado de .eml falló; causa sin confirmar, no se da por validado.
- Evidencia y matriz vigente: [ACCESIBILIDAD_CODEX.md](../ACCESIBILIDAD_CODEX.md), sección «Segunda revisión». IA desactivada, presupuesto cero, integraciones reales bloqueadas; sin llamadas de pago ni lectura del sellado. Servidores propios y pestaña temporal cerrados.


## Misión: versión demostrable local (en curso, 08-11-2026)
Autorización: misión adjunta del usuario, sin commit/push/PR/publicación. Instalaciones solo con autorización específica: el entorno temporal fue autorizado después, como se registra abajo. Se conserva todo el trabajo local.

| Hito / criterio obligatorio | Estado | Evidencia / criterio de cierre |
|---|---|---|
| H1 Punto de partida y suites existentes | Comprobado | Baseline real: 675 Python + 9 JS; trabajo local conservado |
| H2 Demo completa sintética | Comprobada por HTTP/CLI; interfaz parcial en H3 | Uvicorn real, cuatro .eml, prioridad, validación, historial/cierre, reinicio/recuperación; usuario confirma panel y ejemplo 2 |
| H3 Accesibilidad | **Parcial, diferida a fase final por el usuario; no bloquea trabajo técnico** | Usuario confirma zoom 200 % y anuncio de error vacío; IAB verifica .eml, reflujo 320 y cabeceras/CSP. Faltan Narrador audible completo, contraste Windows y recorrido/diálogo manual; matriz vigente en cuarta revisión de ACCESIBILIDAD_CODEX |
| H4 P5-P7 y R-64 | Correcciones y límites validados | 35 regresiones: R-64 y atribución P6 corregidos; P5 proveedores no representados y P7 incertidumbre de destino/sin IA delimitados. R-69 validado con 30 pruebas simuladas |
| H5 Entrega coherente | Comprobada | Fuentes y materiales a 746 Python + 11 JS, rules-0.3.2; 12 diapositivas y PDF de una cara inspeccionados, accesibilidad parcial e IA/Gmail sin uso real |
| H6 Reproducibilidad y revisión local | Comprobada | clean-fuente-3: 163 fuentes, 746 Python + 11 JS y CLI/demo/recuperación correctos con el entorno nuevo autorizado; diff revisado, sin staged ni publicación |

No declarar superadas comprobaciones pendientes. La decisión posterior del usuario difiere H3 a la fase final y suspende nuevas solicitudes manuales; H1/H2/H4/H5/H6 cierran el bloque técnico actual, sin certificar accesibilidad completa ni entrega final al hackatón.


### Evidencia de instalación y copia limpia
- Fuentes: `C:/Users/dialm/Documents/ChatGPT/Hackaton/.mvp-build/clean-fuente-1`; 162 archivos seleccionados con `git ls-files -c -o --exclude-standard` y filtros explícitos, hashes SHA-256 por archivo. Incluye fuentes actuales, pruebas nuevas, cuatro .eml y materiales corregidos; sin archivos ignorados, .git, .venv ni datasets distintos de dev. No se usa `git archive HEAD`.
- Entorno **nuevo**, creado sin paquetes y comprobado antes de instalar: `.../.mvp-build/instalacion-limpia/.venv`. El usuario autorizó exclusivamente allí pip y requirements.lock; instalación completada. `pip check`: sin requisitos rotos; las **26 versiones del lock coinciden**. Python 3.12.10; SDK de Anthropic/OpenAI y librerías reales de Gmail ausentes. Entorno y requisitos del repositorio sin cambios.
- Desde la copia, con el intérprete existente: **709 passed, 4 skipped, 1 xfailed, 1 warning** en 14,45 s y **9 JS correctas**. Desde el entorno nuevo: **709 passed, 4 skipped, 1 xfailed, 1 warning** en 13,01 s y **9 JS correctas**. Flags seguras y clave/modelo retirados en ambas.
- CLI real `python -B -m antifraude` ejecutado desde backend de la copia, con APP_DEMO_MODE=1 y puerto libre de loopback: emparejamiento, .eml BAJO/ALTO/ALTO/NO CONCLUYENTE, cierre y /session protegido; proceso propio detenido y conexión fallida detectada; reinicio con nuevo emparejamiento y análisis correcto. Repetido con el intérprete del entorno nuevo. Se comprobó que antifraude se importaba desde la copia. Códigos/tokens solo en memoria.
- Primer diagnóstico de desconexión esperaba ConnectError y Windows devolvió ConnectTimeout; se corrigió **solo el script temporal** para admitir ambos tipos de conexión fallida. No se modificó ni ocultó un fallo del producto. Todos los procesos propios de esa verificación terminaron.
- Evidencias locales sin secretos: `.mvp-build/manifest-fuente-1.json`, `cli-smoke.json`, recibo `validation3.json` del PPTX y renders de PDF/diapositivas. Fuera del repositorio, no se publican. PPTX: paquete/geometría/reimportación correctos; 12 diapositivas inspeccionadas y contenido cotejado con JSON. PDF: una página A4 y render inspeccionado.
- Confirmación humana: zoom 200 % legible y usable sin barra horizontal en escenario probado; Narrador anunció error vacío; bienvenida/panel y ejemplo 2 con advertencias correctos. **Faltan** los anuncios de espera/resultado porque el usuario no puede escuchar audio ahora, el recorrido completo de teclado, versiones, contraste Windows, reflujo 320 completo y consola/cabeceras del navegador. No sustituir esas pruebas por HTTP/DOM ni declarar WCAG.
- No se ha hecho rediseño visual de la aplicación. Meta **activa, no completada**, a la espera de las comprobaciones indispensables de H3. Sin commit, push, PR ni publicación.


### Continuación: reflujo, .eml y cabeceras reales en IAB
- Defectos reproducidos y corregidos: A11Y-03 (nombre de archivo no visible a 320 px) y A11Y-04 (NO CONCLUYENTE partido dentro de palabra). Texto asociado al selector con textContent; ajuste de relleno/espaciado estrecho sin reducir fuente. Sin rediseño visual definitivo.
- Navegador integrado real a 320×800: cuatro .eml BAJO/ALTO/ALTO/NO CONCLUYENTE; prioridad del archivo, nombre largo completo, error de extensión, recuperación por recarga y texto MEDIO; clientWidth/scrollWidth 305/305 en entrada, panel y resultados. Teclado automatizado en controles y detalles; foco de 4 px y halo visible. No sustituye diálogo nativo/manual ni Narrador.
- Cabeceras emitidas por el navegador observadas con envoltorio ASGI temporal: Origin válido, Sec-Fetch-Site same-origin, CSRF presente en operaciones protegidas y CSP correcta. Consola sin infracciones CSP; 400/401 de pruebas deliberadas. Solo booleanos/estados en evidencia, sin valores secretos. V-25 comprobado para las operaciones IAB ensayadas.
- Nuevas suites del repositorio: **710 passed, 4 skipped, 1 xfailed, 1 warning** en 13,92 s; **11 JS correctas**. Añadida una regresión Python de estado inicial y dos JS para nombre completo/literal y retirada de selección simulada.
- Matriz vigente: **cuarta revisión** de ACCESIBILIDAD_CODEX. Faltan Narrador completo audible/versiones y tema de contraste de Windows; también verificación manual de teclado/diálogo y revisión del ajuste en el viewport de zoom humano si corresponde. Solicitadas dos comprobaciones concretas al usuario; meta sigue abierta.
- Instancia y pestaña propias de esta comprobación cerradas; viewport restablecido. Entorno original y dependencias fijadas sin cambios, IA/presupuesto/integraciones reales a cero. La copia de reproducción se está revalidando con las fuentes actuales tras estas correcciones.


### Revalidación terminada tras A11Y-03/A11Y-04
- Fuentes actuales en `.mvp-build/clean-fuente-2`: **710 passed, 4 skipped, 1 xfailed, 1 warning** en 13,25 s y **11 JS correctas** con el entorno limpio ya instalado; sin nuevas instalaciones. CLI/demo/cierre/desconexión/reinicio correctos. Manifiesto por hashes y `cli-smoke-2.json` sin secretos.
- PPTX actualizado a 710/11: 12 diapositivas, paquete/geometría/reimportación correctos (recibo validation4.json), diapositiva modificada renderizada e inspeccionada, todas las cadenas cotejadas con JSON. PDF actualizado: una página, 710 y 11 comprobados por extracción y render inspeccionado. Sin ejecución nativa de PowerPoint.
- Versiones instaladas leídas de metadatos: Narrador ProductVersion 10.0.26100.9949 y Brave ProductVersion 157.1.99.55; no se atribuyen a la prueba humana sin confirmación.
- Meta todavía abierta por las comprobaciones manuales solicitadas. El trabajo automático ejecutable de este bloque está terminado; no se repiten suites ni se implementa un rediseño para sustituir las pruebas que faltan. Sin commit/push/PR, IA y presupuesto cero.


## Decisión del usuario: accesibilidad diferida a fase final
- No implementar lectura de pantalla propia, voz ni reproducción de audio. Se conserva compatibilidad básica con lectores mediante HTML semántico, etiquetas y atributos accesibles.
- No dedicar más tiempo por ahora a Narrador ni solicitar pruebas manuales de accesibilidad. Los anuncios auditivos pendientes, el tema de contraste elevado y el recorrido manual completo siguen **no verificados**, no superados.
- Simplificación visual y diseño definitivo reservados para la etapa final. La validación completa de accesibilidad/usabilidad se retomará antes de presentar el proyecto.
- Estas comprobaciones **no bloquean el trabajo técnico autorizado actual**. Prioridad: detector, fiabilidad, seguridad y preparación de integraciones. Esto no autoriza APIs de pago, claves reales, OAuth real, SDK nuevos, cambiar proveedor ni publicación; continúan las restricciones existentes.


### Siguiente hito técnico: R-69, cuota de Gmail
Problema reproducible: el adaptador convierte todo 403 en autorización fallida; los 429 de descarga siguen el camino genérico que puede agotar intentos de un mensaje aunque el problema sea de cuota. Criterios: motivos explícitos de cuota 403 y 429 no piden reautorizar; estado de error visible; conservar pendientes/historial y no marcar mensajes como vistos por agotamiento de cuota; cortar el lote sin reintento inmediato; recuperar sin duplicados al cesar la cuota. 401 y 403 desconocidos/de permisos conservan el tratamiento de autorización. Todo con servicio simulado, sin SDK/OAuth/API real.


### Siguiente corrección del detector: P6, mención frente a identidad declarada
Se ha localizado una contradicción del contrato: pipeline pasa como claimed_entity_id la primera entidad mencionada en cualquier parte del cuerpo. El contrato exige la entidad que el mensaje dice ser. Criterio antes de corregir: una revista/persona que solo menciona un banco no genera evidencia de que su enlace suplante a ese banco. Con IA requerida ausente seguirá NO CONCLUYENTE/parcial, no se concederá BAJO por confianza. La identidad del nombre del remitente o dominio oficial seguirá sustentando la comparación; señuelos sensibles, imitaciones y errores conservan sus mínimos. Regresiones y corpus dev sin cambiar etiquetas.


## Estado técnico vigente tras R-69 y P6 (sin publicar)
- `rules-0.3.2`: P6 corregido de forma acotada. Una mención bancaria en el cuerpo no se convierte en identidad del remitente; el nombre/dominio oficial aportan contexto sin autenticar ni crear una excepción de confianza. Cinco fallos reproducidos antes de corregir; 35 regresiones P5–P7/R-64 en verde después. P5 y P7 mantienen sus límites documentados.
- R-69: 403 de cuota explícita y 429 separan cuota de autorización; se detiene el lote y se conservan pendientes sin agotar intentos de mensaje. 30 regresiones nuevas con servicio simulado, incluyendo historial/descarga/recuperación. SDK, OAuth y cuenta real siguen sin usar; espera adaptativa e integración al panel pendientes antes de activar Gmail.
- Suite completa: **746 passed, 4 skipped, 1 xfailed, 1 warning** en 13,19 s; **11 JS correctas**. No nuevos skips ni etiquetas dev modificadas. Los 27 casos dev mantienen nivel aceptable 27/27 (VP14, FP0, FN0, VN10; tres ambiguos aparte): **desarrollo, no evaluación independiente**. Sellado no leído.
- Accesibilidad manual auditiva, contraste elevado y recorrido completo: **no verificados**, diferidos por decisión del usuario a la fase final; no bloquean trabajo técnico. Se conservan controles semánticos; sin voz/audio ni rediseño definitivo.
- IA/presupuesto/integraciones reales a cero, proveedor y entorno del proyecto conservados. Sin commit, push, PR ni publicación. Reproducción final y materiales se revalidan tras estas correcciones.


### Cierre del bloque técnico autorizado actual
- Reproducción final: `.mvp-build/clean-fuente-3`, 163 fuentes actuales seleccionadas, entorno temporal nuevo ya autorizado (sin reinstalar). **746 passed, 4 skipped, 1 xfailed, 1 warning** en 13,08 s; **11 JS correctas**. CLI real desde la copia: cuatro .eml BAJO/ALTO/ALTO/NO CONCLUYENTE, cierre protegido, desconexión y recuperación tras reiniciar. Todos los procesos propios terminados; códigos/tokens solo en memoria.
- PPTX: 12 diapositivas; cambio de cifras renderizado e inspeccionado; paquete, geometría y reimportación correctos (validation5.json); todas las cadenas cotejadas con JSON. PDF: una página A4, 746/11 comprobados por extracción y render inspeccionado. Materiales coherentes, sin afirmar integración real ni accesibilidad completa.
- Diff revisado: código, pruebas y fuentes/materiales; `git diff --check` sin errores. Se conserva el trabajo local previo; no hay archivos preparados en el índice. HEAD 71c5917 y rama feat/fase-0 conservados; sin commit/push/PR. Solo documentación de evidencia y comentario histórico se ajustaron después de la última suite; no cambió comportamiento.
- **Bloque técnico actual completado**, con accesibilidad manual diferida expresamente por el usuario. No equivale a aprobación final para presentar: siguen no verificadas las pruebas auditivas, contraste elevado y recorrido manual completo, reservadas para la fase final. Sin más solicitudes manuales en esta fase.
- Próximos trabajos fuera de este bloque: validación humana de casos, completar fuentes bancarias y evaluación independiente. SDK/OAuth/Gmail real o IA con presupuesto requieren autorización específica. Nada de ello se considera realizado ni se activa en este bloque.


## Consolidación autorizada en GitHub privado — 09-11-2026
El usuario autoriza un commit con el progreso revisado y push exclusivamente de feat/fase-0 a origin, sin force, merge ni cambios en main o visibilidad. Esta autorización sustituye para esta consolidación los avisos históricos de «sin autorización para commit/push»; no autoriza futuras publicaciones ni una nueva fase de desarrollo.

Comprobaciones previas al commit:
- Destino efectivo de fetch y push: https://github.com/diegoalmajano/hackaton-finance-antifraude.git. GitHub confirma visibility=private. Rama remota y HEAD inicial coinciden en 71c59178a9a20a8f55495d39399601c123c9357c; main solo existe localmente.
- 37 archivos candidatos explícitos: 28 modificados y 9 nuevos; código, tests, AGENTS.md, documentación, cuatro correos sintéticos y materiales. Revisión de patrones y de contenido, incluido PDF extraído y miembros descomprimidos del PPTX: sin secretos reales detectados con este alcance. Sin objetos incrustados en el PPTX. No es garantía absoluta para cualquier formato de secreto.
- Exclusiones comprobadas: .env y variantes, credenciales/tokens/clave privada, .venv, cachés, ZIP, temporales, exportaciones/mensajes privados y conjunto sellado. Los temporales de la misión permanecen fuera del repositorio y no se añaden; el sellado no se lee.
- Revalidación: 746 passed, 4 skipped, 1 xfailed, 1 warning en 20,19 s y 11 JS correctas. Integraciones reales bloqueadas; IA=0, presupuesto=0, sin claves reales ni APIs de pago. Ningún cambio funcional nuevo en esta consolidación.
- Se preparan solo rutas explícitas y se comprueba el índice antes del commit. El resultado del push y la coincidencia del commit local/remoto se verificarán al terminar; no se presupone su éxito en esta nota previa.

## Estado vigente — cierre técnico local del 09-11-2026

La continuación autorizada del MVP parte de `dd3e4fb` y conserva el trabajo publicado anterior. Esta misión se consolida en un commit local revisado; **no hay autorización de push, release ni publicación nueva**. El prompt maestro posterior autoriza cambios técnicos, diseño final y commits locales revisados. Las instantáneas anteriores se conservan como historia.

- `rules-0.3.3`: 38 regresiones nuevas de transferencias, OTP, inyección formal y negaciones. El motor mantiene sus cuatro niveles y los límites de pronombres/ingeniería social implícita.
- Seguridad: uso remoto malformado conserva la reserva pesimista; libro de gasto inconsistente falla cerrado; caché separada por usuario y contexto. El control local no resiste el borrado o sustitución coherente de ambos libros por quien controla Windows: se necesita también límite externo de facturación antes de autorizar gasto.
- Gmail unido al panel con consentimiento explícito, aislamiento por sesión, caducidad, guardia antes de cada página/lectura, desconexión y limpieza de credencial local. No envía sus mensajes a IA. `APP_GMAIL_ENABLED=0` por defecto. El JSON OAuth debe estar fuera del repositorio. Desconectar no revoca remotamente el permiso en Google; la revocación se hace en la cuenta.
- Instalación autorizada **solo en el entorno temporal Gmail**: 53 paquetes fijados en `requirements-gmail.lock`, sin cambiar las 26 versiones base ni el `.venv` del proyecto. Ocho comprobaciones con SDK instalado, transporte/OAuth/keyring simulados y red vetada. **OAuth, keyring personal y buzón real no verificados ni autorizados.**
- IA desactivada, presupuesto autorizado **0 USD**, Opus bloqueado, sin SDK Anthropic instalado ni llamadas reales. El piloto de Sonnet es una propuesta, no una autorización. No se cambia de proveedor.
- Suite local: **877 passed, 4 skipped, 1 xfailed, 1 warning**; cuatro integraciones reales bloqueadas, pronombre conocido y aviso Starlette/httpx identificados. Las 11 pruebas JS y las 8 de SDK son comprobaciones separadas.
- UI final visual en verde bosque/crema, resultado principal con nivel, explicación y recomendaciones; detalles secundarios accesibles. Navegador IAB: cuatro .eml, prioridad de archivo, error recuperable, niveles a 320 px y Gmail **SIMULADO** con consentimiento/alerta/desconexión/cierre. Sin infracciones CSP observadas en el recorrido. Esto no acredita accesibilidad completa.
- Narrador audible, contraste elevado de Windows, recorrido manual completo de teclado y **zoom real 200 % del diseño final** siguen no verificados. Se conserva la confirmación humana de zoom de la versión anterior. No solicitar más pruebas manuales por ahora ni implementar voz.
- Los 27 casos dev siguen siendo sintéticos y pendientes de revisión humana. 27/27 niveles aceptables en desarrollo no es evaluación independiente. Procedimiento independiente preparado; conjunto sellado no leído ni creado. Las evidencias deterministas no contienen las 62 citas literales esperadas por ese banco: se mide como cobertura 0/62, sin ocultarlo.

Comprobaciones, instalación, artefactos y límites: `docs/VERIFICACION_FINAL_MVP.md`. Pendientes que requieren al usuario: cuenta de pruebas/GCP/OAuth, permiso específico de SDK y presupuesto de Claude, revisión humana/custodia del sellado, nombre y hora exacta de cierre del hackatón. No bloquean la demo manual local.

Cierre de entrega local: 181 archivos en ZIP candidato, escaneo de 272 unidades sin secretos reales detectados (tres falsos positivos revisados). Extracción limpia: 877 Python / 11 JS / 8 SDK correctas, cuatro integraciones reales saltadas, xfail y aviso identificados. CLI real con cuatro correos ficticios y recuperación tras reinicio correcto; procesos detenidos. PPTX 12 diapositivas y PDF A4 una página validados. Solo cambia documentación tras esas pruebas. Consolidación local autorizada, sin push. El commit que contiene este registro es la referencia de la revisión; consultar git log -1. Próximo paso útil: autorizar cuenta de pruebas/GCP/OAuth o revisar casos humanos, sin gastar créditos de IA.

## Autorizacion posterior de publicacion — 09-11-2026
El usuario solicita ahora subir a GitHub todo el trabajo preparado. Esta instruccion sustituye la prohibicion de push de la instantanea de cierre local anterior y autoriza esta publicacion concreta de feat/fase-0; no es permiso permanente para publicaciones futuras.

Estado comprobado antes de publicar: arbol limpio, HEAD local 9778ffb y remoto dd3e4fb; GitHub confirma repositorio privado. Se suben el commit funcional revisado y esta nota documental, sin reescribir historia, force-push, alterar main ni cambiar visibilidad. Se conservan las exclusiones de secretos, datos privados, conjuntos sellados, entornos y ZIP temporales. No se activan IA, presupuesto ni integraciones reales.

Validacion funcional vigente: 877 Python correctas, 4 integraciones reales saltadas, 1 xfail conocido y 1 aviso; 11 JS y 8 comprobaciones SDK Gmail simuladas correctas. Esta nota no modifica comportamiento ni requiere repetir las suites. El resultado del push se verifica comparando HEAD con refs/heads/feat/fase-0 mediante git ls-remote y comprobando el arbol limpio; no se presupone exito antes de ejecutarlo.

## Aportación de Rafa (compañero) con Claude — 09-11-2026, noche

Trabajo hecho en una copia de `feat/fase-0` (idéntica al ZIP de GitHub a las 21:30) y entregado como **parches** para que el propietario los revise y los aplique: sin commits ni push al repositorio, sin IA real, sin gasto y sin dependencias nuevas del proyecto.

- **Verificación independiente en Linux:** suite, informe dev y recorrido completo de la demo en Chromium (`docs/VERIFICACION_LINUX_2026-11-09.md`). README con instrucciones de Linux comprobadas en una copia limpia.
- **rules-0.3.4:** regla del Bizum inverso con 18 pruebas nuevas (`tests/test_h_bizum_inverso.py`, `docs/LIMITACIONES_DETECCION.md`). Ejemplos de tipología pública escritos por IA: conviene añadir ejemplos reales del equipo.
- **Accesibilidad automática** (axe-core, teclado, zoom 200 % emulado, contraste forzado emulado, movimiento reducido): 4 correcciones y 0 infracciones axe después (`docs/VERIFICACION_ACCESIBILIDAD_2026-11-09.md`, `tests/test_h_accesibilidad.py`). Narrador, contraste alto real y zoom real de Windows siguen **no verificados**.
- Suite tras estos cambios: **899 passed, 4 skipped, 1 xfailed, 1 warning**; 11/11 JS. Evaluación dev 27/27 aceptables, FP=0. Demo: mismos niveles que `GUION_DEMO.md`.
- **Pendiente de decisión del equipo:** los materiales de `docs/entrega/` (PPTX, resumen de una cara, presentación) siguen citando 877 pruebas y rules-0.3.3; no se han regenerado.
