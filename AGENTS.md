# AGENTS.md — Asistente antifraude

> Estado vigente de cierre, 10-11-2026: rules-0.3.5, 926 Python / 11 JS / 8 SDK Gmail simulados. Rama codex/cierre-mvp, base compartida c013f5b, sin publicación nueva. Evidencia y pendientes: [CIERRE_MVP_2026-11-10.md](docs/CIERRE_MVP_2026-11-10.md). Las secciones fechadas anteriores son históricas.

> Estado vigente 09-11-2026: rules-0.3.3, 877 Python / 11 JS / 8 SDK simulados; cierre local sin push. Véase «Estado vigente — cierre técnico local» al final y docs/VERIFICACION_FINAL_MVP.md. Las cifras anteriores son historia fechada.

## Contexto y fuentes
- Trabaja en español. Proyecto independiente para Hackfinance: prevención de estafas financieras en mensajes escritos; usuario final mayor o vulnerable. El usuario decide siempre.
- Lee primero `docs/TRASPASO_CODEX.md` (estado comprobado el 08-11-2026), `docs/contexto/15_SEGUIMIENTO.md`, `docs/contexto/09_PENDIENTES.md` y, si existe, `docs/ACCESIBILIDAD_CODEX.md` (protocolo de accesibilidad pendiente). Arquitectura aprobada: `docs/adr/` (0001–0015); contratos: `backend/antifraude/contracts/`. SQLite (ADR-0008) no está implementado: el historial es solo de sesión.
- Si encuentras cambios locales sin confirmar, no los descartes ni sobrescribas: pueden ser trabajo de otra sesión. Pregunta antes de incluirlos en un commit.
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
  $env:APP_GMAIL_ENABLED='0'
  $env:ANTIFRAUDE_PRUEBAS_REALES='0'
  $env:ANTIFRAUDE_PRUEBAS_REALES_GMAIL='0'
  Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
  Remove-Item Env:CLAUDE_MODEL -ErrorAction SilentlyContinue
  .\.venv\Scripts\python.exe -m pytest -ra
  ```
- Línea base verificada de nuevo el 08-11-2026 a las 22:03 (HEAD `71c5917`): **674 passed, 4 skipped, 1 xfailed**. Las 4 saltadas son las integraciones reales de Claude y Gmail; no las actives. La limitación del pronombre «facilítesela» es conocida. Hay un aviso de deprecación de Starlette/httpx; no actualizar dependencias por ello en esta migración.
- Ejecutar aplicación sin IA: desde `backend`, `..\.venv\Scripts\python.exe -m antifraude`. Demo sintética opcional con `APP_DEMO_MODE=1`; ver README.

## Forma de trabajar
- Cambios pequeños, conservar contratos y decisiones ADR; documentar qué está implementado, probado, simulado, no probado y pendiente. Para cambiar arquitectura, proponer un ADR y obtener aprobación.
- La publicación inicial y el commit de traspaso están autorizados en la solicitud de migración. Para futuros commits/push/PR, seguir las autorizaciones vigentes del usuario; no interpretar esta migración como permiso permanente para publicar.
- Añadir únicamente rutas explícitas. Sin `git add -A`, force-push, borrado de ramas, reescritura de historial ni comandos destructivos.
- Nunca versionar `.env`, credenciales, tokens, claves, datos privados, resultados locales, entorno virtual ni ZIP temporales. `.env.example` es una plantilla sin secretos y no se carga automáticamente.
- Mantener la memoria dentro del repositorio; actualizar seguimiento y pendientes al cerrar trabajo. No atribuir al usuario decisiones que aún no ha tomado.

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

## Autorizacion posterior de publicacion — 09-11-2026
El usuario solicita ahora subir a GitHub todo el trabajo preparado. Esta instruccion sustituye la prohibicion de push de la instantanea de cierre local anterior y autoriza esta publicacion concreta de feat/fase-0; no es permiso permanente para publicaciones futuras.

Estado comprobado antes de publicar: arbol limpio, HEAD local 9778ffb y remoto dd3e4fb; GitHub confirma repositorio privado. Se suben el commit funcional revisado y esta nota documental, sin reescribir historia, force-push, alterar main ni cambiar visibilidad. Se conservan las exclusiones de secretos, datos privados, conjuntos sellados, entornos y ZIP temporales. No se activan IA, presupuesto ni integraciones reales.

Validacion funcional vigente: 877 Python correctas, 4 integraciones reales saltadas, 1 xfail conocido y 1 aviso; 11 JS y 8 comprobaciones SDK Gmail simuladas correctas. Esta nota no modifica comportamiento ni requiere repetir las suites. El resultado del push se verifica comparando HEAD con refs/heads/feat/fase-0 mediante git ls-remote y comprobando el arbol limpio; no se presupone exito antes de ejecutarlo.
