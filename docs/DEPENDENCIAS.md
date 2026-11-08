# Dependencias del proyecto — registro de versiones, licencias y justificación

> Política (CLAUDE.md §9.6, ADR-0014): cada dependencia se justifica; versión exacta fijada; licencia verificada al instalar; nada se instala sin aprobación de la fase. Última actualización: **2026-11-08, Fase 0 (F0-01/F0-02)**.

## Intérprete
| Elemento | Versión | Origen / procedimiento | Licencia |
|---|---|---|---|
| CPython | **3.12.10** (64 bits; OpenSSL 3.0.16) | Python install manager oficial (`pymanager install 3.12-64`); 3.12.10 es la versión 3.12 más reciente que ofrece su índice | PSF |
Ruta: `%LOCALAPPDATA%\Python\pythoncore-3.12-64\`. Se invoca con `py -3.12`. El Python predeterminado del sistema sigue siendo 3.14 (sin cambios).
Entorno virtual del repo: `.venv` (ignorado por Git), creado con `py -3.12 -m venv .venv`; pip 25.0.1 (incluido, no actualizado).

## Dependencias directas aprobadas (Fase 0)
| Paquete | Versión | Uso | Licencia (metadatos del paquete) | Archivo |
|---|---|---|---|---|
| fastapi | 0.162.2 | API local | MIT | requirements.txt |
| pydantic | 2.14.3 | contratos y validación (ADR-0003) | MIT | requirements.txt |
| uvicorn | 0.54.0 | servidor ASGI en `127.0.0.1` | BSD-3-Clause | requirements.txt |
| jinja2 | 3.1.6 | plantillas de la UI (ADR-0012) | BSD (BSD-3-Clause) | requirements.txt |
| python-multipart | 0.0.33 | formularios enviados por htmx | Apache-2.0 | requirements.txt |
| pytest | 9.2.0 | pruebas | MIT | requirements-dev.txt |
| httpx | 0.28.1 | cliente de pruebas de FastAPI | BSD (BSD-3-Clause) | requirements-dev.txt |
Versiones = última estable publicada en PyPI el 2026-11-08 (`pip index versions`).

## Dependencias transitivas (instaladas automáticamente por las anteriores)
| Paquete | Versión | Requerido por | Licencia |
|---|---|---|---|
| starlette | 1.10.0 | fastapi | BSD-3-Clause |
| pydantic_core | 2.50.4 | pydantic | MIT |
| annotated-types | 0.8.0 | pydantic | MIT |
| typing-inspection | 0.4.5 | pydantic | MIT |
| typing_extensions | 4.16.0 | varios | PSF-2.0 |
| annotated-doc | 0.0.5 | fastapi | MIT |
| **opentelemetry-api** | 1.45.2 | **fastapi** | Apache-2.0 |
| anyio | 4.16.0 | starlette / httpx | MIT |
| idna | 3.20 | anyio / httpx | BSD-3-Clause |
| click | 8.5.1 | uvicorn | BSD-3-Clause |
| h11 | 0.16.0 | uvicorn / httpcore | MIT |
| MarkupSafe | 3.0.4 | jinja2 | BSD-3-Clause |
| httpcore | 1.0.9 | httpx (dev) | BSD-3-Clause |
| certifi | 2026.10.23 | httpx (dev) | MPL-2.0 |
| pluggy | 1.7.0 | pytest (dev) | MIT |
| iniconfig | 2.3.1 | pytest (dev) | MIT |
| packaging | 26.3 | pytest (dev) | Apache-2.0 OR BSD-2-Clause |
| Pygments | 2.21.0 | pytest (dev) | BSD-2-Clause |
| colorama | 0.4.6 | pytest / click (Windows) | BSD |
Bloqueo completo: `requirements.lock`. `pip check`: sin conflictos (2026-11-08).
**Nota sobre `opentelemetry-api`:** es solo la API de instrumentación; sin un SDK y un exportador configurados no envía datos. **No se instalará ni configurará ningún SDK/exportador de telemetría** (privacidad). ⏳ Confirmarlo con una prueba sin red en la Fase 0 (F0-05/F0-06).
**Licencia MPL-2.0 (`certifi`)**: copyleft débil por archivo; solo se usa sin modificar como dependencia de pruebas → compatible con el uso previsto.

## Recursos estáticos vendorizados
| Recurso | Versión | Origen | Verificación | Licencia |
|---|---|---|---|---|
| `vendor/htmx/htmx.min.js` | **2.0.11** (dist-tag `latest`; se descarta `next` 4.0.1) | paquete npm `htmx.org`, descargado con `npm pack` en un directorio temporal (sin instalar nada en el proyecto) | integridad sha512 del tarball = la publicada en el registro npm; SHA-256 del archivo: `d6fdc75f204e6bdefa99b69bf1e6d4ac69b8a364f77929f45c13476b4000f717` | 0BSD (`vendor/htmx/LICENSE`, SHA-256 `d3d2456f76414f2456104660ebd65aff1c04cd7966b942bdabd63f3cdb316a38`) |
Ubicación provisional `vendor/htmx/`; en F0-06 se servirá como estático local (sin CDN). La extensión SSE de htmx **no** se ha descargado (fase e).

## No instalado (se pedirá en su fase)
`anthropic` (d) · `tldextract` + PSL local, `rapidfuzz`, `beautifulsoup4` (b) · extensión SSE de htmx (e) · `keyring`, `google-auth-oauthlib`, `google-api-python-client` (f) · `pywebview`, `pystray`, `win11toast` (g).

## Auditoría de vulnerabilidades conocidas (misión 3, 2026-11-08)
- Método: consulta de las 26 versiones de `requirements.lock` a la base pública **OSV** (`https://api.osv.dev/v1/querybatch`, ecosistema PyPI) con `curl`. Solo se enviaron nombres y versiones. No se instaló `pip-audit` (no autorizado).
- Control positivo: la misma consulta para `Jinja2==2.10` devuelve 12 vulnerabilidades, así que la consulta funciona.
- Resultado: **0 vulnerabilidades conocidas** en las 26 dependencias fijadas a esta fecha.
- Limitación: es una foto del momento. Repetirla antes de la entrega y cuando se añadan `anthropic` o las librerías de Google (R-37 queda mitigado, no cerrado).
