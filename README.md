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
El estado detallado y actualizado está en `docs/contexto/15_SEGUIMIENTO.md` y en `docs/contexto/08_PROGRESO.md`. Lo pendiente y los riesgos, en `docs/contexto/09_PENDIENTES.md`.

## 8. Estructura
```
backend/antifraude/   aplicación (contracts, core, connectors, analysis, intel, ai, risk, app)
backend/data/         directorio de entidades (reales pendientes de verificar + ficticias de prueba)
eval/                 banco de evaluación (casos sintéticos de desarrollo)
tests/                pruebas automáticas
docs/                 ADR, contexto del proyecto, configuración y dependencias
vendor/htmx/          htmx 2.0.11 (servido localmente)
```
