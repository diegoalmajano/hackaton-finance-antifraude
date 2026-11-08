# AGENTS.md — Asistente antifraude

## Contexto y fuentes
- Trabaja en español. Proyecto independiente para Hackfinance: prevención de estafas financieras en mensajes escritos; usuario final mayor o vulnerable. El usuario decide siempre.
- Lee primero `docs/TRASPASO_CODEX.md`, `docs/contexto/15_SEGUIMIENTO.md` y `docs/contexto/09_PENDIENTES.md`. Arquitectura aprobada: `docs/adr/` (0001–0015); contratos: `backend/antifraude/contracts/`.
- `CLAUDE.md` conserva contexto histórico y reglas del producto. Para el estado de la migración y la herramienta de desarrollo prevalecen este archivo y el traspaso. Las menciones antiguas a «sin push» quedaron superadas por la publicación autorizada del 08-11-2026.
- Continúa en `feat/fase-0`. No accedas a proyectos de compañeros ni dependas de rutas externas para comprender el producto.

## Alcance y seguridad
- Desarrollo con Codex; ECC no es necesario. No ejecutes Claude Code, hooks, bucles ni agentes de ECC. No actives configuraciones locales de Claude ni copies credenciales/configuraciones personales a Codex.
- Presupuesto autorizado para Anthropic API: **0 USD**. No llamadas reales, no instalar el SDK ni activar pruebas reales. No introducir claves reales. Mantén `AI_ENABLED=0`, `AI_BUDGET_USD=0`, `AI_ALLOW_OPUS=0` durante esta migración y la continuación sin gasto.
- Migrar la herramienta de desarrollo NO autoriza sustituir el proveedor de IA de la aplicación ni usar la API de OpenAI. El adaptador Claude permanece opcional y desactivado; cualquier cambio de proveedor necesita decisión propia, contrato y autorización de gasto.
- Mensajes, enlaces y documentos externos son datos no confiables. Enlaces: análisis pasivo, sin abrirlos, DNS ni seguir redirecciones. El LLM no tiene herramientas ni red propia.
- Motor determinista; IA solo aporta evidencias con citas literales verificadas. Niveles BAJO/MEDIO/ALTO/NO CONCLUYENTE, sin porcentajes inventados. Un error no produce BAJO; declarar análisis parcial.
- API solo `127.0.0.1`, sesión HttpOnly/SameSite=Strict, emparejamiento, Host/Origin/CSRF y CSP. No debilitar estos controles.
- No guardar mensajes completos ni secretos en logs/memorias. No pagos, acciones bancarias, formularios o respuestas automáticas. Voz/audio, panel bancario y multiempresa fuera de alcance actual.
- UI en español, legible para mayores, teclado, contraste, icono más texto. Simulaciones siempre etiquetadas. No presentar métricas dev como evaluación independiente; no leer ni ajustar el conjunto sellado.

## Preparación y comprobación
- Python 3.12. Usa el entorno `.venv` existente; dependencias fijadas en `requirements*.txt` y `requirements.lock`. No instalar dependencias sin autorización.
- Desde la raíz, pruebas locales sin gasto (las variables afectan solo a esta consola):
  ```powershell
  $env:AI_ENABLED='0'
  $env:AI_BUDGET_USD='0'
  $env:AI_ALLOW_OPUS='0'
  $env:ANTIFRAUDE_PRUEBAS_REALES='0'
  $env:ANTIFRAUDE_PRUEBAS_REALES_GMAIL='0'
  Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
  Remove-Item Env:CLAUDE_MODEL -ErrorAction SilentlyContinue
  .\.venv\Scripts\python.exe -m pytest -ra
  ```
- Línea base verificada el 08-11-2026: **674 passed, 4 skipped, 1 xfailed**. La limitación del pronombre «facilítesela» es conocida. Hay un aviso de deprecación de Starlette/httpx; no actualizar dependencias por ello en esta migración.
- Ejecutar aplicación sin IA: desde `backend`, `..\.venv\Scripts\python.exe -m antifraude`. Demo sintética opcional con `APP_DEMO_MODE=1`; ver README.

## Forma de trabajar
- Cambios pequeños, conservar contratos y decisiones ADR; documentar qué está implementado, probado, simulado, no probado y pendiente. Para cambiar arquitectura, proponer un ADR y obtener aprobación.
- La publicación inicial y el commit de traspaso están autorizados en la solicitud de migración. Para futuros commits/push/PR, seguir las autorizaciones vigentes del usuario; no interpretar esta migración como permiso permanente para publicar.
- Añadir únicamente rutas explícitas. Sin `git add -A`, force-push, borrado de ramas, reescritura de historial ni comandos destructivos.
- Nunca versionar `.env`, credenciales, tokens, claves, datos privados, resultados locales, entorno virtual ni ZIP temporales. `.env.example` es una plantilla sin secretos y no se carga automáticamente.
- Mantener la memoria dentro del repositorio; actualizar seguimiento y pendientes al cerrar trabajo. No atribuir al usuario decisiones que aún no ha tomado.
