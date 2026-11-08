# 13 — Arquitectura técnica del MVP antifraude (**APROBADA con modificaciones**, D-26)

> **Sesión 6 (2026-11-08): la arquitectura queda APROBADA** con las modificaciones de la auditoría ECC. **Fuente de verdad de las decisiones: `docs/adr/` (ADR-0001 a ADR-0015)**; si algo de este documento contradice un ADR, **prevalece el ADR**. Los puntos ⏳ siguen sin verificar.
> **Cambios aprobados respecto a lo que sigue (resumen):** 6 paquetes en lugar de 12 módulos (ADR-0001) · web local en navegador primero, pywebview/bandeja/toasts solo en la fase g; Electron descartado (ADR-0002) · sin generación de TypeScript (ADR-0003) · no resolver DNS de dominios sospechosos ni seguir acortadores (ADR-0005) · estados `done`/`failed`/`not_configured` y credenciales/OTP desde dominio oficial = mínimo MEDIO (ADR-0006, §6.1 actualizado) · modelo por medición de calidad, coste y latencia (ADR-0007) · purga al arrancar (ADR-0008) · reputación opcional (ADR-0009) · Python 3.12 (ADR-0011) · nuevos: UI HTML+Jinja+htmx (0012), seguridad de la API local (0013), venv + dependencias fijadas (0014), modo degradado sin IA (0015). Un solo desarrollador (D-33); orden de prioridad D-28.

> **Copia de trabajo del repositorio** (2026-11-08, sesión 5): adaptada del documento homónimo de la memoria original; referencias ajustadas para no depender de carpetas externas. Cambios marcados con «(sesión 5)».

Sesión 4 (2026-11-08). Basado en `11_PRODUCTO_ANTIFRAUDE.md` v2. Hechos verificados marcados ✅ (doc. oficial) / 🟡 (fuentes secundarias) / ⏳ (por verificar en spike). Todo lo demás es **propuesta** ⚖.

## 1. Auditoría del entorno (verificado en esta máquina, 2026-11-08)
- (Histórico, sesión 4) La carpeta de trabajo original no era un repositorio Git. **Actualización sesión 5:** el proyecto vive en el repositorio **independiente** `hackaton-finance-antifraude` (remoto `origin` en la cuenta GitHub del usuario); **sesión 6:** trasladado fuera de la carpeta original y con primer commit local (sin push); sin relación con el repositorio de otro equipo (D-23). Git 2.53 instalado; **`gh` no instalado** (no imprescindible).
- Python **3.14.3**; Node **24.15**, npm 11.12; **Rust/cargo no instalados** (Tauri los necesita junto a MSVC Build Tools ✅ doc. Tauri).
- Ninguna dependencia del proyecto instalada (fastapi, pydantic, pytest, anthropic, google-auth…).
- **Reutilizable del trabajo anterior:** nada de código (el motor fiscal no aplica). Sí: la memoria, la rúbrica, la investigación de plataformas (`12`) y el patrón «motor determinista + LLM que explica».
- ⚠ Python 3.14 es muy reciente: algunas dependencias con extensiones nativas (p. ej. `pythonnet`, que usa pywebview en Windows) pueden no tener soporte ⏳ → **propuesta: fijar Python 3.12 o 3.13** para todo el equipo.

## 2. Selección tecnológica de escritorio
> **Histórico parcial (sesión 6):** la decisión vigente es ADR-0002 (web local primero; pywebview/bandeja después; Electron descartado) y ADR-0012 (HTML + Jinja + htmx; sin React). El token en la URL (`?token=`) mencionado abajo queda **descartado** por ADR-0013. La tabla se conserva por trazabilidad.
| Opción | Pros | Contras para nosotros (equipo Python/IA, ~4 días, 3–5 h/día) | Veredicto ⚖ |
|---|---|---|---|
| **Tauri 2** + React/TS + Python *sidecar* | Ligero, seguro, bandeja y notificaciones vía plugins | Requiere **Rust + MSVC Build Tools** (no instalados) ✅; sidecar Python empaquetado con PyInstaller, con problemas conocidos de cierre del proceso 🟡; tres lenguajes | **Descartado para el MVP** (riesgo de integración) |
| **Electron** + React/TS + Python hijo | Ecosistema enorme; bandeja y notificaciones nativas | Dos runtimes, empaquetar Python + Electron, endurecer seguridad (contextIsolation), peso | Alternativa B si falla la opción C |
| **C — «Python-first»**: FastAPI (motor) + UI React/TS (Vite) **o** HTML+htmx servida localmente, dentro de **pywebview** (ventana nativa con WebView2) + **pystray** (bandeja) + **win11toast** (notificaciones) | Un solo proceso y lenguaje para toda la lógica; el equipo domina Python; Node solo para compilar la UI; pruebas simples | pystray: última versión 0.19.5 (2023) 🟡, licencia por verificar ⏳; toasts: win11toast MIT, release ene-2026 🟡 (windows-toasts Apache-2.0, inactivo); compatibilidad con Python 3.14 ⏳ | **Recomendado**, con **spike de 2 h el día 0** |
**Plan B dentro de C:** si pywebview falla → la UI se abre en el navegador predeterminado (`http://127.0.0.1:<puerto>` con token local), manteniendo bandeja y notificaciones. **Plan C:** Electron.
**UI:** React + TypeScript (Vite) si la persona 4 se siente cómoda; si no, **HTML + htmx + Jinja** (todo Python). Decisión del equipo el día 0.
Tiempo real UI ← backend: **SSE** (Server-Sent Events, más simple que WebSocket para notificaciones unidireccionales).

### Librerías candidatas (verificar versión, licencia y Python 3.12/3.13 al instalar ⏳)
FastAPI + Pydantic v2 (MIT) · Uvicorn · `anthropic` SDK (MIT) · `google-auth-oauthlib`, `google-api-python-client` (Apache-2.0) · `keyring` (MIT; Credential Manager de Windows) · `httpx` (BSD) + `respx` (mocks) · `tldextract` (BSD; **con snapshot local de la Public Suffix List**, sin descargas en ejecución) · `idna` (BSD) · `rapidfuzz` (MIT; similitud de dominios) · tabla de confusables Unicode TR39 (homoglifos) · `beautifulsoup4` (MIT; texto visible vs `href` en HTML) · `email` (stdlib) · `sqlite3` (stdlib) · pytest · pywebview (BSD, 6.2.1 abr-2026 🟡) · pystray ⏳ · win11toast (MIT 🟡).
No se añaden librerías por popularidad: cada una debe justificar su uso en un ADR o en el PR.

## 3. Monolito modular: módulos
> **Sesión 6 (ADR-0001):** los módulos A–L se agrupan en **6 paquetes**: `connectors` (A) · `analysis` (B + C) · `intel` (D) · `ai` (E) · `risk` (F + explicaciones) · `app` (G, H, I, J y API). Comunes: `contracts` y `core/security` (L). La columna «Resp.» (P1–P5) es **histórica** (D-33: un desarrollador). K (evaluación) vive en `eval/`.
| Mód. | Responsabilidad | Entrada → Salida | Depende de | Errores | Tests | Resp. |
|---|---|---|---|---|---|---|
| **A Connectors** | Gmail (P1); `ManualInput` (pegar/importar .txt/.eml, P0); `SimulatedConnector` etiquetado (tests/demo); futuro Telegram/Outlook/voz por el mismo `InputAdapter` | evento externo → `RawMessage` | L (tokens), J (estado historyId) | auth caducada, cuota, red → estado del conector «degradado», nunca silencioso | mocks del servicio Gmail | P5 |
| **B Ingestion** | Normalización a `IncomingMessage`, parseo MIME, HTML→texto, extracción de URLs (texto visible + `href`), **deduplicación** (id fuente + hash), minimización | `RawMessage` → `IncomingMessage` | L (enmascarado) | MIME roto → mensaje con `parse_warnings` | fixtures .eml | P1 |
| **C Fast Screening** | Reglas + rasgos estructurados, sin LLM por defecto | `IncomingMessage` (+perfil) → `ScreeningResult` | D (léxico rápido de URL), G | — | casos dev | P2 |
| **D Threat Intelligence** | Directorio de entidades, análisis pasivo de URLs/dominios, RDAP (edad de dominio), reputación | URLs + entidad declarada → `UrlAnalysis[]` | L | timeouts/cuotas → `verification_status=error` + `limitations` | unitarios + respx | P3 |
| **E AI Analysis** | Claude con contenido delimitado y salida estructurada; verificación de citas | mensaje minimizado + hallazgos de D → `AiFindings` | L | refusal, timeout, JSON inválido → `ai_status=failed` (nunca BAJO) | cliente Anthropic simulado | P2 |
| **F Risk Engine** | Fusión determinista → nivel, evidencias, incertidumbres, recomendaciones | C+D+E+G+correlación → `FraudAssessment` | — | — | tabla de decisión exhaustiva | P2 |
| **G Personalization** | Perfil, bancos, sensibilidad, remitentes de confianza, reglas individuales con procedencia, feedback | `UserFeedback` → reglas; perfil → C/F | J | — | aislamiento entre usuarios, reversibilidad | P1 |
| **H Notifications** | Preventiva/definitiva; toasts + SSE + panel; deduplicación de avisos | `ScreeningResult`/`FraudAssessment` → notificación | I | fallo de toast → queda en panel | unitarios | P4 |
| **I Desktop UI** | Ventana, bandeja, pantallas, accesibilidad | API local | API (FastAPI) | — | pruebas manuales guiadas + teclado | P4 |
| **J Persistence** | SQLite local; repositorios con `user_id` obligatorio; retención y borrado | — | — | migraciones simples | aislamiento, purga | P1 |
| **K Evaluation** | Banco dev/test, runner, métricas, coste/latencia | datasets → informe | todos | — | — | P2+P5 |
| **L Security** | Enmascarado/minimización, secretos (keyring/env), logging sin contenido, validación, guardas de red, pruebas adversariales | transversal | — | — | adversariales | P3 |
**Orquestador** (en B/API, P1): `on_message` → C → (preventiva) → D ∥ E → F → H → J. Toda la lógica de análisis es común; **los conectores no analizan**.
**Futuro módulo de voz:** implementará `InputAdapter` y emitirá `IncomingMessage(channel="voice_transcript", …)` → sin rehacer el motor.

## 4. Contratos de datos (revisión de la propuesta del usuario)
> **Sesión 6, F0-04 — histórico de diseño.** La **fuente única y autoritativa** de los contratos es ahora el código `backend/antifraude/contracts/` (versión `0.1.0`, protocolo *contract-first*: cualquier cambio se hace primero allí, con tests). Lo que sigue se conserva solo como trazabilidad. Diferencias principales: `Channel` = `manual | gmail | simulated | voice_transcript` (telegram/outlook fuera del MVP); `RawMessage` + `InputAdapter.fetch_new()`; `CheckResult.required` y estado `not_configured`; `AiOutput` (salida del modelo, citas **sin verificar**) separado de `Evidence` (solo verificadas; las de IA exigen cita); `Alert` (preventiva/definitiva); `is_partial` **calculado** a partir de las comprobaciones; `ConsentContext`, `headers_subset`, `UserProfile` y `UserFeedback` **aplazados** a sus fases (f, personalización).
Pydantic v2 en `backend/app/contracts/` (fuente única); tipos TS generados o mantenidos a mano desde el **OpenAPI** de FastAPI. Cambios solo por PR revisado por P1. Fechas en UTC ISO-8601; ids UUID; enums en `snake_case` en inglés, textos al usuario en español.
```
Channel = gmail | manual | simulated | telegram | outlook | voice_transcript(futuro)
Sender { display_name?, address?, domain?, auth?: {spf?, dkim?, dmarc?, raw_header_present: bool} }
ExtractedUrl { url_id, raw, display_text?, href, normalized?, host?, registrable_domain?, location: body_text|html_href|subject }
ConsentContext { connector_id, scopes: [str], granted_at, revocable: true }
IncomingMessage { id, user_id, channel, source_message_id, received_at, sender: Sender, reply_to?: Sender, subject?,
  text (normalizado y MINIMIZADO), urls: [ExtractedUrl], attachments_meta: [{filename, mime, size}] (no se abren),
  metadata: {headers_subset, labels?, thread_id?}, conversation_id?, consent_context, content_hash, parse_warnings: [str], is_simulated: bool }
Signal { code, family: content|sender|url|context, severity: critical|high|medium|low, description_user, description_tech, span?: {start,end}, source: rule }
ScreeningResult { message_id, suspicion_detected, detected_signals: [Signal], severity: none|low|medium|high|critical,
  needs_deep_analysis, preliminary_alert_required, status: ok|partial|error, rule_version, latency_ms }
CheckResult { name, required: bool, status: done|failed|not_configured|skipped|not_applicable, detail?, duration_ms? }   (sesión 6: `required` y `not_configured`, ADR-0006)
UrlAnalysis { url_id, original_url, normalized_url, registrable_domain, claimed_entity?, official_domains_for_claimed: [str],
  comparison: official|lookalike|unrelated|unknown, lookalike_of?, display_href_mismatch: bool, is_shortener, punycode_or_confusable: bool,
  domain_age_days?, reputation_findings: [{source, verdict: listed|not_listed|error, detail}], domain_findings: [Signal],
  verification_status: verified|partial|failed, limitations: [str], checks: [CheckResult] }
Evidence { evidence_id, source: rule|threat_intel|ai|user_profile|correlation, kind: risk|legitimacy, severity, category,
  description_user, description_tech, quote? (literal, verificada), verified: bool, ref? (url_id/message_id) }
FraudAssessment { assessment_id, message_id, user_id, risk_level: low|medium|high|inconclusive, is_partial,
  fraud_categories: [credential_theft|payment_fraud|bank_impersonation|phishing_link|investment_scam|account_takeover|other],
  evidence: [Evidence], uncertainties: [str], checks_performed: [CheckResult], explanation_user (español llano), explanation_tech,
  recommendations: [{code, text_user}], related_message_ids: [id], model_version?, rule_version, prompt_version?,
  ai_usage?: {input_tokens, output_tokens, cost_estimate_usd}, created_at }
UserProfile { user_id, enabled_channels: [Channel], selected_banks: [entity_id], alert_sensitivity: low|normal|high,
  retention_policy: {assessment_days (def. 30), store_message_excerpt: bool (def. true, ≤300 caracteres)},
  personalization_preferences: {trusted_senders: [{address|domain, require_auth_pass: true, added_at, provenance}], custom_rules: [...]},
  autostart: false }
UserFeedback { feedback_id, user_id, assessment_id, feedback: false_alarm|confirmed_fraud|unsure, comment?, timestamp,
  review_status: pending|applied|rejected, applied_rule_id? }
```
Cambios respecto a la propuesta: `sender` estructurado (autenticación), `urls` con texto visible vs destino, `Signal`/`Evidence`/`CheckResult` como tipos propios (separan **herramientas** de **inferencias de IA** mediante `source`), `is_partial`, `kind=legitimacy`, versiones de regla/prompt/modelo, `is_simulated`, `content_hash` para deduplicar, `ai_usage` para costes.

## 5. Pipeline de detección
### 5.1 Nivel 1 — filtro rápido (C)
Reglas sobre texto normalizado y estructura (no solo palabras): petición de contraseña/PIN/OTP/datos de tarjeta, petición de transferencia/Bizum/cambio de IBAN, urgencia o amenaza de bloqueo, entidad financiera mencionada (directorio) + remitente o enlace fuera de sus dominios oficiales, nombre mostrado de entidad con dominio gratuito/ajeno, texto visible del enlace ≠ destino, acortador, punycode/confusables, adjuntos ejecutables, promesas de rentabilidad. Salida con severidad; **la ausencia de coincidencias no es garantía**: `needs_deep_analysis` también se activa si hay **incertidumbre** (entidad financiera + petición de acción aunque no salte ninguna regla fuerte). **Haiku 5.5** solo como experimento medido para la zona gris (no imprescindible).
### 5.2 Nivel 2 — análisis profundo (D + E)
D (técnico) y E (IA) en paralelo; sus resultados se guardan **separados** (`source`). E recibe: contenido minimizado delimitado como datos, hallazgos técnicos ya calculados, dominios oficiales de la entidad declarada, contexto permitido (correlación). Devuelve JSON con esquema (`output_config.format`): `claimed_entity`, `tactics[{category, quote, explanation}]`, `inconsistencies[...]`, `financial_request{type, details}`, `injection_attempt: bool`, `uncertainties[...]`, `suggested_level`. **Cada `quote` se verifica como subcadena literal** del mensaje; si no aparece, la evidencia se descarta y se anota.
**Modelo: PENDIENTE (D-24, T-11) (sesión 5)** — candidatos `claude-sonnet-5-5` ($2/$10 por M tokens ✅ tabla oficial; candidato indicado inicialmente por el usuario) y `claude-opus-5-5` ($4/$20 ✅ tabla oficial, ver `12` §3); se elegirá por **calidad, coste y finalidad** midiendo en el conjunto dev. Notas de la propuesta Sonnet (verificar para el modelo elegido): temperatura/top_p no configurables (400 si se envían); `effort` a medir (`low`/`medium`); **gestionar `stop_reason: "refusal"`** (el contenido de phishing podría activar clasificadores de seguridad, p. ej. `cyber`) → `ai_status=failed` + motivo, nunca BAJO; usar el parámetro de *fallback* de servidor (`fallbacks: "default"`, beta) en la API de Claude ⏳ al implementar; prompt de sistema estable para **prompt caching**.

## 6. Motor de riesgo (F) — política inicial (a ajustar SOLO con el conjunto dev)
### 6.1 Reglas de decisión
1. **ALTO** si hay ≥1 evidencia **crítica verificada**: (a) petición de credenciales/OTP/tarjeta + enlace o canal de respuesta fuera de dominios oficiales de la entidad declarada; (b) dominio parecido (lookalike) a una entidad del directorio; (c) URL en lista de reputación; (d) evidencia IA de categoría `credential_theft` o `payment_redirection` con cita verificada **y** al menos una evidencia de otra fuente (regla/técnica/correlación).
2. **MEDIO** si: ≥1 evidencia alta, o ≥2 medias de fuentes distintas, o evidencia IA alta sin corroboración, o cambio de datos de pago sin otros indicios.
0. **(Sesión 6, ADR-0006/D-29)** Cada comprobación tiene estado `done` | `failed` | `not_configured` (o `skipped`/`not_applicable`). **Obligatorias en el MVP:** filtro por reglas, análisis pasivo de todas las URLs e IA si el filtro escaló. RDAP y reputación son **complementarias**: si están `not_configured` se declaran en «lo que no se pudo comprobar», pero **no** fuerzan NO CONCLUYENTE.
3. **BAJO** solo si **todas las comprobaciones obligatorias están en `done`** y no hay evidencias ≥ media. Evidencias de legitimidad (dominio oficial + DMARC pass + remitente habitual) pueden bajar MEDIO→BAJO **solo** sin evidencias críticas/altas **y nunca si hay petición de credenciales/OTP/tarjeta**.
4. **NO CONCLUYENTE** si una comprobación **obligatoria** está en `failed` (IA fallida/refusal/timeout) y las evidencias disponibles no alcanzan ALTO. ~~RDAP/reputación caídos con URL no oficial~~ y ~~acortador no resoluble~~ ya no fuerzan NO CONCLUYENTE por sí solos (el acortador es una señal y una incertidumbre declarada). **Errores → NO CONCLUYENTE o el nivel que justifiquen las evidencias existentes, nunca BAJO.**
4 bis. **(Sesión 6, D-29)** ~~«dominio oficial + petición de OTP» → NO CONCLUYENTE~~ → **una petición de credenciales, contraseña, PIN, OTP o datos de tarjeta nunca es segura por venir de un dominio aparentemente oficial: mínimo MEDIO** (ALTO si se suma otra evidencia crítica), con la recomendación de verificar por el canal oficial del directorio.
5. Si se alcanzó ALTO con comprobaciones fallidas → ALTO con `is_partial=true`.
### 6.2 Sensibilidad
`low|normal|high` desplaza el umbral de **alerta preventiva** y si MEDIO genera notificación emergente o solo aparece en el panel. **No** modifica las reglas críticas.
### 6.3 Personalización y correlación en F
Remitente de confianza = evidencia de legitimidad **solo si** el dominio autenticado coincide; jamás anula evidencias críticas. «Falsa alarma» crea una regla individual que **suprime una señal no crítica concreta para ese remitente** (con procedencia, reversible). Correlación: evidencia media «relacionado con alerta previa (mismo dominio/hilo/entidad en 7 días)»; nunca fusiona mensajes en un mismo fraude.
### 6.4 Camino a probabilidades (fuera del MVP)
Datos etiquetados representativos (≥ cientos por clase, reales y consentidos + conjuntos públicos con licencia) → modelo (p. ej. regresión logística sobre rasgos) → calibración (Platt/isotónica) en validación → Brier, ECE, diagrama de fiabilidad en test independiente → corrección por **prevalencia** → recalibración periódica.

## 7. Inteligencia de enlaces (D)
**(Sesión 6, ADR-0005/D-31)** Estrictamente pasivo: **no se visita ninguna URL, no se resuelven por DNS los dominios sospechosos y no se siguen acortadores**. RDAP y reputación: complementarias (ADR-0009). ⏳ Cobertura RDAP de `.es` (V-18).
**Pasivo (MVP):** normalización (minúsculas, punycode→Unicode para mostrar, quitar credenciales `user@host`, decodificar porcentajes), dominio registrable con PSL local, subdominios con marca (`bbva.seguridad-x.com`), confusables/homoglifos, similitud con dominios oficiales (rapidfuzz), TLD, IP literal, puerto no estándar, acortadores conocidos (destino **no** resuelto → incertidumbre), discrepancia texto visible/`href`, edad de dominio por **RDAP** (consulta a registro, no a la web sospechosa), reputación.
**Reputación — opciones:** Google **Web Risk** (uso comercial; Lookup gratis hasta 100 000/mes 🟡; requiere proyecto GCP, probablemente facturación ⏳) · Google **Safe Browsing v5** (gratis, **solo no comercial** ✅; v4 obsoleta, fin de soporte 31-mar-2027 🟡) · feeds CC0 (TweetFeed) como señal secundaria. **Propuesta:** Web Risk si se puede habilitar sin coste en el proyecto GCP del equipo; si no, Safe Browsing v5 declarando su uso no comercial en el prototipo. VirusTotal público y urlscan: **no** (licencia no comercial / privacidad).
**Activo (P2, no MVP):** solo en sandbox aislado (contenedor sin credenciales, egress filtrado, bloqueo de IP privadas/loopback/link-local/metadatos tras **cada** resolución DNS (anti-rebinding: conectar a la IP validada), máx. redirecciones, timeout, tamaño, tipos permitidos, sin descargas ni JS de terceros salvo navegador aislado).
**(F0-09, D-53) Implementado el esquema y las consultas:** contrato `backend/antifraude/contracts/entities.py`, consultas `backend/antifraude/intel/entities.py`, datos `backend/data/entities_es.json` (reales, **pendientes y sin dominios**, V-27) y `backend/data/entities_ficticias.json` (solo pruebas/demo). Lo que sigue es el diseño original (histórico).
**Directorio de entidades:** JSON versionado `entities_es.json` con `{entity_id, nombre, dominios_oficiales[], dominios_correo[], canales_oficiales{web, app, telefono}, fuente_url, verificado_por, fecha}`; cada dato con **fuente oficial** (web del banco). Inicial: los bancos que use la demo + principales españoles (P3). Teléfonos solo si están verificados en la fuente.

## 8. Conector Gmail (A) — verificado en documentación oficial
- Scope **`gmail.readonly` = restringido** ✅ (también `gmail.metadata`, que además no da el cuerpo). Los restringidos exigen verificación; **«si almacenas o transmites datos de scopes restringidos a servidores, necesitas una evaluación de seguridad»** ✅ → producto comercial: verificación + CASA (y revisar si enviar fragmentos a Anthropic cuenta como transmisión ⏳ + política de Uso Limitado de Google ⏳).
- Modo **Testing**: hasta 100 usuarios de prueba; **refresh token caduca a los 7 días** 🟡 (doc. Google Health; confirmar) → **re-autorizar la cuenta de demo el 10–11 nov**. Máx. 100 refresh tokens vivos por cuenta y cliente 🟡.
- **Recepción**: *push* requiere tema Pub/Sub, conceder publicación a `gmail-api-push@system.gserviceaccount.com`, renovar `watch` ≤7 días (recomendado diario), máx. 1 evento/s por usuario ✅ → exige backend con suscripción: **no para el MVP de escritorio**. **Propuesta: polling** de `history.list` (2 unidades) cada 20–30 s con `startHistoryId` persistido; `messages.get` (`format=full`: 60 unidades) solo para mensajes nuevos; cuota 6 000 unidades/min por usuario ✅ → holgada. Si `historyId` caducó (404) → resincronizar con `messages.list` reciente.
- **Flujo OAuth**: cliente «Aplicación de escritorio», flujo de app instalada con redirección *loopback* (google-auth-oauthlib); el `client_secret.json` fuera del repo; refresh token en **keyring** (Credential Manager); nunca en logs. **Desconectar**: revocar token en Google + borrar local.
- Solo lectura: no modifica etiquetas ni marca como leído; adjuntos: solo metadatos. Incluir mensajes de **SPAM** en el análisis (los correos de prueba pueden caer ahí).
- ⏳ Verificar en spike: cabecera `Authentication-Results` disponible en `payload.headers`.
- **Configuración que hará falta (con autorización del usuario):** cuenta Gmail nueva del hackatón (+ otra emisora para la demo) → proyecto Google Cloud → habilitar Gmail API → pantalla de consentimiento *External/Testing* → añadir usuarios de prueba → crear cliente OAuth «Desktop» → descargar JSON a ruta local fuera del repo.

## 9. Segundo canal (P2) — comparación
| | **Outlook (Microsoft Graph)** | **Telegram bot (reenvío)** | **Telegram Business connection** |
|---|---|---|---|
| Permisos | `Mail.ReadBasic`/`Mail.Read` delegado; **cuentas personales soportadas** en `message: delta` ✅ | Token de bot | Usuario conecta el bot en ajustes Business ✅; ¿Premium? ⏳ |
| Recepción automática | **Sí** (delta query por polling; sin URL pública) | **No** (el usuario reenvía) → es el mecanismo de **compartición** para SMS/WhatsApp | **Sí**, solo chats privados |
| Complejidad | Media (registro app Entra, MSAL) — reutiliza parseo de correo | Baja | Media |
| Riesgos | Registro de app; detalles de cuentas personales ⏳ | Mensaje reenviado pierde remitente original | Requisito Premium; alcance limitado |
| Valor demo | Medio (otro proveedor) | **Alto** (móvil en el escenario: «reenvío el SMS sospechoso al asistente») | Alto si funciona |
**Propuesta:** no comprometer Gmail. Si el MVP está estable el día 2: **Telegram bot** como canal de compartición (cubre SMS/WhatsApp de forma legal); Outlook solo si sobra capacidad. El análisis manual (pegar/importar) cubre P0.

## 10. Seguridad, privacidad y prompt injection (L)
**Prompt injection (10 defensas):** 1 contenido externo en bloque delimitado y etiquetado como datos, instrucciones solo en el sistema; 2 validación/normalización de entradas (longitud, codificación, caracteres de control/invisibles); 3 salida con esquema JSON y validación Pydantic; 4 **decisión final determinista** (F) independiente del LLM; 5 el LLM **no tiene herramientas** (sin acciones, sin red); 6 sin red saliente desde E salvo la API de Anthropic; 7 `user_id` obligatorio en toda consulta; 8 conjunto adversarial en el banco (inyecciones, texto oculto, Unicode invisible); 9 secretos fuera del alcance del modelo y de los logs; 10 errores → NO CONCLUYENTE. Un intento de inyección detectado = **evidencia de riesgo**. Ningún mensaje puede autorizar integraciones, cambiar configuración ni ejecutar comandos.
**Minimización antes de Claude:** enmascarar OTP/códigos, contraseñas aparentes, IBAN (mantener país + últimos 4 + «nuevo/no visto»), tarjetas (Luhn), tokens, emails/teléfono del propio usuario; eliminar valores de parámetros de URL (mantener dominio y ruta); truncar a N caracteres relevantes; enviar solo mensajes escalados.
**Retención (propuesta inicial, configurable):** evaluaciones 30 días; **no se guarda el cuerpo completo** (solo extracto ≤300 caracteres y citas de evidencia); borrado manual total; purga automática diaria; logs sin contenido.
**Secretos:** `.env` local + `.env.example` sin valores; tokens OAuth en keyring; `.gitignore` para `client_secret*.json`, `.env`, `*.db`.
**Datos y Anthropic:** las fuentes secundarias indican que las condiciones comerciales de la API **no permiten entrenar con el contenido del cliente** y que la retención por defecto ronda 30 días 🟡 — ⏳ verificar en la documentación oficial de Anthropic antes de afirmarlo en la presentación.
**Legal:** prototipo académico ≠ producto comercial (RGPD: base jurídica, roles responsable/encargado con el banco, EIPD, transferencias; AI Act ⏳). No afirmar cumplimiento certificado.

## 11. Estructura de repositorio
**Vigente (sesión 6, ADR-0001/0012/0014; se crea en la Fase 0, `14` §11):**
```
backend/antifraude/{contracts,core,connectors,analysis,intel,ai,risk,app}   (F0-03: raíz `antifraude` en lugar de `app` para evitar `app.app`)
backend/antifraude/app/{templates,static}        (Jinja + htmx vendorizado)
pyproject.toml (solo configuración de pytest)    arranque: `cd backend && ..\.venv\Scripts\python -m antifraude`
backend/data/entities_es.json      backend/data/entities_ficticias.json      (F0-09)
eval/{README.md, SELLADO.md, datasets/dev/*.jsonl, runner (fase posterior)}   (F0-08: formato = contrato `EvalCase`; el conjunto sellado vive FUERA del repo, D-40)      tests/{unit,integration,adversarial}
vendor/htmx/      docs/adr/      docs/DEPENDENCIAS.md      .env.example      requirements.txt      requirements-dev.txt      requirements.lock      README.md
```
Histórico (sesión 4): `backend/app/{contracts,connectors/{gmail,manual,simulated},ingestion,screening,threat_intel,ai_analysis,risk,personalization,notifications,persistence,security,api}` + `desktop/` + `frontend/`.

## 12. ADR — **histórico** (sesión 4–5). Vigentes y aprobados: `docs/adr/` (D-26)
| ADR | Decisión | Motivo principal |
|---|---|---|
| 001 | Monolito modular, un proceso | Plazo y equipo; sin microservicios |
| 002 | Escritorio «Python-first» (FastAPI + pywebview + pystray + toasts); spike día 0; plan B navegador; plan C Electron | Sin Rust; equipo Python |
| 003 | Contratos Pydantic como fuente única; TS desde OpenAPI | Evitar divergencias front/back |
| 004 | Gmail por polling de `history.list` (no Pub/Sub) | Push exige backend en la nube |
| 005 | Enlaces: solo análisis pasivo en MVP | No se garantiza aislamiento robusto |
| 006 | 4 niveles + motor determinista; sin porcentajes | Requisito del usuario; sin datos de calibración |
| 007 | Modelo de análisis profundo **pendiente**: `claude-opus-5-5` vs `claude-sonnet-5-5` según calidad, coste y finalidad (medir en dev); reglas en filtro; Haiku 5.5 solo si se mide valor | D-24 (sesión 5); antes proponía Sonnet por coste/latencia |
| 008 | SQLite local + keyring; retención 30 días; sin cuerpo completo | Privacidad |
| 009 | Reputación: Web Risk (o Safe Browsing v5 no comercial en prototipo) | Licencias |
| 010 | Voz aplazada; `InputAdapter` común | Alcance |
| 011 | Python 3.12/3.13 fijado para el equipo | Compatibilidad de dependencias |
