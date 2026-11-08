# Integración con Gmail: estado y pasos para activarla

> Estado (2026-11-08): **preparada, NO conectada**. La lógica está probada con un servicio de Gmail **simulado** (`tests/test_e_gmail_simulado.py`, `tests/test_e_gmail_api_simulada.py`). La parte de OAuth y keyring (`build_gmail_service`) está escrita pero **sin probar**, porque faltan las librerías y el cliente OAuth. No se ha accedido a ninguna cuenta real.

## Piezas preparadas
| Pieza | Archivo | Estado |
|---|---|---|
| Conector `history.list` (primera consulta sin leer el buzón antiguo, resincronización si el historyId caduca, deduplicación, SPAM, autorización caducada) | `connectors/gmail.py` | Probado (simulado) |
| Adaptador de la API real (paginación, `format=raw`, traducción de errores 404/401/403) | `connectors/gmail_api.py` → `GmailApiClient` | Probado con un servicio simulado |
| Sondeo en segundo plano con parada limpia | `connectors/gmail_api.py` → `GmailPoller` | Probado |
| OAuth de app de escritorio (redirección loopback) + token en el keyring de Windows | `connectors/gmail_api.py` → `build_gmail_service` | **Sin probar** |
| Ingesta común RFC 822 → pipeline | `analysis/ingest.py` → `from_raw` | Probado |
| Arranque del sondeo desde la aplicación y alertas de Gmail en el panel | — | **Pendiente** (es el último paso, una vez probado OAuth) |

## Pasos (los hace el usuario, con autorización)
1. **Cuenta de pruebas**: crear una cuenta Gmail nueva solo para el hackatón, más otra cuenta emisora para enviar los mensajes de la demo.
2. **Google Cloud Console** → crear un proyecto → «APIs y servicios» → habilitar la **Gmail API**.
3. **Pantalla de consentimiento OAuth** → tipo *External*, estado **Testing** → añadir la cuenta de pruebas como *usuario de prueba*. Scope: `https://www.googleapis.com/auth/gmail.readonly` (scope restringido; en modo Testing basta para hasta 100 usuarios de prueba).
4. **Credenciales** → «Crear ID de cliente OAuth» → tipo **Aplicación de escritorio** → descargar el JSON. **Guardarlo fuera del repositorio** (por ejemplo `C:\Users\<usuario>\secretos\client_secret.json`). `.gitignore` ya bloquea `client_secret*.json`.
5. **Autorizar la instalación** (versiones exactas, que se fijarán y registrarán en `docs/DEPENDENCIAS.md`): `google-auth-oauthlib`, `google-api-python-client`, `keyring`.
6. **Primera autorización**: se abre el navegador con el consentimiento de Google y el token de actualización se guarda en el Administrador de credenciales de Windows, nunca en archivos ni en registros.
7. **Caducidad**: en modo Testing, el token de actualización caduca a los **7 días** (pendiente de confirmar, V-11). Hay que **volver a autorizar el 10 u 11 de noviembre**, antes de la demo.
8. **Desconectar**: revocar el acceso en https://myaccount.google.com/permissions y borrar el token local (`forget_local_token`).

## Qué falta en el código cuando se autorice
1. Probar `build_gmail_service` con la cuenta de pruebas.
2. Arrancar `GmailPoller` desde la aplicación (por ejemplo con `APP_GMAIL_CLIENT_SECRET=<ruta>`). Cada mensaje nuevo pasa por `from_raw` y por el pipeline común, y las alertas se muestran en el panel.
3. Prueba de extremo a extremo: enviar un correo desde la cuenta emisora y comprobar que la alerta aparece.

## Limitaciones conocidas
- Datos de un scope restringido: un producto comercial necesitaría verificación de Google y una evaluación CASA. Enviar fragmentos a la IA podría contar como «transmisión» (V-15). Prototipo académico: no afirmar que cumple esos requisitos.
- Los correos de prueba pueden llegar a SPAM: el conector los incluye.
