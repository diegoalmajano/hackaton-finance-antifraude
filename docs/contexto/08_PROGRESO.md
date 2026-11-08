# 08 — Progreso

> Adaptado (sesión 5) del documento homónimo de la memoria original; las tablas de estado de la idea fiscal histórica se omiten.

## Historial de sesiones (2026-11-08)
| Sesión | Qué se hizo |
|---|---|
| 1 | Inventario y lectura de las fuentes originales (PDF oficial, investigación sobre GPTadvisor, chat exportado, prototipo fiscal en ZIP); creación de la memoria original |
| 2 | Análisis estratégico de ideas fiscales (histórico); cambio de objetivo D-08 |
| 3 | **Cambio definitivo (D-09): asistente antifraude.** Investigación web de viabilidad por plataforma (`12`); especificación de producto v1 |
| 4 | Prompt maestro v2.0: auditoría del entorno; verificación oficial de Gmail, Tauri, librerías de escritorio, Safe Browsing/Web Risk, Graph, AI Act; producto v2 (`11`), arquitectura propuesta (`13`), plan (`14`); decisiones D-12–D-22. **Sin código** |
| 5 | **Repositorio independiente** `hackaton-finance-antifraude`: creada la memoria propia (`CLAUDE.md`, `docs/contexto/`, `docs/referencia/`) y `.gitignore`; decisiones D-23–D-25. Sin código, sin commits, sin instalar herramientas |
| 6 | **Traslado verificado**: el repo está en `C:\Users\dialm\Desktop\hackaton-finance-antifraude` y es completamente independiente (la carpeta `Hackaton Finance` es hermana, no superior; su `CLAUDE.md` no se carga). Remoto `origin` comprobado (accesible, vacío). Revisión de secretos y **primer commit local** `2f27d7f` (sin push). Instalación de **ECC** (plugin local, hooks desactivados, MCP `chrome-devtools` desactivado por el usuario) y reglas §10 bis. **Auditoría de arquitectura con ECC → arquitectura APROBADA con modificaciones (D-26–D-37)**; creados `docs/adr/` (ADR-0001–0015) y el plan para un desarrollador con la Fase 0 (`14` §11, pendiente de aprobación). Sin código, sin instalar Python ni dependencias |

## Estado por área (sesión 6)
| Área | Estado |
|---|---|
| Producto y MVP | ✅ Definidos (`11`); orden de prioridad aprobado (D-28); la demo no depende de Gmail (D-34) |
| Arquitectura y ADR | ✅ **Aprobada con modificaciones** (D-26): `docs/adr/` ADR-0001–0015; puntos ⏳ sin verificar |
| Stack | ✅ Python 3.12 + FastAPI + Pydantic + SQLite + Jinja/htmx; web local primero (D-27, D-35) |
| **Fase 0** | 🟡 **En curso por etapas** (D-38), rama local `feat/fase-0`. ✅ **F0-01** Python 3.12.10 instalado con el gestor oficial (3.14 intacto) · ✅ **F0-02** `.venv` + dependencias fijadas (`requirements*.txt`, `requirements.lock`), `pip check` OK, licencias en `docs/DEPENDENCIAS.md`, htmx 2.0.11 vendorizado con integridad verificada · ✅ **F0-03** esqueleto `backend/antifraude/` (6 paquetes + `contracts` + `core`), configuración por entorno (sin clave ni modelo por defecto), `/health` mínimo, documentación automática desactivada; **Probado**: arranque real escuchando solo en `127.0.0.1`; puerto por defecto 8790 con error claro si está ocupado (D-42) · ✅ **F0-04** contratos Pydantic v0.1.0 (`backend/antifraude/contracts/`: mensajes, comprobaciones, filtro, enlaces, IA, evidencias, evaluación, alertas) + `InputAdapter`; **Probado** (corregido en F0-05, D-44) · ✅ **F0-05** seguridad de la API local (`app/security/`, emparejamiento, sesiones, Host/Origin/CSRF, SSE protegido, errores sin detalles, contratos con `hide_input_in_errors`); revisión con `ecc:security-review`; **Probado**: **146 tests** en verde + flujo real con servidor (emparejar, SSE, logout, LAN rechazada, sin fugas en stderr) · ⏸ F0-06–F0-10 **no iniciadas** (esperan autorización) |
| Modelo de Claude | 🟡 **Pendiente** Opus 5.5 vs Sonnet 5.5, por medición de calidad, coste y latencia (D-24, D-32) |
| Plan de ejecución | 🟡 Plan para un desarrollador y **Fase 0** propuestos (`14` §11, P-16) — pendientes de aprobación |
| Repositorio | ✅ Trasladado a `C:\Users\dialm\Desktop\hackaton-finance-antifraude` y completamente independiente; rama `main` con primer commit local; remoto `origin` accesible (vacío); **push pendiente** (con autorización) |
| Memoria del repo | ✅ Implementada (sesión 5); verificada sin dependencias de carpetas externas |
| Código | 🔴 No iniciado (D-10) |
| Gmail / GCP | 🔴 Cuenta de pruebas y proyecto GCP sin crear (B-04) |
| README / PDF / PPTX | 🔴 No iniciados |
| Herramientas (ECC) | ✅ Instalado (sesión 6): plugin `ecc@ecc` con alcance local, hooks desactivados (`hooks_enabled=false`), MCP `chrome-devtools` desactivado; reglas de uso en `CLAUDE.md` §10 bis |

## Próximos pasos
1. ~~Trasladar el repositorio~~ ✅ · ~~Primer commit~~ ✅ local · ~~Instalar ECC~~ ✅ · ~~Aprobar arquitectura~~ ✅ (D-26).
2. **Aprobar el plan de la Fase 0** (`14` §11), el método de sesión de la API local (T-13) y las instalaciones de `14` §11.4.
3. Commit de la documentación de la sesión 6 y primer push (con autorización).
4. Fase 0 técnica → informe → aprobación → fases a–g (D-28).
5. En paralelo (usuario): hora de cierre (Q-01); cuenta Gmail de pruebas + proyecto GCP (B-04); clave de Anthropic y presupuesto (Q-25, T-06).
