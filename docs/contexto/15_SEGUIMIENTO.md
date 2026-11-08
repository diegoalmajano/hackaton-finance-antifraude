# 15 — Seguimiento del desarrollo autónomo hacia el MVP (D-54, misión 2)

> Documento vivo para retomar el trabajo si se interrumpe la sesión. Actualizar al cerrar cada bloque.
> Rama: `feat/fase-0` (solo commits locales; **sin push**). Coordinador: Claude Code (sesión 6).

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
