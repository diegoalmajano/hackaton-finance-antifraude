# 15 — Seguimiento del desarrollo autónomo hacia el MVP (D-54)

> Documento vivo para retomar el trabajo si se interrumpe la sesión. Actualizar al cerrar cada bloque.
> Rama: `feat/fase-0` (solo commits locales; **sin push**). Coordinador: Claude Code (sesión 6).

## Cómo retomar
1. Leer `CLAUDE.md` → este archivo → `09_PENDIENTES.md`.
2. `git log --oneline -8` y `git status`.
3. Ejecutar `.\.venv\Scripts\python.exe -m pytest` y comprobar que el total coincide con el último registrado aquí.
4. Continuar por la sección «Próxima acción».

## Estado por etapa
| Etapa | Estado | Notas |
|---|---|---|
| A — Cerrar Fase 0 (F0-10) | 🟡 en curso | README, `.gitattributes` |
| B — Motor de detección | ⏳ | — |
| C — Integración de IA | ⏳ | sin presupuesto: solo mocks; llamadas reales bloqueadas |
| D — Experiencia de usuario | ⏳ | — |
| E — Gmail | ⛔ bloqueada (prevista) | requiere credenciales OAuth + librerías no autorizadas; solo mocks |
| F — Evaluación y entrega | ⏳ | ZIP oficial requiere push (no autorizado) |

## Registro de tareas
| Tarea | Responsable | Archivos | Pruebas | Estado |
|---|---|---|---|---|
| Commit F0-08/F0-09 | Coordinador | eval/, backend/data/, contracts/entities.py, intel/entities.py | 286 ✅ | ✅ `71c55e2` |
| Casos dev sintéticos (24) | Agente de datos (subagente, sin leer el detector) | eval/datasets/dev/casos_dev.jsonl | test_f0_08 | 🟡 en curso |
| F0-10 README + .gitattributes | Coordinador | README.md, .gitattributes | — | 🟡 |

## Bloqueos y autorizaciones pendientes del usuario
- **API de Claude (pago):** sin presupuesto aprobado → no se hacen llamadas reales (D-24, D-32).
- **Gmail real:** credenciales OAuth (B-04) + instalar `google-auth-oauthlib`, `google-api-python-client`, `keyring` (no autorizado).
- **Dominios bancarios reales:** verificación en fuente oficial (V-27).
- **Publicación:** push/ZIP oficial desde GitHub requiere autorización.

## Próxima acción
Terminar F0-10 → Etapa B (ingesta y extracción de enlaces).
