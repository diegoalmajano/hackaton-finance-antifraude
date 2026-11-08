# Asistente antifraude — prototipo para Hackfinance (BEST UC3M)

Asistente de IA que **ayuda a reconocer estafas financieras en mensajes escritos** (correo, SMS…), pensado para personas mayores y clientes de banca. Analiza el texto y los enlaces **sin abrirlos**, explica en español sencillo qué ha encontrado y qué no ha podido comprobar, y deja **siempre la decisión al usuario**.

> **Estado: prototipo académico en desarrollo**, no es un producto comercial. Consulte la sección «Estado y limitaciones». Nada de lo que se muestra como simulado se presenta como real.

## 1. Requisitos
- Windows 10/11 con PowerShell (probado en Windows 11).
- **Python 3.12** (64 bits). Comprobación: `py -3.12 --version`.
  - Si no lo tiene: instálelo desde python.org o con el gestor oficial de Python (`pymanager install 3.12-64`).
- Un navegador moderno (Edge, Chrome o Firefox).
- No hace falta Node, Rust, Docker ni conexión a Internet para ejecutar la aplicación.

## 2. Instalación (una sola vez)
Abra PowerShell en la carpeta del proyecto (la que contiene este README):
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```
- `requirements.txt` contiene las dependencias de ejecución, con versiones exactas.
- `requirements-dev.txt` añade las de pruebas.
- `requirements.lock` es el bloqueo completo.
- Licencias y justificación de cada dependencia: `docs/DEPENDENCIAS.md`.

## 3. Configuración (opcional)
Todo funciona sin configurar nada. Las variables se definen en la consola. El asistente **no** lee archivos `.env`; `.env.example` es solo una referencia. Detalle: `docs/CONFIGURACION.md`.

| Variable | Por defecto | Para qué |
|---|---|---|
| `APP_PORT` | `8790` | Puerto local (siempre `127.0.0.1`) |
| `APP_LOG_LEVEL` | `INFO` | Detalle de los registros |
| `ANTHROPIC_API_KEY` | vacía | Análisis con IA (opcional; sin clave, la IA figura como «no configurada») |
| `CLAUDE_MODEL` | vacío | Modelo de Claude (pendiente de elegir por medición) |

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
Requiere la librería oficial `anthropic` (su instalación está **pendiente de autorización**), una clave (`ANTHROPIC_API_KEY`) y un modelo (`CLAUDE_MODEL`: `claude-opus-5-5` o `claude-sonnet-5-5`; la elección se hará midiendo). Sin ellos, la aplicación funciona con reglas y análisis de enlaces, y lo indica: «análisis parcial — IA no disponible».

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
Ejecuta las pruebas automáticas de contratos, seguridad, interfaz, configuración, registros, banco de evaluación y directorio de entidades. Todas son locales: no usan Internet ni APIs de pago.

## 6. Seguridad y privacidad (resumen)
- Solo escucha en `127.0.0.1`. Se accede mediante un emparejamiento con un código de un solo uso. La sesión usa una cookie HttpOnly y SameSite=Strict, y las operaciones están protegidas con CSRF, Host y Origin. La CSP es estricta y no hay recursos externos.
- **Los enlaces nunca se abren**: el análisis es pasivo, sin visitas ni consultas DNS a dominios sospechosos.
- Los registros no incluyen códigos, cookies, tokens, claves ni contenido de mensajes.
- Arquitectura y decisiones: `docs/adr/` (ADR-0001 a 0015) y `docs/contexto/`.

## 7. Estado y limitaciones
| Funcionalidad | Estado |
|---|---|
| Análisis manual (texto y `.eml`), extracción de enlaces, filtro por reglas | Implementado y probado |
| Análisis **pasivo** de enlaces (dominios parecidos, texto visible ≠ destino, acortadores, IP, punycode) | Implementado y probado |
| Motor de riesgo determinista (4 niveles, sin porcentajes; un error nunca da BAJO) | Implementado y probado |
| Alertas preventiva y definitiva con explicación, evidencias, incertidumbres y recomendaciones | Implementado y probado |
| Interfaz accesible en español con sesión segura | Implementada; prueba manual en navegador hecha; pendientes: CSP en consola, teclado completo, zoom 200 % y contraste medido |
| Análisis con Claude | Implementado y probado **con respuestas simuladas**; sin llamadas reales (falta autorizar la librería y el presupuesto) |
| Gmail | Conector implementado y probado con un **Gmail simulado**; conexión real **bloqueada** (credenciales OAuth y librerías no autorizadas) |
| Directorio de bancos reales | Preparado; **dominios oficiales pendientes de verificar** (por eso la demo usa el banco ficticio) |
| RDAP y reputación de URLs | No configurados (opcionales; se declaran como no comprobados) |
| Escritorio (bandeja, notificaciones nativas) | No implementado (fase opcional) |
| Idioma de los mensajes | Las reglas están pensadas para **español**; mensajes en otros idiomas pueden no detectarse por su contenido |

Más detalle: `docs/contexto/15_SEGUIMIENTO.md`, `08_PROGRESO.md` y `09_PENDIENTES.md`.

## 8. Estructura
```
backend/antifraude/   aplicación (contracts, core, connectors, analysis, intel, ai, risk, app)
backend/data/         directorio de entidades (reales pendientes de verificar + ficticias de prueba)
eval/                 banco de evaluación (casos sintéticos de desarrollo)
tests/                pruebas automáticas
docs/                 ADR, contexto del proyecto, configuración y dependencias
vendor/htmx/          htmx 2.0.11 (servido localmente)
```
