# ADR-0008: SQLite local + keyring; retención mínima

**Fecha**: 2026-11-08
**Estado**: accepted (D-26)
**Decisores**: usuario · Claude Code (propuesta)

## Contexto
Privacidad y minimización son obligatorias (CLAUDE.md §4); la app es local y monousuario en la demo, pero el modelo de datos debe aislar usuarios.

## Decisión
SQLite local (stdlib `sqlite3`), con `user_id` obligatorio en todas las consultas. Secretos y tokens OAuth en **keyring** (Credential Manager de Windows); claves de API en `.env` local no versionado. Retención propuesta 30 días de evaluaciones, **sin cuerpo completo** (extracto ≤300 caracteres y citas de evidencia). Para el MVP: **borrado total manual y purga al arrancar** (en lugar de tarea diaria). Logs sin contenido de mensajes.

## Alternativas consideradas
### PostgreSQL / servidor
- **Por qué no**: infraestructura innecesaria.
### Ficheros JSON
- **Por qué no**: sin consultas ni integridad.

## Consecuencias
### Positivas
- Sin dependencias externas; fácil de borrar por completo.
### Negativas
- Monoproceso; suficiente para la demo.
### Riesgos
- Fuga por logs o base de datos → minimización antes de guardar y tests de que no se guarda el cuerpo completo.
