# Traspaso de Claude Code/ECC a Codex — 08-11-2026

## Resultado y alcance
La herramienta de desarrollo pasa a Codex. No se cambia el proveedor de IA de la aplicación, sus contratos, dependencias ni funcionamiento. ECC queda como configuración histórica local; no hace falta ejecutarlo ni desinstalarlo para continuar.

Repositorio privado: https://github.com/diegoalmajano/hackaton-finance-antifraude
Rama de trabajo: `feat/fase-0`.
Ruta local existente: `C:\Users\dialm\Desktop\hackaton-finance-antifraude`.
Primer push verificado: `58bc5f9cb0180dee898bf16766d582ffbf5b129c`, sin forzar, solo esta rama, sin etiquetas. No se publicó `main`.

## Revisión antes de publicar
- Árbol de trabajo limpio y remoto GitHub privado confirmado mediante el conector de GitHub.
- Remoto inicialmente sin ramas; los **28 commits** de `feat/fase-0` eran locales (no solo los 9 de la misión 3).
- Revisión de los **316 blobs únicos** y **153 rutas históricas** alcanzables desde la rama: sin rutas de `.env` real, credenciales, claves privadas o ZIP; la plantilla `.env.example` sí se versiona.
- Búsqueda por patrones de tokens de proveedores, claves privadas, asignaciones de credenciales y URL con contraseña. Las 16 coincidencias revisadas eran textos de error, una ruta de ejemplo y claves ficticias de pruebas. No se detectaron secretos reales con este alcance; no es una garantía absoluta sobre todo formato de secreto.
- Exclusiones verificadas: `.env`, `.env.local`, `credentials*.json`, `client_secret*.json`, `token*.json`, `secrets/`, `.claude/settings.local.json` y `dist/antifraude_58bc5f9.zip`. El ZIP temporal permanece local; no se elimina ni se publica. Se añade `*.zip` como protección para futuras copias fuera de `dist/`.
- No se copian credenciales ni configuración privada a Codex. No se reescribe historial.

## Arquitectura que se conserva
Python 3.12, FastAPI, Pydantic v2; monolito modular con UI HTML/Jinja/htmx vendorizado. Fuentes de verdad: `docs/adr/` y contratos Pydantic. SQLite/keyring son decisiones de arquitectura; no asumir que toda la persistencia y los flujos reales están terminados.

Flujo: conector manual/.eml o simulado → ingesta y minimización → reglas `rules-0.3.0` → enlaces pasivos/directorio bancario → analizador IA opcional → motor determinista → alertas preventiva y definitiva.

| Área | Estado comprobado |
|---|---|
| Ingesta, reglas, enlaces, riesgo, UI local y alertas | Implementados y probados localmente |
| Claude | Adaptador y control de gasto probados con simulaciones; API real sin verificar y desactivada |
| Gmail | Conector/adaptador/poller probados con simulaciones; OAuth real y librerías pendientes |
| Bancos | Cinco webs corporativas con cobertura parcial; falta completar/verificar dominios de correo |
| Evaluación | Ejecutor y metodología preparados; cifras dev no independientes; revisión humana y conjunto sellado pendientes |
| Entrega | PPTX/PDF/guion existentes; revisar coherencia con la versión final y descargar ZIP oficial desde GitHub cuando corresponda |
| Escritorio, bandeja y avisos nativos | No implementados; alcance opcional |

## Validación sin gasto
Ejecutadas las pruebas en el entorno existente con IA desactivada, presupuesto cero, clave/modelo retirados del proceso y ambas banderas de integración real a cero:
**674 passed, 4 skipped, 1 xfailed, 1 warning**, en 10,59 segundos.

Las cuatro pruebas reales de Claude/Gmail se saltaron. El fallo esperado corresponde a resolver el pronombre «facilítesela». El aviso es una deprecación de Starlette/httpx; no impide las pruebas. No se instalaron dependencias ni se hicieron llamadas a Anthropic API durante el traspaso. No se comprobó facturación de cuentas externas.

Para repetir los comandos seguros, ver `AGENTS.md`. La aplicación no carga `.env` automáticamente. Mantener **AI_ENABLED=0, AI_BUDGET_USD=0, AI_ALLOW_OPUS=0**. La suscripción usada para desarrollar con Codex no configura ni autoriza llamadas de IA de esta aplicación.

## Pendientes recomendados, sin API de pago
1. Revisar manualmente los 27 casos dev, especialmente dev-0009, dev-0025 y dev-0027; mantener separado el test sellado y no ajustar reglas con él.
2. Probar interfaz con teclado, zoom 200 %, contraste y lector de pantalla; comprobar CSP y flujo completo local.
3. Revisar falsos positivos P5/P6 (enlaces externos y menciones bancarias), P7 sin IA, sufijos de dominio aproximados sin PSL y enlaces a ejecutables (R-64). Añadir regresiones cuando se corrija comportamiento.
4. Completar la verificación de dominios oficiales y de correo; no convertir el remitente de confianza en excepción absoluta.
5. Revisar PDF/PPTX/README, ensayar demo sintética sin red y preparar el ZIP oficial de la misma versión. Hora exacta de entrega y nombre del producto siguen pendientes de confirmación.

Gmail real sigue requiriendo cuenta de pruebas, GCP/OAuth y autorización para librerías. IA real y cualquier cambio a otro proveedor quedan fuera de este traspaso: no usar los créditos restantes de Anthropic.

## Abrir la carpeta en Codex
1. En Codex de escritorio, abre o añade como proyecto la carpeta local indicada arriba. Selecciona trabajar en esa carpeta existente. Los nombres de los controles pueden variar con la versión.
2. Inicia un chat dentro de ese proyecto y comprueba que la carpeta es la correcta y que `git branch --show-current` muestra `feat/fase-0`. No hace falta clonar otra copia en este ordenador.
3. Codex lee `AGENTS.md` al iniciar el trabajo. Si ya había un chat abierto antes de crear el archivo, inicia uno nuevo y pide que confirme las instrucciones cargadas.
4. Usa el acceso con tu cuenta de ChatGPT para desarrollar según las condiciones de tu cuenta; no introduzcas una clave Anthropic ni una clave OpenAI para esta migración.
5. En otro ordenador, clona con autenticación de GitHub ya configurada: `git clone --branch feat/fase-0 https://github.com/diegoalmajano/hackaton-finance-antifraude.git`. Crea `.venv` con Python 3.12 e instala `requirements-dev.txt` como indica README; eso requiere acceso para descargar paquetes, pero no llamadas a Anthropic.

Documentación oficial consultada:
- Abrir una carpeta/proyecto e iniciar el trabajo: https://learn.chatgpt.com/docs/app
- Instrucciones de repositorio: https://learn.chatgpt.com/docs/agent-configuration/agents-md

## Prompt para continuar
> Continúa este proyecto antifraude en la rama feat/fase-0. Lee AGENTS.md, docs/TRASPASO_CODEX.md y el seguimiento/pendientes del proyecto. Confirma estado Git y línea base de pruebas. Mantén IA desactivada, presupuesto 0 USD y pruebas reales bloqueadas; no uses claves reales, Claude Code ni ECC. Prioriza la revisión local de accesibilidad y las limitaciones documentadas del detector con casos sintéticos. No leas el conjunto sellado. Antes de cambiar comportamiento, identifica el pendiente concreto y los criterios de aceptación; conserva contratos, controles de seguridad y análisis pasivo. Informa qué verificaste y qué sigue pendiente. No cambies proveedor de IA ni publiques nuevos cambios sin autorización.
