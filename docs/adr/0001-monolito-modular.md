# ADR-0001: Monolito modular en un proceso, 6 paquetes

**Fecha**: 2026-11-08
**Estado**: accepted (D-26)
**Decisores**: usuario (aprobación) · Claude Code (propuesta y auditoría)

## Contexto
Un único desarrollador asistido por Claude Code (D-33), ~3,5 días hasta la demo del 12-nov. La propuesta original tenía 12 módulos (A–L) pensados para 5 personas, demasiada estructura para el plazo.

## Decisión
Un solo proceso Python con **6 paquetes**: `connectors` (manual, simulado, Gmail), `analysis` (ingesta, normalización, filtro por reglas), `intel` (enlaces pasivos, directorio de entidades, RDAP/reputación opcionales), `ai` (cliente Claude, esquema, verificación de citas), `risk` (motor determinista y explicaciones) y `app` (API FastAPI, UI, notificaciones, persistencia). Comunes: `contracts` (Pydantic) y `core/security` (minimización, configuración, guardas).

## Alternativas consideradas
### 12 módulos A–L
- **Pros**: separación fina. **Contras**: sobrecoste de estructura e interfaces. **Por qué no**: un solo desarrollador.
### Microservicios
- **Por qué no**: despliegue y comunicación sin valor para la demo.

## Consecuencias
### Positivas
- Arquitectura explicable en una diapositiva; arranque y pruebas simples.
### Negativas
- Disciplina manual para respetar las fronteras entre paquetes.
### Riesgos
- Acoplamiento accidental → los paquetes solo se comunican mediante `contracts`; los conectores **no analizan**.
