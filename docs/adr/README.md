# Architecture Decision Records — asistente antifraude

Registros de decisiones de arquitectura (formato Nygard ligero, skill `ecc:architecture-decision-records`).
Aprobados por el usuario el **2026-11-08 (sesión 6, D-26)** a partir de la auditoría de los ADR 001–011 propuestos en `docs/contexto/13_ARQUITECTURA_TECNICA.md` §12 (histórico) y de los nuevos 012–015.

- La numeración 0001–0011 corresponde a los antiguos ADR 001–011.
- **Aprobar un ADR no convierte en verificados sus puntos ⏳**: siguen pendientes de comprobación externa (`docs/contexto/09_PENDIENTES.md` §5).
- Cambiar un ADR aceptado exige uno nuevo que lo sustituya (`superseded by ADR-NNNN`) y aprobación del usuario.

| ADR | Título | Estado | Fecha |
|-----|--------|--------|-------|
| [0001](0001-monolito-modular.md) | Monolito modular en un proceso, 6 paquetes | accepted | 2026-11-08 |
| [0002](0002-escritorio-python-web-local.md) | Aplicación web local primero; pywebview y bandeja después | accepted | 2026-11-08 |
| [0003](0003-contratos-pydantic.md) | Contratos Pydantic v2 como fuente única | accepted | 2026-11-08 |
| [0004](0004-gmail-polling-history.md) | Gmail por polling de `history.list` | accepted | 2026-11-08 |
| [0005](0005-enlaces-analisis-pasivo.md) | Enlaces: análisis estrictamente pasivo | accepted | 2026-11-08 |
| [0006](0006-motor-riesgo-determinista.md) | Motor de riesgo determinista con 4 niveles y estados de comprobación | accepted | 2026-11-08 |
| [0007](0007-modelo-claude-por-medicion.md) | Modelo de Claude elegido por medición (pendiente) | accepted | 2026-11-08 |
| [0008](0008-persistencia-sqlite-keyring.md) | SQLite local + keyring; retención mínima | accepted | 2026-11-08 |
| [0009](0009-reputacion-opcional.md) | Reputación de URLs opcional y complementaria | accepted | 2026-11-08 |
| [0010](0010-voz-aplazada-inputadapter.md) | Voz aplazada; `InputAdapter` común | accepted | 2026-11-08 |
| [0011](0011-python-3-12.md) | Python 3.12 para el proyecto | accepted | 2026-11-08 |
| [0012](0012-interfaz-html-jinja-htmx.md) | Interfaz HTML + Jinja + htmx | accepted | 2026-11-08 |
| [0013](0013-seguridad-api-local.md) | Seguridad de la API local | accepted | 2026-11-08 |
| [0014](0014-distribucion-venv-dependencias-fijadas.md) | Distribución con venv y dependencias fijadas | accepted | 2026-11-08 |
| [0015](0015-modo-degradado-sin-ia.md) | Modo degradado etiquetado sin IA | accepted | 2026-11-08 |
