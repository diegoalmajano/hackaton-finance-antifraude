# 15 — Seguimiento del desarrollo autónomo hacia el MVP (D-54)

> Documento vivo para retomar el trabajo si se interrumpe la sesión. Actualizar al cerrar cada bloque.
> Rama: `feat/fase-0` (solo commits locales; **sin push**). Coordinador: Claude Code (sesión 6).

## Cómo retomar
1. Leer `CLAUDE.md` → este archivo → `09_PENDIENTES.md`.
2. `git log --oneline -10` y `git status` (añadir archivos **solo por ruta explícita**; nunca `git add -A`).
3. `.\.venv\Scripts\python.exe -m pytest` → debe coincidir con el total registrado abajo.
4. Continuar por «Próxima acción».

## Estado por etapa (2026-11-08)
| Etapa | Estado | Resultado verificable |
|---|---|---|
| A — Cerrar Fase 0 (F0-10) | ✅ | README completo, `.gitattributes` (vendor intacto, SHA-256 sin cambios) |
| B — Motor de detección | ✅ | ingesta texto/.eml/HTML, minimización, enlaces pasivos, reglas, motor determinista, pipeline, alertas 2 fases |
| C — Integración de IA | ✅ (simulada) | cliente Claude con SDK oficial (no instalado → «no configurada»), prompt anti-inyección, esquema estricto, citas verificadas, rechazos/timeout; **0 llamadas reales** |
| D — Experiencia de usuario | ✅ | `/analizar` (texto/.eml), resultado explicado, historial sin texto, modo demo etiquetado; revisión a11y aplicada (`b46ffa4`) |
| E — Gmail | 🟡 lógica simulada / ⛔ real bloqueado | conector `history.list` probado con Gmail simulado |
| F — Evaluación y entrega | 🟡 | 27 casos dev + informe `python -m antifraude.evaluation`; borradores en `docs/entrega/`; faltan PDF/PPTX maquetados, ZIP (requiere push) y evaluación sellada |

## Registro de tareas
| Tarea | Responsable | Archivos principales | Pruebas | Estado / commit |
|---|---|---|---|---|
| Commit F0-08/F0-09 | Coordinador | eval/, backend/data/, contracts/entities.py, intel/entities.py | 286 ✅ | `71c55e2` |
| 24 casos dev sintéticos | **Agente de datos** (no leyó el detector) | eval/datasets/dev/casos_dev.jsonl | test_f0_08 ✅ | `4c96eaa` |
| F0-10 + motor (B) | Coordinador | analysis/*, intel/urls.py, risk/engine.py, app/pipeline.py, evaluation.py | 334 ✅ | `4c96eaa` |
| Revisión Python del motor | **Agente python-reviewer** (solo lectura) | 12 hallazgos verificados | — | corregidos en `dcecc13` |
| IA (C) + interfaz de análisis (D) + correcciones | Coordinador | ai/*, app/analysis_routes.py, templates/partials/*, tests/test_b_regresiones_revision.py | 391 ✅ | `dcecc13` |
| Gmail simulado (E) + `from_raw` + informe de métricas (F) | Coordinador | connectors/gmail.py, evaluation.py | 397 ✅ | `f6bc959` |
| Borradores de entrega | Coordinador | docs/entrega/* | — | `8511ffa` |
| Revisión de seguridad del motor | **Agente security-reviewer** (solo lectura) | 10 hallazgos: DoS, evasión, minimización | 30 regresiones | corregidos en `409b1d2` |
| Revisión de accesibilidad | **Agente a11y-architect** (solo lectura) | 12 hallazgos: foco, anuncios, reflujo, lenguaje | 9 regresiones | corregidos en `b46ffa4` |

## Métricas de DESARROLLO (no son evaluación; motor ajustado con estos casos; sin IA)
27 casos (14 deben alertar / 13 no): VP=14 FP=2 FN=0 VN=11 · Precision 0,88 · Recall 1,00 (IC95% Wilson 0,78–1,00) · F1 0,93 · Tasa FP 0,15 (IC95% 0,04–0,42) · nivel aceptable 27/27 · latencia local p95 ≈ 1 ms · coste: no medido.

## Incidencias
- El agente de seguridad dejó un script propio (`backend/_poc1.py`, medición de tiempos, inofensivo) que entró por error en el commit `dcecc13` (se usó `git add -A`). **Retirado en `409b1d2`** sin reescribir el historial; desde entonces solo se añaden rutas explícitas.
- Un comando de shell mal construido dejó un intérprete Python 3.14 inactivo esperando entrada (no escucha en puertos ni modifica archivos). El clasificador de seguridad denegó cerrarlo: lo debe cerrar el usuario (Administrador de tareas, `python.exe` de `pythoncore-3.14-64` iniciado a las 19:32).

## Bloqueos y autorizaciones pendientes del usuario
- **IA real:** instalar `anthropic` (SDK oficial) + clave + **presupuesto** para la comparativa Opus/Sonnet (D-24, D-32).
- **Gmail real:** proyecto GCP + OAuth «Desktop» + cuenta de pruebas (B-04) e instalar `google-auth-oauthlib`, `google-api-python-client`, `keyring`.
- **Dominios bancarios reales:** verificación en fuente oficial (V-27).
- **Publicación:** push a GitHub (el ZIP oficial se descarga de GitHub).
- **Revisión humana** de los 27 casos sintéticos (R-47) y dudas del agente de datos: dev-0009 (¿aceptar NO CONCLUYENTE?), dev-0025/0027 (¿aceptar BAJO?), ambiguos sin categorías, IBAN de ejemplo.

## Total de pruebas: **436** en verde (última ejecución).

## Próxima acción
Esperar las autorizaciones del usuario (sección «Bloqueos»). Sin ellas, lo más útil es: revisión humana de los casos; prueba manual en navegador (teclado, zoom 200 %, consola CSP, lector de pantalla); maquetar PDF y PPTX desde `docs/entrega/`; preparar push + ZIP cuando se autorice.
