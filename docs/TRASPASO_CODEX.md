# Traspaso a Codex — estado comprobado el 08-11-2026 (22:03, hora peninsular)

> Estado vigente de cierre, 10-11-2026: rules-0.3.5, 926 Python / 11 JS / 8 SDK Gmail simulados. Rama codex/cierre-mvp, base compartida c013f5b, sin publicación nueva. Evidencia y pendientes: [CIERRE_MVP_2026-11-10.md](CIERRE_MVP_2026-11-10.md). Las secciones fechadas anteriores son históricas.

> Estado vigente 09-11-2026: rules-0.3.3, 877 Python / 11 JS / 8 SDK simulados; cierre local sin push. Véase «Estado vigente — cierre técnico local» al final y docs/VERIFICACION_FINAL_MVP.md. Las cifras anteriores son historia fechada.

> Actualización 09-11-2026: versión local rules-0.3.2, 746 pruebas Python y 11 JS; consolidación y push de feat/fase-0 autorizados expresamente. Los estados Git anteriores son instantáneas históricas. Véase el registro de consolidación al final.

> Este documento sustituye al traspaso inicial del mismo día (commit `71c5917`). Todo lo marcado «comprobado» se ha verificado en esta revisión; lo histórico se indica como tal.

## 1. Repositorio y Git (comprobado)
- Ruta local: `C:\Users\dialm\Desktop\hackaton-finance-antifraude`. Repositorio privado: https://github.com/diegoalmajano/hackaton-finance-antifraude
- Rama de trabajo: `feat/fase-0`. El nombre es histórico: el proyecto está mucho más allá de la «fase 0».
- El remoto se consultó con `git ls-remote --heads origin`. `origin` solo tiene `refs/heads/feat/fase-0` = `71c59178a9a20a8f55495d39399601c123c9357c`.
- HEAD local = `71c5917` = `origin/feat/fase-0`: **0 commits pendientes de subir y 0 por bajar**.
- `main` existe solo en local, con el commit inicial de documentación, y **no está publicada**.
- Cambios locales **sin confirmar ni publicar**, de una sesión de Codex posterior a `71c5917`. Son solo documentación:
  - `docs/contexto/09_PENDIENTES.md` y `docs/contexto/15_SEGUIMIENTO.md`: nota de publicación y bloque «Continuación con Codex — accesibilidad parcial».
  - `docs/ACCESIBILIDAD_CODEX.md` (sin seguimiento): contraste calculado sobre la paleta CSS y protocolo de aceptación de accesibilidad.
  - No se han modificado en esta revisión. Decidir con el usuario si se confirman.
- Ignorados locales, que no se publican:
  - `dist/antifraude_58bc5f9.zip`: ZIP de `58bc5f9`; `71c5917` solo añade documentación.
  - `eval/results/`: un informe de desarrollo.
  - `.claude/` y `.pytest_cache/`.

## 2. Avances
- **Desde `71c5917`:** ningún commit. Solo los cambios de documentación sin confirmar del punto 1. No hay cambios de código ni de comportamiento.
- **Hasta `71c5917`** (histórico; detalle en `docs/contexto/15_SEGUIMIENTO.md`):
  - Misión 1 (`4c96eaa`…`6d76468`): motor, IA simulada, interfaz de análisis, Gmail simulado y entregables preliminares.
  - Misión 2 (`63c66cf`…`aac5fb8`): auditoría de la API de Claude, adaptador de Gmail, revisión de etiquetas, regresiones adversariales, PPTX, PDF, y prueba desde ZIP.
  - Misión 3 (`6dbfea3`…`58bc5f9`): control de gasto de la IA, correcciones de seguridad, `rules-0.3.0`, dominios bancarios del Banco de España, ejecutor de evaluación y pruebas de integración real preparadas.
  - `71c5917`: traspaso a Codex, `AGENTS.md` y `*.zip` en `.gitignore`.

## 3. Fase real
| Estado | Qué |
|---|---|
| Implementado y probado localmente | Análisis manual de texto y `.eml`, minimización, reglas `rules-0.3.0`, enlaces pasivos, directorio de entidades, motor determinista de 4 niveles, alertas en 2 fases, UI local segura en español, modo demo sintético, control de gasto, ejecutor de evaluación |
| Probado solo con simulaciones | Cliente de Claude (transportes falsos); conector, adaptador y sondeo de Gmail (servicio y keyring falsos) |
| Implementado y no probado | `build_gmail_service` (OAuth de escritorio y keyring) |
| Bloqueado (autorizaciones) | Claude real (SDK, clave, presupuesto); Gmail real (GCP/OAuth, cuenta de pruebas, librerías); evaluación independiente (conjunto sellado y su ubicación); ZIP oficial final (descargar de GitHub tras confirmar la versión) |
| Pendiente, sin bloqueo | Accesibilidad en navegador y lector de pantalla (R-58/V-26/R-43/V-25; protocolo en `docs/ACCESIBILIDAD_CODEX.md`); revisión humana de los 27 casos (R-47) y de los 5 bancos; falsos positivos P5–P7; R-64 |
| No implementado (alcance opcional o posterior) | Persistencia SQLite (ADR-0008), escritorio (bandeja y notificaciones), correlación de varios mensajes, segundo canal, voz (fase 2) |

**Criterios que faltan para dar el MVP por terminado:**
- verificación manual de accesibilidad;
- revisión humana de los casos;
- prueba real de Claude con presupuesto autorizado y su coste medido;
- Gmail real o, si no se autoriza, demo solo manual y simulada, que es la principal según D-34;
- entregables coherentes con la versión final y ZIP oficial descargado de GitHub;
- hora de cierre (Q-01) y nombre del producto.

## 4. Arquitectura actual
- Python 3.12.10, FastAPI, Pydantic v2 y Uvicorn. UI HTML, Jinja y htmx vendorizado. Solo `127.0.0.1:8790`.
- Monolito modular en `backend/antifraude/`: `connectors`, `analysis`, `intel`, `ai`, `risk`, `app`, más `contracts` y `core`.
- **Flujo:** entrada manual, `.eml` o simulada → ingesta, minimización y cabeza+cola si es muy largo → reglas → enlaces pasivos y directorio → IA opcional (bloqueada por `CostGuard`) → motor determinista → alertas.
- **Persistencia real:**
  - El historial vive en la memoria de la sesión y no guarda el texto.
  - El libro de gasto de la IA es un JSON fuera del repositorio (`%LOCALAPPDATA%\antifraude\gasto_ia.json` y su copia `.bak`).
  - El directorio de entidades es JSON versionado.
  - **SQLite no está implementado.** `keyring` solo se usa, de forma diferida, en Gmail, y no está instalado.
- **Cambios respecto a los ADR**, registrados como decisiones; no hay ADR nuevos:
  - D-57: control de gasto; Sonnet previsto y Opus bloqueado. ADR-0007 sigue vigente: el modelo es configuración sin valor por defecto.
  - `domain_coverage` en el contrato de entidades (cobertura parcial).
  - Nuevo comprobante `ingest.complete`.
  - Sin *fallback* de modelo.

## 5. Validación (repetida en esta revisión, 08-11-2026 22:03)
- Entorno: `.venv` con Python 3.12.10.
- Consola con `AI_ENABLED=0`, `AI_BUDGET_USD=0`, `AI_ALLOW_OPUS=0` y `ANTIFRAUDE_PRUEBAS_REALES*=0`, sin `ANTHROPIC_API_KEY` ni `CLAUDE_MODEL`.
- `python -m pytest -p no:cacheprovider -ra` → **674 passed, 4 skipped, 1 xfailed, 1 warning** (7,69 s).
  - Saltadas: 3 de Claude real y 1 de Gmail real.
  - `xfail`: limitación del pronombre «facilítesela».
  - Aviso: deprecación de Starlette/httpx.
- `python -m antifraude.evaluation --salida <temporal>`:
  - 27 casos dev: VP 14, FP 0, FN 0, VN 10, 3 ambiguos aparte, nivel aceptable 27/27.
  - Son **métricas de desarrollo, no evaluación**.
- Comprobación de instalaciones: `anthropic`, `googleapiclient`, `google_auth_oauthlib` y `keyring` **no instalados**.
- **No ejecutado en esta revisión:** integraciones reales (prohibidas), prueba desde una carpeta limpia (histórica: misión 3, en `ec3774c`, con el mismo resultado de pruebas) y pruebas manuales en navegador o con lector de pantalla (nunca hechas).

## 6. IA y costes
- Proveedor de la aplicación: Anthropic (Claude), adaptador opcional. **IA desactivada**:
  - `AI_ENABLED=0` por defecto;
  - presupuesto autorizado 0 USD (el previsto de 0,50 USD no está autorizado);
  - Sonnet 5.5 previsto para las primeras pruebas;
  - Opus bloqueado sin `AI_ALLOW_OPUS=1`;
  - SDK no instalado.
- **Llamadas reales de la aplicación: ninguna registrada.** No existe el libro de gasto en la ruta por defecto, el SDK no está instalado y las pruebas reales están saltadas.
  - No se puede verificar desde el repositorio el uso de otras claves fuera de la aplicación ni la facturación de la cuenta: hay que revisarlo en Anthropic Console.
- **Claude Code** (la herramienta de desarrollo usada hasta `58bc5f9`) se autenticaba con su inicio de sesión propio, no con una clave del proyecto. Su consumo es independiente de la API de la aplicación y no se ha verificado su facturación.
- **Codex:** no configura ni autoriza llamadas de IA de la aplicación.
- **Controles de gasto** (`docs/CONTROL_COSTES_IA.md`):
  - reserva del peor caso antes de enviar y liquidación con el `usage` real;
  - límites de tokens y de solicitudes, una solicitud a la vez;
  - sin reintentos ni *fallback*;
  - libro fuera del repositorio con copia `.bak`.
  - Es un límite **local**: el efectivo es el de Anthropic Console.

## 7. Pendientes y riesgos
- **Errores y limitaciones conocidas:**
  - pronombres referidos («facilítesela»);
  - ingeniería social sin palabras clave (sin IA queda BAJO);
  - P5/P6 (enlaces de terceros, menciones de bancos) y P7 (NO CONCLUYENTE sin IA);
  - un correo real de un banco desde un dominio no registrado sale MEDIO o NO CONCLUYENTE;
  - un 403 de cuota de Gmail se trata como fallo de autorización;
  - aviso de deprecación de Starlette/httpx.
  - Detalle: `docs/LIMITACIONES_DETECCION.md` y `docs/contexto/09_PENDIENTES.md`.
- **Decisiones pendientes del usuario:**
  - gasto de la API y modelo final (D-24/D-32);
  - Gmail real;
  - ubicación del conjunto sellado (T-14) y regla de denegación (T-18);
  - nombre del producto;
  - hora de cierre (Q-01);
  - si se confirman los cambios de documentación locales;
  - futuros commits, push o PR.
- **Tres próximas tareas recomendadas (sin gasto):**
  1. Verificación manual de accesibilidad según `docs/ACCESIBILIDAD_CODEX.md` (R-58/V-26/R-43/V-25): teclado, zoom 200 %, 320 px, lector de pantalla, CSP y cabeceras reales.
  2. Revisión humana de los 27 casos dev (R-47) y de las 5 fichas bancarias. Completar los dominios web y de correo desde fuentes oficiales de cada banco.
  3. Corregir P5–P7 y R-64 con casos sintéticos y regresiones, y después reconciliar README, PDF, PPTX y guion con la versión final.

## 8. Cómo continuar en Codex
- **Abrir:** en Codex de escritorio, abrir la carpeta local existente y comprobar con `git branch --show-current` que la rama es `feat/fase-0`. Codex lee `AGENTS.md` al empezar; si el chat es anterior al archivo, iniciar uno nuevo. En otro ordenador: `git clone --branch feat/fase-0 https://github.com/diegoalmajano/hackaton-finance-antifraude.git`.
- **Instalación** (solo si falta `.venv`; requiere descargar paquetes):
  ```powershell
  py -3.12 -m venv .venv
  .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
  ```
- **Pruebas sin gasto:** ver `AGENTS.md`. **Arranque sin IA:** `cd backend` y `..\.venv\Scripts\python.exe -m antifraude`, y abrir `http://127.0.0.1:8790/` con el código de la consola. Para la demo sintética, añadir `APP_DEMO_MODE=1`.
- **Documentos a leer, en orden:**
  1. `AGENTS.md` y este archivo.
  2. `docs/contexto/09_PENDIENTES.md` y `docs/contexto/15_SEGUIMIENTO.md`.
  3. `docs/ACCESIBILIDAD_CODEX.md`.
  4. `docs/adr/` y `docs/ARQUITECTURA.md`.
  5. `docs/CONTROL_COSTES_IA.md`, `docs/LIMITACIONES_DETECCION.md`, `docs/DOMINIOS_BANCARIOS.md` y `eval/EJECUCION.md`.
- **Instrucciones obsoletas o superadas:**
  - en `CLAUDE.md` §8 y en el seguimiento histórico: «sin push», «F0-09 pendiente de aprobación», «siguiente etapa F0-07» y «Aún sin detector»;
  - las reglas de ECC (§10 bis) solo aplican a Claude Code;
  - «Coordinador: Claude Code».
  - **Siguen vigentes:** las reglas de producto de `CLAUDE.md` §4, los ADR y las decisiones D-xx.

## Prompt para continuar
> Continúa este proyecto antifraude en la rama feat/fase-0 (HEAD publicado 71c5917; hay cambios de documentación locales sin confirmar en 09_PENDIENTES.md, 15_SEGUIMIENTO.md y docs/ACCESIBILIDAD_CODEX.md: no los descartes). Lee AGENTS.md, docs/TRASPASO_CODEX.md, 09/15 y docs/ACCESIBILIDAD_CODEX.md. Confirma estado Git y línea base (674 passed, 4 skipped, 1 xfailed). Mantén IA desactivada, presupuesto 0 USD y pruebas reales bloqueadas; no uses claves reales, Claude Code ni ECC. Prioriza la verificación manual de accesibilidad y luego la revisión humana de casos y P5–P7 con casos sintéticos. No leas el conjunto sellado. Antes de cambiar comportamiento, fija el pendiente concreto y sus criterios; conserva contratos, controles de seguridad y análisis pasivo. No cambies proveedor de IA ni hagas commit/push/PR sin autorización.


## Actualización posterior: accesibilidad con Codex (08-11-2026, sin confirmar)

El estado de las secciones anteriores corresponde a la revisión de las 22:03. Después se continuó la revisión autorizada, conservando los cambios locales anteriores. Ahora existen también cambios de código sin confirmar: `backend/antifraude/app/static/js/app.js`, `backend/antifraude/app/templates/emparejar.html`, `backend/antifraude/app/templates/panel.html`, `tests/test_d_accesibilidad.py` y el nuevo `tests/ui/test_accesibilidad.cjs`.

Se corrigieron anuncios de espera que permanecían tras errores y se asociaron los mensajes de error a sus campos. Se comprobó parte del flujo en el navegador integrado: teclado, emparejamiento, validación, resultado, reflujo a 320 px, desconexión y cierre. **No equivale a una auditoría completa:** zoom real 200 %, lector de pantalla, colores forzados, .eml/prioridad en navegador y cabeceras reales siguen pendientes. Detalle y evidencia en [ACCESIBILIDAD_CODEX.md](ACCESIBILIDAD_CODEX.md), sección «Segunda revisión».

Validación vigente: **675 passed, 4 skipped, 1 xfailed, 1 warning** en Python; **9 pruebas JS correctas** con DOM/temporizadores simulados (`node --test tests/ui/test_accesibilidad.cjs`, opcional; Node ya instalado). No se instalaron dependencias. IA desactivada, presupuesto cero, pruebas reales bloqueadas, sellado no leído. HEAD permanece en `71c5917`; **sin commit, push ni PR**. Servidores y pestaña propios de esta prueba cerrados.


## Estado vigente de la misión de demo local (08-11-2026, sin publicar)
- Las secciones previas son revisiones fechadas. Ahora: `rules-0.3.1`, R-64 acotado corregido, cuatro .eml sintéticos de demo y cinco pruebas HTTP reales de loopback. P5–P7 revisados y técnicamente delimitados, sin afirmar que estén corregidos.
- **709 pruebas Python correctas, 4 integraciones reales saltadas, 1 xfail conocido y 1 aviso**; **9 JS correctas**. Copia limpia de fuentes actuales con cambios sin commit e instalación nueva temporal autorizada: mismas suites y CLI/demo/recuperación correctos. No se copió .venv.
- README, arquitectura, guion, fuentes, PPTX (12 diapositivas) y PDF (una página) reconciliados; originales generados conservados fuera del repositorio. Accesibilidad sigue parcial.
- Usuario confirma zoom real 200 % en el escenario probado y anuncio de error vacío con Narrador. Pendientes: anuncios automáticos de espera/resultado, recorrido completo de teclado, versiones, contraste de Windows, reflujo 320 completo y consola/cabeceras reales. No realizar rediseño visual definitivo.
- Metodología y evidencias en seguimiento H1–H6 y tercera revisión de `docs/ACCESIBILIDAD_CODEX.md`. **Meta abierta, sin commit/push/PR/publicación**, IA=0 y presupuesto=0, proveedor conservado y sellado no leído.


### Actualización: accesibilidad estrecha y navegador real
A11Y-03/A11Y-04 corregidos: nombre completo de archivo y etiqueta NO CONCLUYENTE legible a 320 px. IAB verificó cuatro .eml, prioridad, errores y recuperación, recorrido automatizado de teclado, consola CSP y cabeceras reales de operaciones ensayadas (V-25 acotado). Matriz vigente: cuarta revisión de docs/ACCESIBILIDAD_CODEX.md. **710 Python correctas, 4 skipped, 1 xfailed; 11 JS correctas**. Materiales actualizados. Siguen pendientes Narrador audible completo, versiones, contraste Windows y comprobación manual nativa/zoom afectado. Sin rediseño definitivo ni publicación; meta abierta.


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
