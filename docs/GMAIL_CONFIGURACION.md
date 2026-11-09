# Integración con Gmail: estado y pasos para activarla

> Estado revisado el 09-11-2026: **puente de aplicación implementado, sin cuenta conectada ni OAuth real autorizado**. El flujo conector → minimización → reglas/enlaces pasivos → motor → alertas del panel está probado con dobles. Los SDK opcionales están instalados y su compatibilidad comprobada exclusivamente en el entorno temporal autorizado; eso no es una integración real con Gmail.

## Piezas y alcance verificado

| Pieza | Implementación | Evidencia/estado |
|---|---|---|
| Cursor inicial, mensajes nuevos, deduplicación, inclusión de spam y resincronización | `connectors/gmail.py` | Pruebas simuladas; primera consulta solo registra el cursor, sin leer el buzón antiguo |
| Paginación, raw y traducción de errores | `connectors/gmail_api.py` | Pruebas con servicio simulado y SDK auténtico con HTTP simulado |
| Consentimiento por petición/página | `GmailApiClient.set_read_guard` y `app/gmail_bridge.py` | Revocación entre páginas impide la siguiente operación del adaptador; una operación SDK ya en curso puede terminar, pero su resultado se descarta tras revocar |
| OAuth de escritorio y almacenamiento seguro | `build_gmail_service`, `ensure_secure_keyring` | Firmas e integración del código comprobadas con OAuth/keyring simulados; **OAuth, cuenta y almacén real sin probar ni autorizar** |
| Sondeo, ciclo de vida y alertas del panel | `app/gmail_bridge.py`, `app/gmail_routes.py` | Implementado y probado con clientes sintéticos: errores, cierre/caducidad, separación de navegadores, retención acotada y guard por sesión |
| Ingesta RFC 822 y minimización | `analysis/ingest.py` → pipeline | Reutiliza el análisis común; Gmail usa un pipeline sin IA externa |
| Errores de ingesta | `GmailPoller(on_failure=…)` | Aviso NO CONCLUYENTE/parcial, sin registrar el cuerpo ni mostrar detalles internos |
| Desconexión local | `forget_local_token`, ciclo del bridge | Código y dobles comprobados; advierte si no pudo borrar la credencial. Borrado real de keyring pendiente |

El panel conserva como máximo 20 tarjetas minimizadas y el contador de ALTO de la conexión para no ocultar un riesgo previo al recortar tarjetas. No almacena cuerpos completos, asunto/remitente ni identificadores de Gmail en las alertas del panel. Desconectar borra esas alertas. El sondeo del panel no prolonga la sesión y evita reemplazar controles cuando no cambió el estado.

## Dependencias opcionales: instalación autorizada y acotada

La autorización recibida cubre **solo** `C:/Users/dialm/Documents/ChatGPT/Hackaton/.mvp-final/gmail-venv`; instalación completada allí. El entorno `.venv` y las 26 versiones de [requirements.lock](../requirements.lock) del proyecto se conservan.

[requirements-gmail.lock](../requirements-gmail.lock) fija las 53 versiones del entorno opcional, con las 26 base idénticas. Coinciden con los metadatos instalados y `pip check` es correcto. Paquetes directos: google-auth-oauthlib 1.5.0, google-api-python-client 2.201.0 y keyring 25.7.0. Fuentes/licencias y reproducción de la comprobación en [GMAIL_PREPARACION_REAL.md](GMAIL_PREPARACION_REAL.md).

[scripts/verificar_gmail_sdk.py](../scripts/verificar_gmail_sdk.py) pasó **8 comprobaciones** con SDK auténtico y HTTP/OAuth/keyring simulados. Red, DNS, navegador, servidor local y almacén personal están vetados. Se verifica compatibilidad de versiones, firmas, solicitudes, errores y controles, sin abrir Google, obtener tokens ni leer una cuenta. No es una prueba real de Gmail y no sustituye la autorización de conexión.

## Configuración y consentimiento

- `APP_GMAIL_ENABLED=0` por defecto. El arranque no abre OAuth ni conecta cuentas.
- `APP_GMAIL_CLIENT_SECRET` designa un JSON OAuth externo al repositorio. La configuración rechaza rutas dentro del proyecto; no incluirlo en Git ni en el chat.
- La activación de la flag no basta: el panel requiere sesión local válida, CSRF/Origin y consentimiento explícito para conectar la cuenta de pruebas.
- Cada nueva conexión del panel retira primero la credencial local anterior y solicita selección/consentimiento de cuenta en Google. Si no puede retirar el permiso previo, no inicia la conexión. El permiso de una sesión no se presta a otro navegador.
- El flujo está preparado para loopback `127.0.0.1` con puerto efímero y espera OAuth acotada; los parámetros se han verificado contra la firma instalada, pero el diálogo real no se ha ejecutado.
- Gmail se analiza en el equipo **sin transmitirlo a IA externa**, incluso si la entrada manual tuviera IA configurada. Conectar Gmail no autoriza Anthropic, Opus ni otra API de pago.
- Mantener `AI_ENABLED=0`, `AI_BUDGET_USD=0`, `AI_ALLOW_OPUS=0` y ambas flags de integraciones reales a cero en la fase actual.

## Cuenta de pruebas: pasos posteriores que requieren permiso

1. El usuario elige o crea una cuenta Gmail de pruebas, separada de su cuenta personal, y una cuenta emisora para mensajes sintéticos.
2. Configura un proyecto Google Cloud propio, Gmail API, pantalla de consentimiento/usuario de prueba y cliente OAuth de escritorio, con el único scope `https://www.googleapis.com/auth/gmail.readonly`. No se habilitan servicios de pago ni facturación por esta guía.
3. Conserva el JSON fuera del repositorio y lo configura localmente, sin compartir secretos, códigos o tokens por chat.
4. Autoriza expresamente la conexión de esa cuenta y el entorno que ejecutará la app. La instalación temporal previa no autoriza usar la cuenta ni instalar en otro entorno.
5. Tras esa autorización, activa las variables de Gmail y concede el consentimiento del panel/Google. Comprueba lectura inicial del cursor y envía después mensajes sintéticos desde la cuenta emisora.
6. Registra versiones y resultados reales de recepción, clasificación, duplicados, cuota/autenticación y desconexión; no inventar un resultado esperado de OAuth o de la cuenta antes de medirlo.
7. Desconecta en el panel y comprueba la retirada del token local. **La revocación del acceso en Google es una acción manual adicional** desde [los permisos de la cuenta](https://myaccount.google.com/permissions); borrar la credencial de este equipo no revoca automáticamente el permiso remoto.

La cuenta, la configuración Google Cloud, el OAuth real y el keyring real siguen pendientes y no autorizados. La posible caducidad del modo Testing debe verificarse en la configuración y documentación oficial vigentes; no se fija una fecha de reautorización ficticia para una cuenta todavía sin conectar.

## Permisos y recuperación de errores

Solo `gmail.readonly`: no se envían correos, modifican etiquetas, marcan como leídos, mueven ni borran mensajes. El conector incluye spam para que no queden fuera mensajes sospechosos.

- 401 y 403 desconocidos/de permisos conservan el tratamiento de autorización. Un 403 de política de dominio puede requerir al administrador y no resolverse reautorizando.
- 403 con motivos explícitos dailyLimitExceeded/rateLimitExceeded/userRateLimitExceeded y 429 son cuota: estado visible, lote detenido y pendientes conservados sin agotar sus intentos por ese motivo.
- 404 del historial produce resincronización acotada a los 20 mensajes recientes, con deduplicación; no implica revisar todo el buzón.
- El límite local es 40 mensajes por consulta. No demuestra por sí solo cumplimiento de todas las cuotas: paginación y otros consumos también cuentan.
- El bridge aplica espera creciente tras errores y recupera el intervalo normal cuando la consulta funciona. No hay reintento inmediato dentro del lote ni se interpreta Retry-After; no se garantiza cuándo desaparecerá una cuota diaria.

R-69 está validado con simulaciones. Los detalles remotos se tratan de forma acotada y no se presentan como mensaje del servidor al usuario. Referencia de clasificación: [errores oficiales de Gmail](https://developers.google.com/workspace/gmail/api/guides/handle-errors), sin que consultarla signifique ejecutar la API.

## Prueba real y límites pendientes

`tests/integracion_real/test_gmail_real.py` permanece bloqueada salvo autorización específica, librerías presentes, `ANTIFRAUDE_PRUEBAS_REALES_GMAIL=1` y `GMAIL_CLIENT_SECRET` externo. Esa variable pertenece al test; la aplicación utiliza `APP_GMAIL_CLIENT_SECRET`. No activar el test como parte de la comprobación de compatibilidad. Véase [PRUEBAS_INTEGRACION_REAL.md](PRUEBAS_INTEGRACION_REAL.md).

Falta verificar con cuenta autorizada el consentimiento oficial, lectura real de nuevos mensajes, renovación, manejo efectivo del almacén seguro y retirada local. El puente y los controles ya implementados permiten preparar esa prueba; no necesitan presentarse como código pendiente. La revocación remota sigue siendo manual y no está implementada como llamada automática.

El producto es un prototipo académico, sin afirmaciones de preparación comercial ni cumplimiento bancario. Datos y requisitos del scope restringido necesitan revisión específica antes de cualquier uso posterior. No publicar correos ni secretos y no convertir compatibilidad simulada en evidencia de una integración real.
