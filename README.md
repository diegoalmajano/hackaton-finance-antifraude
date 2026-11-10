# Asistente antifraude — prototipo para Hackfinance (BEST UC3M)

> Candidata Council local, 10-11-2026: rules-0.3.9, 1030 Python / 11 JS / 8 SDK Gmail simulados. Base 615b4a9, rama aislada codex/candidata-council, cambios sin commit. Decisión y validación: [DECISION_VERSION_FINAL.md](docs/DECISION_VERSION_FINAL.md). Los estados anteriores son históricos. IA y presupuesto cero; sin integraciones reales ni nueva publicación.

Asistente antifraude con IA opcional que **ayuda a reconocer estafas financieras en mensajes escritos** (correo, SMS…), pensado para personas mayores y clientes de banca. Analiza el texto y los enlaces **sin abrirlos**, explica en español sencillo qué ha encontrado y qué no ha podido comprobar, y deja **siempre la decisión al usuario**.

> **Estado: prototipo académico en desarrollo**, no es un producto comercial. Consulte la sección «Estado y limitaciones». Nada de lo que se muestra como simulado se presenta como real.

Para continuar el desarrollo con Codex: [guía de traspaso](docs/TRASPASO_CODEX.md) e [instrucciones del repositorio](AGENTS.md). Anthropic API permanece desactivada y con presupuesto de 0 USD.

## 1. Requisitos
- Windows 10/11 con PowerShell (probado en Windows 11). También funciona en Linux (probado; ver «Linux o macOS» en la sección 2).
- **Python 3.12** (64 bits). Comprobación: `py -3.12 --version`.
  - Si no lo tiene: instálelo desde python.org o con el gestor oficial de Python (`pymanager install 3.12-64`).
- Un navegador moderno (Edge, Chrome o Firefox).
- Para el análisis manual no hacen falta Node, Rust, Docker ni los SDK de Google o Anthropic. Una vez instaladas las dependencias base, funciona sin Internet. Las integraciones opcionales requieren sus autorizaciones y conexión.

## 2. Instalación (una sola vez)
Abra PowerShell en la carpeta del proyecto (la que contiene este README):
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
```
### Linux o macOS (alternativa)
Con Python 3.12 instalado (`python3.12 --version`), desde la carpeta del proyecto:
```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
```
Para ejecutar, sustituya `..\.venv\Scripts\python.exe` por `../.venv/bin/python` y defina las variables con `export NOMBRE=valor` en lugar de `$env:NOMBRE = "valor"`. Por ejemplo, la demo sin IA:
```bash
cd backend
AI_ENABLED=0 AI_BUDGET_USD=0 APP_GMAIL_ENABLED=0 APP_DEMO_MODE=1 ../.venv/bin/python -m antifraude
```
Comprobado el 09-11-2026 en Linux x86_64 con Python 3.12.3 y `requirements.lock`: misma suite (877 correctas antes de los cambios del 09-11; 899 después, 4 saltadas, 1 `xfail`) y mismo recorrido de demo (tres ejemplos, texto libre y cuatro `.eml` con los niveles esperados). macOS no se ha probado.

- `requirements.txt` contiene las dependencias de ejecución, con versiones exactas.
- `requirements-dev.txt` añade las de pruebas.
- `requirements.lock` es el bloqueo completo del entorno base.
- Gmail es opcional: `requirements-gmail.lock` reúne 53 versiones, incluidas las 26 de base, comprobadas en Windows con Python 3.12. No se presupone compatibilidad del lock opcional con otros sistemas; su instalación requiere autorización para el entorno concreto. Ver `docs/GMAIL_PREPARACION_REAL.md`.
- Licencias y justificación de cada dependencia: `docs/DEPENDENCIAS.md`.

## 3. Configuración (opcional)
El análisis manual funciona sin configurar integraciones. Las variables se definen en la consola. El asistente **no** lee archivos `.env`; `.env.example` es solo una referencia. Detalle: `docs/CONFIGURACION.md`.

| Variable | Por defecto | Para qué |
|---|---|---|
| `APP_PORT` | `8790` | Puerto local (siempre `127.0.0.1`) |
| `APP_LOG_LEVEL` | `INFO` | Detalle de los registros |
| `APP_GMAIL_ENABLED` | `0` | Gmail apagado. El panel solo permite iniciar la conexión tras configurar y autorizar la cuenta de pruebas |
| `APP_GMAIL_CLIENT_SECRET` | vacío | Ruta del cliente OAuth fuera del repositorio; no introducir credenciales en el chat ni en el proyecto |
| `ANTHROPIC_API_KEY` | vacía | Análisis con IA (opcional; sin clave, la IA figura como «no configurada») |
| `CLAUDE_MODEL` | vacío | Modelo de Claude: `claude-sonnet-5-5` previsto para las primeras pruebas; `claude-opus-5-5` solo con `AI_ALLOW_OPUS=1` |
| `AI_ENABLED` / `AI_BUDGET_USD` | `0` / `0` | La IA está **desactivada** y el gasto autorizado es **0 USD** por defecto. Más límites en `docs/CONTROL_COSTES_IA.md` |

## 4. Ejecución
```powershell
cd backend
..\.venv\Scripts\python.exe -m antifraude
```
1. En la consola aparecerá un **código de emparejamiento** (`XXXX-XXXX`). Deje esa ventana abierta.
2. Abra **http://127.0.0.1:8790/** en el navegador y pulse **Empezar**.
3. Escriba el código y pulse **Conectar**. Caduca en 5 minutos y sirve una sola vez.
4. Para cerrar el asistente, pulse `Ctrl+C` en la consola.

Si el puerto 8790 está ocupado, el asistente lo indica en español y no se inicia. Use otro puerto:
```powershell
$env:APP_PORT = "8791"
```

### Uso
En el panel, pegue el texto de un correo o SMS (o elija un archivo `.eml`) y pulse **Analizar**. Verá:
- un **aviso preventivo** si hay algo sospechoso;
- el **resultado definitivo** con su nivel (BAJO, MEDIO, ALTO o NO CONCLUYENTE, con icono y texto);
- por qué, qué le recomendamos y **lo que no se ha podido comprobar**.
El texto de los mensajes no se guarda.

### Modo demostración (datos ficticios)
```powershell
$env:APP_DEMO_MODE = "1"
..\.venv\Scripts\python.exe -m antifraude
```
Carga la entidad ficticia «Banco Ficticio» y tres **ejemplos sintéticos** que se analizan con un clic: aviso legítimo, estafa evidente y estafa sofisticada. Todo va etiquetado como «EJEMPLO SINTÉTICO»; ningún dato es real.

### Análisis con IA (opcional)
**Desactivado por defecto y sin gasto autorizado.** Requiere:
- la librería oficial `anthropic` (instalación **pendiente de autorización**);
- `AI_ENABLED=1`;
- una clave (`ANTHROPIC_API_KEY`);
- un modelo (`CLAUDE_MODEL`);
- un presupuesto **autorizado** (`AI_BUDGET_USD`).

Cada solicitud pasa por un **control de gasto local**:
- estimación del peor caso y reserva previa en un libro de gasto fuera del repositorio;
- límites de tokens y de solicitudes;
- una solicitud a la vez;
- sin reintentos ni cambio a otros modelos;
- registro del coste real sin guardar contenido.

Detalle: `docs/CONTROL_COSTES_IA.md`. Sin IA, la aplicación funciona con reglas y análisis de enlaces, y lo indica: «análisis parcial — IA no disponible».

### Gmail (opcional, conexión real pendiente)
El conector ya está integrado en el panel: consentimiento de la sesión → sondeo de mensajes nuevos → análisis local → avisos explicados. La recepción, los errores, la deduplicación y la desconexión se han probado con servicios simulados; esa prueba no acredita recepción de una cuenta real. Si caduca el punto de lectura, la recuperación puede revisar hasta 20 mensajes recientes. La aplicación no envía, modifica ni borra correos.

`APP_GMAIL_ENABLED=0` mantiene el flujo real apagado. El análisis manual no necesita las librerías de Gmail. Las 8 comprobaciones opcionales de `scripts/verificar_gmail_sdk.py` usaron objetos de los SDK instalados en un entorno temporal autorizado y transportes HTTP, OAuth y keyring simulados: no iniciaron OAuth ni consultaron una cuenta. Faltan consentimiento para una cuenta de pruebas y prueba real de extremo a extremo; el entorno base del proyecto sigue sin las librerías opcionales. Antes de conectar habrá que elegir un entorno autorizado que las tenga. Instrucciones y alcance: `docs/GMAIL_PREPARACION_REAL.md` y `docs/GMAIL_CONFIGURACION.md`.

### Métricas del conjunto de desarrollo
```powershell
cd backend
..\.venv\Scripts\python.exe -m antifraude.evaluation
```
Son cifras de **desarrollo**: el motor se ajustó con esos casos, así que **no son una evaluación independiente**.

## 5. Pruebas
Desde la carpeta del proyecto:
```powershell
.\.venv\Scripts\python.exe -m pytest
```
Ejecuta las pruebas automáticas de contratos, seguridad, interfaz, configuración, registros, banco de evaluación, directorio de entidades, motor de detección (con regresiones adversariales) e IA y Gmail **simulados**. Todas son locales: no usan Internet ni APIs de pago. Última ejecución (10-11-2026, cierre local del detector): **1030 pruebas Python en verde**, más 4 de integración real **saltadas** por defecto (requieren credenciales; ver `docs/PRUEBAS_INTEGRACION_REAL.md`) y 1 limitación conocida marcada como `xfail`; persiste un aviso de deprecación de Starlette/httpx. Las 11 pruebas JavaScript y las 8 comprobaciones opcionales de SDK se contabilizan por separado. La comprobación de la copia temporal con los cambios actuales y los límites de instalación se registra en `docs/contexto/15_SEGUIMIENTO.md`.

## 6. Seguridad y privacidad (resumen)
- Solo escucha en `127.0.0.1`. Se accede mediante un emparejamiento con un código de un solo uso. La sesión usa una cookie HttpOnly y SameSite=Strict, y las operaciones están protegidas con CSRF, Host y Origin. La CSP es estricta y los recursos estáticos se sirven localmente.
- **Los enlaces nunca se abren**: el análisis es pasivo, sin visitas ni consultas DNS a dominios sospechosos.
- Los registros no incluyen códigos, cookies, tokens, claves ni contenido de mensajes.
- Arquitectura y decisiones: `docs/adr/` (ADR-0001 a 0015) y `docs/contexto/`.

## 7. Estado y limitaciones
| Funcionalidad | Estado |
|---|---|
| Análisis manual (texto y `.eml`), extracción de enlaces, filtro por reglas | Implementado y probado |
| Análisis **pasivo** de enlaces (dominios parecidos, texto visible ≠ destino, acortadores, IP, punycode) | Implementado y probado |
| Motor de riesgo determinista (4 niveles, sin porcentajes; un error nunca da BAJO) | Implementado y probado; reglas `rules-0.3.3` |
| Alertas preventiva y definitiva con explicación, evidencias, incertidumbres y recomendaciones | Implementado y probado |
| Interfaz en español con sesión segura | Diseño bosque/crema y flujo simplificado. Reflujo a 320 px comprobado en los cuatro niveles y Gmail simulado; teclado revisado parcialmente. El zoom 200 % confirmado corresponde al diseño anterior y no se ha revalidado en el actual. Narrador, contraste elevado y recorrido manual completo siguen pendientes. Matriz: `docs/ACCESIBILIDAD_CODEX.md` |
| Análisis con Claude | Implementado y probado **con respuestas simuladas**; sin llamadas reales (falta autorizar la librería y el presupuesto). **Gasto real: 0 USD** |
| Control de gasto de la IA | Implementado y probado con clientes simulados; alcance y límites del libro local en `docs/CONTROL_COSTES_IA.md` |
| Gmail | Conector, ciclo de sesión y avisos integrados en el panel, probados con **Gmail simulado**. Compatibilidad de SDK comprobada por separado con HTTP/OAuth/keyring simulados. Conexión real apagada (`APP_GMAIL_ENABLED=0`), OAuth y cuenta real pendientes |
| Directorio de bancos reales | 5 dominios web tomados del **Registro de Entidades del Banco de España**, con cobertura **parcial** (`docs/DOMINIOS_BANCARIOS.md`); la demo usa el banco ficticio |
| Límites de la detección sin IA | Documentados en `docs/LIMITACIONES_DETECCION.md` |
| RDAP y reputación de URLs | No configurados (opcionales; se declaran como no comprobados) |
| Escritorio (bandeja, notificaciones nativas) | No implementado (fase opcional) |
| Idioma de los mensajes | Las reglas están pensadas para **español**; mensajes en otros idiomas pueden no detectarse por su contenido |

Más detalle: `docs/contexto/15_SEGUIMIENTO.md`, `08_PROGRESO.md` y `09_PENDIENTES.md`.

Documentación útil:
| Documento | Contenido |
|---|---|
| `docs/ARQUITECTURA.md` | Resumen de la arquitectura para el jurado |
| `docs/AUDITORIA_CLAUDE_API.md` | Integración con Claude comparada con la documentación oficial: qué está verificado y qué no |
| `docs/GMAIL_CONFIGURACION.md` / `docs/GMAIL_PREPARACION_REAL.md` | Flujo del panel, alcance probado, dependencias opcionales y pasos para la cuenta de pruebas cuando se autorice |
| `eval/METODOLOGIA_INDEPENDIENTE.md` | Cómo se hará la evaluación independiente (conjunto sellado fuera del repositorio) |
| `eval/CAMBIOS_ETIQUETAS.md` | Correcciones de etiquetas del conjunto de desarrollo, con su justificación |
| `eval/EJECUCION.md` | Cómo ejecutar la evaluación reproducible (reglas frente a Claude; conjunto sellado) |
| `docs/CONTROL_COSTES_IA.md` | Control de gasto de la IA; límite local frente al límite de facturación |
| `docs/PRUEBAS_INTEGRACION_REAL.md` | Pruebas con Claude y Gmail reales (preparadas, no ejecutadas) |
| `docs/DOMINIOS_BANCARIOS.md` | Dominios de bancos reales: fuente oficial, fecha y cobertura |
| `docs/LIMITACIONES_DETECCION.md` | Lo que la detección por reglas no puede resolver |
| `docs/entrega/` | Presentación (PPTX), resumen de una cara (PDF) y guion de la demo |

## 8. Estructura
```
backend/antifraude/   aplicación (contracts, core, connectors, analysis, intel, ai, risk, app)
backend/data/         directorio de entidades (cinco webs verificadas, cobertura parcial + ficticias de prueba)
eval/                 banco de evaluación (casos sintéticos de desarrollo)
tests/                pruebas automáticas
docs/                 ADR, contexto del proyecto, configuración y dependencias
vendor/htmx/          htmx 2.0.11 (servido localmente)
```


## Demo local sin IA: configuración explícita
Desde la raíz del proyecto, en una consola PowerShell nueva:
```powershell
$env:AI_ENABLED='0'
$env:AI_BUDGET_USD='0'
$env:AI_ALLOW_OPUS='0'
$env:APP_GMAIL_ENABLED='0'
$env:ANTIFRAUDE_PRUEBAS_REALES='0'
$env:ANTIFRAUDE_PRUEBAS_REALES_GMAIL='0'
Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:CLAUDE_MODEL -ErrorAction SilentlyContinue
$env:APP_DEMO_MODE='1'
cd backend
..\.venv\Scripts\python.exe -m antifraude
```
Abra `http://127.0.0.1:8790/`, pulse Empezar e introduzca el código de esa consola. Los tres botones son ejemplos sintéticos. Para probar archivos use `docs/entrega/ejemplos/01-sintetico.eml` a `03-sintetico.eml` (BAJO, ALTO, ALTO) y `04-ambiguo-sintetico.eml` (NO CONCLUYENTE). Si hay texto y archivo, el archivo tiene prioridad. Los campos Authentication-Results de esos archivos son datos de prueba, no autenticación real de correo. No abra sus enlaces. Guion completo: `docs/entrega/GUION_DEMO.md`.

Para repetir las pruebas JavaScript adicionales desde la raíz, si Node ya está instalado:
```powershell
node --test tests/ui/test_accesibilidad.cjs
```
Son once pruebas con DOM/temporizadores simulados; no sustituyen la verificación manual del lector ni requieren Node para ejecutar la aplicación. La suite Python incluye cinco pruebas HTTP contra Uvicorn real en loopback, con claves de sesión solo en memoria.


## Cierre local del 10 de noviembre
Ver [estado actual y evidencia](docs/DECISION_VERSION_FINAL.md), [revisión humana preparada](docs/REVISION_HUMANA_MVP.md) y [valor diferencial e hipótesis de negocio](docs/VALOR_DIFERENCIAL.md). Gmail real, Claude real, revisión humana y evaluación independiente siguen pendientes de sus permisos/datos. El sondeo de Linux del compañero es evidencia de portabilidad de la versión anterior; no una evaluación independiente de eficacia.
