# 09 — Pendientes, dudas, riesgos y contradicciones

> Adaptado (sesión 5) del documento homónimo de la memoria original: solo lo vigente para el asistente antifraude (las preguntas y riesgos de la idea fiscal son históricos y se omiten). Identificadores originales conservados. Cerrar una entrada = anotarlo aquí con fecha y fuente.

## 0. Autorizaciones pendientes del usuario para completar el MVP (sesión 6)
- **IA real:** instalar `anthropic` (SDK oficial) + clave + **presupuesto** para la comparativa Opus/Sonnet (D-24, D-32).
- **Gmail real:** proyecto GCP + OAuth «Desktop» + cuenta de pruebas (B-04) e instalar `google-auth-oauthlib`, `google-api-python-client`, `keyring`.
- **Publicación inicial:** completada; traspaso en `71c5917`. Futuros commits, push o PR requieren autorización específica. ZIP oficial de la versión final: pendiente; la prueba histórica de la copia local figura en el seguimiento.
- **Revisión humana** de los 27 casos sintéticos (R-47) y de las dudas del agente de datos (dev-0009, dev-0025, dev-0027).
- **Dominios bancarios reales** (V-27) y **nombre del producto** (A-07).
- (sesión 6) Riesgos nuevos: R-55 dominio registrable aproximado **sin PSL** (lista corta de sufijos); R-56 reglas **solo en español** (inglés/catalán no se detectan por contenido; documentarlo); R-57 los casos dev se usaron para ajustar el motor → sus métricas no son evaluación; R-58 accesibilidad corregida solo por revisión estática (falta navegador real y lector de pantalla); R-59 HTML > 300 KB se analiza solo en parte (declarado).
- (misión 2) Riesgos abiertos de la prueba adversarial:
  - R-60 (P5): un correo oficial con enlaces de terceros (encuestas, redes, seguimiento de clics) sale MEDIO.
  - R-61 (P6): un tercero que menciona un banco y pone un enlace sale MEDIO.
  - R-62 (P7): sin IA, los mensajes informativos con una sola señal media quedan en NO CONCLUYENTE.
  - R-63 (A12): **mitigado en la misión 3.** Hay 5 dominios del registro del Banco de España con cobertura parcial, y las imitaciones con el nombre del banco dan MEDIO, no ALTO. **Pendiente:** completar los dominios web y de correo con las fuentes de cada entidad (V-27, revisión humana).
  - R-64 (A17): **corregido de forma acotada en rules-0.3.1**: extensión de ejecutable en la ruta genera precaución; no inspecciona contenido ni sigue redirecciones. Límites y 29 regresiones: `docs/LIMITACIONES_DETECCION.md`.
- (misión 3) Riesgos y pendientes nuevos:
  - R-66: el límite de gasto es **preventivo y local**; el efectivo es el de Anthropic Console. Fijarlo antes de autorizar gasto (`docs/CONTROL_COSTES_IA.md` §4).
  - R-67: el coste real por análisis, la latencia y los rechazos con Claude siguen **sin medir** (V-28).
  - R-68: la urgencia sola ya no alerta. Es una decisión contra los falsos positivos; podría bajar la detección de estafas que solo meten prisa (lo cubre la IA).
  - R-69: un 403 de Gmail por cuota se trata como fallo de autorización.
  - R-70: el registro del Banco de España da solo la web corporativa. Un correo real del banco desde otro dominio sale MEDIO o NO CONCLUYENTE (incertidumbre declarada).
  - Limitaciones de las reglas: `docs/LIMITACIONES_DETECCION.md`.
  - R-65: las reglas son patrones; habrá variantes no cubiertas. Por eso hace falta la evaluación independiente (`eval/METODOLOGIA_INDEPENDIENTE.md`) y la IA como segunda capa.
- (misión 2) **Pendiente de verificación:**
  - V-28: el kwarg `fallbacks` del SDK y la compilación de `anyOf` en la API real (`docs/AUDITORIA_CLAUDE_API.md`).
  - V-29: `build_gmail_service` con las librerías reales de Google.

## 1. Bloqueantes para empezar a programar
- B-01 (actualizado sesión 6) ~~Aprobación del MVP y de los ADR~~ ✅ (D-26, `docs/adr/`). Pendiente: **aprobación del plan de la Fase 0** (`14` §11, P-16) y de sus instalaciones (Python 3.12 + dependencias de `14` §11.4).
- B-02 (actualizado sesión 5) Repositorio: ✅ creado e independiente (D-23). ~~Traslado~~ ✅ hecho y verificado (sesión 6, 2026-11-08) · remoto ✅ comprobado (accesible, vacío) · primer commit ✅ local (sesión 6). Pendiente: **primer push** (con autorización).
- B-03 **Hora exacta de cierre** (no publicada; preguntar a BEST UC3M) = Q-01.
- B-04 Cuenta **Gmail de pruebas** (+ cuenta emisora) y proyecto **Google Cloud** (consentimiento OAuth External/Testing, usuarios de prueba, cliente «Desktop»); conectar solo con autorización.

## 2. Decisiones técnicas abiertas
- ~~T-01 Stack de UI~~ ✅ HTML + Jinja + htmx (D-35) · T-02 resultado del spike pywebview/pystray/win11toast (ahora en la fase g) · ~~T-03 versión de Python~~ ✅ 3.12 (D-27; instalación pendiente de autorización) · T-04 reputación: **opcional** (ADR-0009); queda decidir si se intenta Web Risk o Safe Browsing v5 · T-05 retención inicial (propuesta 30 días, sin cuerpo completo; ADR-0008) · T-06 presupuesto de API y límite de gasto · T-07 segundo canal (P2) · ~~T-08 empaquetado~~ ✅ venv + dependencias fijadas (D-36) · ~~T-09 test sellado~~ ✅ **fuera del repo**, no consultable por agentes; en el repo solo procedimiento, metadatos y SHA-256 (D-40). **Nuevo T-14: acordar la ubicación del conjunto final sellado** antes de crearlo · T-10 bancos del directorio inicial (~5) y verificación de sus dominios con fuente oficial.
- **T-11 (sesión 5) Modelo de Claude para el análisis profundo: `claude-opus-5-5` vs `claude-sonnet-5-5`** según calidad, coste y **latencia** (D-32), con presupuesto autorizado (también refusals, V-17). Decide el usuario (D-24).
- ~~T-12 composición del equipo~~ ✅ **un desarrollador** asistido por Claude Code y ECC (D-33).
- ~~T-13 Cómo obtiene la sesión el navegador~~ ✅ **opción A**: código de emparejamiento aleatorio de un solo uso, con caducidad y límite de intentos; cookie segura; nunca tokens en URLs (D-39, ADR-0013).
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
- (sesión 6) V-18 **Cobertura RDAP de dominios `.es`** (y otros ccTLD frecuentes) · V-19 **parámetros actuales de la API de Claude** (salida estructurada, `stop_reason: "refusal"`, *fallbacks*, temperatura, `effort`, caché) en la documentación oficial al implementar la fase d · V-20 compatibilidad de htmx con CSP estricta (sin `eval` ni estilos en línea) · ~~V-21 versiones y licencias~~ ✅ registradas en `docs/DEPENDENCIAS.md` (F0-02).
- (F0-03) ~~V-22 Puerto 8765 ocupado~~ ✅ resuelto con D-42 (8790 + error claro) · V-23 aviso de Starlette: «usar `httpx` con `starlette.testclient` está obsoleto; instalar `httpx2`» → no se instala nada sin autorización; las pruebas funcionan · ~~V-24 sin carga automática de `.env`~~ ✅ documentado en `docs/CONFIGURACION.md` y `.env.example` (F0-07); falta enlazarlo desde el README (F0-10).
- (F0-04) T-15 **Límites de tamaño** de los contratos propuestos sin medir (mensaje original 5 MiB, cuerpo normalizado 100 000 caracteres, 200 URLs, URL 8 192, cita 500): revisar con casos reales; un correo con adjuntos puede superar 5 MiB → la ingesta deberá descartar el contenido de adjuntos y avisar (`parse_warnings`). · T-16 `ConsentContext`, `UserProfile`, `UserFeedback` y cabeceras completas **aplazados** a sus fases (f y personalización) por mínimo MVP. · T-17 `fetch_new()` es síncrono; confirmar en la fase f que encaja con el polling de Gmail en un hilo.
- (F0-05) R-32 **El código de emparejamiento se imprime en la consola**: si alguien redirige la salida a un archivo, quedará en disco (un solo uso, 5 min). · R-33 Un proceso local malicioso podría agotar los 5 intentos (denegación de servicio del emparejamiento; se recupera reiniciando). · R-34 Cookie sin `Secure` (HTTP en loopback, sin TLS). · R-35 SSE: la sesión se comprueba al conectar; en la fase e hay que **revalidarla periódicamente** en conexiones largas. · R-36 Sin limitación general de peticiones salvo en el emparejamiento (riesgo bajo en loopback). · R-37 Sin auditoría automática de vulnerabilidades de dependencias (`pip-audit` no autorizado). · R-38 UX: con 30 min de inactividad, una persona mayor tendrá que reemparejar a menudo en modo navegador; con pywebview (fase g) la sesión podrá inyectarse sin código. · V-25 Comprobar en F0-06 que htmx envía `X-CSRF-Token` y que el navegador real manda `Origin` en POST y `Sec-Fetch-Site` como se espera → **sigue pendiente** (incluido en V-26).
- (F0-09) **V-27 Verificar en fuentes oficiales** (web oficial de cada entidad y Registro de Entidades del Banco de España) el **nombre oficial y los dominios web y de correo** de Santander, BBVA, CaixaBank, Sabadell y Bankinter; hasta entonces siguen `pending_verification` y **sin dominios** (T-10: ¿quién verifica y cuándo?). · R-50 Los alias «Santander» y «Sabadell» son ambiguos (también son ciudades): reconocer un nombre no implica que el mensaje hable del banco. · R-51 El directorio no resuelve IDN: un host no ASCII nunca se considera oficial (protección frente a homoglifos); si un banco tuviera un dominio IDN habría que registrarlo en punycode. · R-52 Coincidencia por **nombre exacto**: variantes no registradas como alias («BBVA Net», «Caixa») no se reconocen; ampliar alias con criterio y sin subcadenas. · R-53 El directorio es estático (JSON versionado): un dominio oficial nuevo o retirado exige actualizar y volver a verificar. · R-54 La entidad ficticia solo se carga con `include_fictitious=True`; la demo deberá activarla de forma explícita y **etiquetada** (fase a/b).
- (F0-08) R-47 Los 3 casos de demo los redactó Claude Code (`synthetic_ai`) y están **pendientes de revisión humana**: revisar realismo, tono y etiquetas antes de usarlos en la demo. · R-48 Con 3 casos **no hay métricas significativas**; hacen falta 24–36 casos dev escritos sobre todo por personas. · T-18 ¿Añadir una regla de denegación de lectura para la ruta del conjunto sellado en `.claude/settings.local.json` cuando se acuerde su ubicación (T-14)? (impide técnicamente que los agentes lo lean). · R-49 Los dominios `.example`/`.test` no existen: en la fase b el análisis pasivo no debe intentar resolverlos (coherente con ADR-0005) y RDAP quedará «no configurado/no aplicable» para ellos.
- (F0-07) R-44 El filtro de ocultación reconoce **formas** de secreto (cookie, cabeceras, `sk-ant-`, tokens de 43 caracteres, códigos de 8); no puede reconocer contenido arbitrario de mensajes: la garantía principal sigue siendo **no registrar contenido** en el código (ninguna llamada a `logging` lo hace hoy). Posibles falsos positivos: palabras de 8 mayúsculas sin I/L/O se ocultarían. · R-45 Al escribir la clave en PowerShell queda en la memoria del proceso y, si se teclea literalmente, en el historial de PSReadLine → usar `Read-Host` (documentado). · R-46 Los errores no controlados se registran sin mensaje: depurar requiere reproducir el fallo (compromiso aceptado por privacidad).
- (F0-06, actualizado F0-07) **V-26 Navegador real — PARCIAL**: el usuario confirmó manualmente (D-48) bienvenida, emparejamiento → panel, funciones pendientes visibles, cerrar sesión y `/panel` protegido tras cerrar sesión. **Siguen pendientes:** consola sin errores de CSP, navegación completa con teclado, zoom al 200 %, contraste medido (R-43) y cabeceras reales `Origin`/`Sec-Fetch-Site`/`X-CSRF-Token` (V-25). Motivo original de no automatizarlo: no se automatizó un navegador porque Edge/Chrome hacen conexiones de fondo a servicios externos (actualizaciones, telemetría) y la fase prohíbe conexiones externas; y el MCP `chrome-devtools` no debe usarse. Queda como comprobación manual del usuario (lista en el informe de F0-06): flujo completo, consola sin errores de CSP, `Origin`/`Sec-Fetch-Site`/`X-CSRF-Token` reales, teclado, zoom 200 %. · R-35 (SSE): **sigue pendiente** la revalidación de la sesión durante conexiones largas; el panel aún no abre `/events`. · R-39 La interfaz necesita JavaScript (sin JS solo se muestra un aviso). · R-40 htmx escribe en `sessionStorage` la clave `htmx-current-path-for-history` (solo la ruta). · R-41 Los iconos son emojis: su aspecto depende de la fuente del sistema (en Windows, Segoe UI Emoji); el significado nunca depende solo del icono (siempre hay texto). · R-42 Con `core.autocrlf=true`, Git podría cambiar los finales de línea de `vendor/htmx/LICENSE` (y en teoría de `htmx.min.js`) al hacer checkout, alterando las huellas SHA-256 registradas → valorar un `.gitattributes` que los marque como binarios. · R-43 Contraste de colores calculado a mano en el CSS, no medido con una herramienta.

## 6. Contradicciones
| ID | Contradicción | Tratamiento |
|---|---|---|
| C-01 | PDF: «diapositivas opcionales» vs PowerPoint como entregable | Entregar PPTX siempre (P-04) |
| C-02 | El PDF no fija fecha; el 12-nov procede del equipo | Marcar 💬; confirmar (Q-01) |
| C-16 (sesión 5) | P-13 proponía Opus 5.5 por defecto; ADR 007 proponía Sonnet 5.5 | **Resuelta como pendiente explícita** (D-24); `13` y `14` actualizados |
| C-17 (sesión 5) | `12` §1 y §3 contemplan una demo con audio sintético y ElevenLabs | **Prevalece D-12** (voz en fase 2); `12` §5bis ya lo indica |
| C-19 (sesión 6) | `11` §5 y §12 exigen «recepción **real** de correo» / «≥1 con Gmail real» en la demo; D-34 dice que la demo principal **no depende de Gmail** | ✅ **Resuelta** (D-41): `11` §5 y §12 corregidos en la sesión 6 |
| C-18 (sesión 5) | La memoria original hablaba de un «repositorio compartido no clonado» | **Superada por D-23** (repositorio propio e independiente) |

## 7. Riesgos
- (sesión 6) R-29 **Capacidad de un solo desarrollador** → orden D-28, recortar g y después f. · R-30 La seguridad de la API local retrasa el núcleo → límite de tiempo en F0-05. · R-31 Clasificación errónea en los 3 casos de demo (falsos positivos o NO CONCLUYENTE) → ADR-0006 y ensayo desde la fase c.
- R-20 Novedad frente a competidores consolidados (30 %). · R-21 Prometer canales imposibles (`12` §1). · R-22 Porcentajes sin calibrar (prohibidos, D-14). · R-23 Prompt injection. · R-24 Privacidad de mensajes enviados a la nube. · R-25 Alcance vs 4 días. · R-26 Banco de pruebas circular (IA que escribe y detecta). · R-27 Demo dependiente de red/APIs → modo sin IA real etiquetado. · R-28 Correos de prueba en SPAM.
- Registro completo con mitigaciones: `14` §7 (incluye la posible pérdida de puntos de IA frontera por no usar audio, aceptada).


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


## Misión de versión demostrable: estado actual
- R-64 corregido con análisis pasivo y contrapartidas legítimas; P5/P6 siguen siendo posibles falsas alarmas y P7 incertidumbre deliberada. Revisión delimitada en `docs/LIMITACIONES_DETECCION.md`, sin cambios de etiquetas ni lectura del sellado.
- Usuario confirma manualmente bienvenida/panel, error vacío anunciado por Narrador, ejemplo 2 ALTO y zoom real 200 % legible/sin barra horizontal. No dar por superados anuncios de espera/resultado, teclado completo, CSP/cabeceras, versiones del lector/navegador ni contraste elevado. Matriz vigente: tercera revisión en `docs/ACCESIBILIDAD_CODEX.md`.
- Instalación de pip/requirements.lock autorizada **solo** en el entorno temporal de la misión; completada y verificada. El entorno del repositorio y los archivos de dependencias no se modifican. No se autoriza ninguna integración real.
- Meta **no completada** por las comprobaciones manuales obligatorias pendientes. Sin rediseño visual, commit, push, PR ni publicación.


### Actualización: accesibilidad estrecha y navegador real
A11Y-03/A11Y-04 corregidos: nombre completo de archivo y etiqueta NO CONCLUYENTE legible a 320 px. IAB verificó cuatro .eml, prioridad, errores y recuperación, recorrido automatizado de teclado, consola CSP y cabeceras reales de operaciones ensayadas (V-25 acotado). Matriz vigente: cuarta revisión de docs/ACCESIBILIDAD_CODEX.md. **710 Python correctas, 4 skipped, 1 xfailed; 11 JS correctas**. Materiales actualizados. Siguen pendientes Narrador audible completo, versiones, contraste Windows y comprobación manual nativa/zoom afectado. Sin rediseño definitivo ni publicación; meta abierta.


## Decisión del usuario: accesibilidad diferida a fase final
- No implementar lectura de pantalla propia, voz ni reproducción de audio. Se conserva compatibilidad básica con lectores mediante HTML semántico, etiquetas y atributos accesibles.
- No dedicar más tiempo por ahora a Narrador ni solicitar pruebas manuales de accesibilidad. Los anuncios auditivos pendientes, el tema de contraste elevado y el recorrido manual completo siguen **no verificados**, no superados.
- Simplificación visual y diseño definitivo reservados para la etapa final. La validación completa de accesibilidad/usabilidad se retomará antes de presentar el proyecto.
- Estas comprobaciones **no bloquean el trabajo técnico autorizado actual**. Prioridad: detector, fiabilidad, seguridad y preparación de integraciones. Esto no autoriza APIs de pago, claves reales, OAuth real, SDK nuevos, cambiar proveedor ni publicación; continúan las restricciones existentes.


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
