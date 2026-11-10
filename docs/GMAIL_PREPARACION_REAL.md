# Preparación de Gmail real — estado 10-11-2026

## Implementado y verificado sin cuenta
La aplicación ya une conector, minimización, motor y alertas del panel. Las pruebas inyectan un servicio SIMULADO y lo etiquetan; no prueban OAuth ni una cuenta real. Hay consentimiento por sesión, separación entre navegadores, lectura inicial solo del cursor, errores visibles, resguardo de cola, limpieza y revalidación antes de cada petición paginada. La IA de Gmail permanece desactivada, independiente de la entrada manual. El sondeo HTTP no prolonga la sesión ni reemplaza controles cuando no hay cambios. Se retienen como máximo 20 tarjetas minimizadas y el contador de ALTO de esa conexión.

## Instalación opcional autorizada y completada

El usuario autorizó exclusivamente el entorno temporal `C:/Users/dialm/Documents/ChatGPT/Hackaton/.mvp-final/gmail-venv`. La instalación ya se realizó allí, sin modificar el entorno `.venv` del proyecto. [requirements-gmail.lock](../requirements-gmail.lock) fija **53 paquetes**, incluidos los **26 del lock base con las mismas versiones**; las 53 versiones instaladas coinciden y `pip check` no detecta requisitos rotos. No hay autorización implícita para instalar estos paquetes en otros entornos.

Paquetes opcionales directos de [requirements-gmail.txt](../requirements-gmail.txt):

- google-auth-oauthlib 1.5.0 (Apache 2.0), Python>=3.10: [PyPI oficial](https://pypi.org/project/google-auth-oauthlib/).
- google-api-python-client 2.201.0 (Apache 2.0), Python>=3.10: [PyPI oficial](https://pypi.org/project/google-api-python-client/).
- keyring 25.7.0 (MIT), Python>=3.9: [PyPI oficial](https://pypi.org/project/keyring/).

Metadatos consultados el 09-11-2026. La instalación de dependencias y la compatibilidad local están verificadas; no equivalen a autorizar OAuth, acceso al almacén personal, conexión de una cuenta ni lectura de Gmail.

## Compatibilidad del SDK comprobada sin servicios reales

[scripts/verificar_gmail_sdk.py](../scripts/verificar_gmail_sdk.py): **8 comprobaciones correctas** con los SDK auténticos instalados y transportes HTTP/OAuth/keyring simulados. Cubre versiones/firmas, solicitudes y paginación mediante discovery incluido, clases HttpError reales construidas desde respuestas simuladas, denegación entre páginas, consentimiento de selección de cuenta, fallo de retirada del token simulado y rechazo de backend inseguro simulado. Activa vetos de red, DNS, servidor local, navegador y credenciales personales.

Desde la raíz del repositorio puede repetirse, exclusivamente con ese entorno ya autorizado:

```powershell
& 'C:/Users/dialm/Documents/ChatGPT/Hackaton/.mvp-final/gmail-venv/Scripts/python.exe' -B scripts/verificar_gmail_sdk.py
```

El script fuerza IA, presupuesto y Gmail a cero y retira las variables de claves/rutas de credenciales del proceso. No instala nada. Si faltan dependencias termina con error explícito, no con un skip que parezca éxito. Es una comprobación adicional de compatibilidad, separada de la suite del entorno base y de la prueba real de integración. Las versiones o firmas compatibles no demuestran que funcionen la cuenta, el consentimiento de Google o el Administrador de credenciales de Windows.

## Revalidación del entorno autorizado — 10-11-2026

Se ha comprobado la existencia de `.mvp-final/gmail-venv`, sin recrearlo ni instalar paquetes. Sus **53 versiones** coinciden con `requirements-gmail.lock`; las **26 del lock base** se conservan. `pip check`: **No broken requirements found**. El SDK Anthropic no está instalado en este entorno.

Con el código actual, `scripts/verificar_gmail_sdk.py` dio **8 comprobaciones correctas en 0,053 s**, sin saltos, manteniendo IA/presupuesto/Gmail/flags reales a cero. `TEMP` y `TMP` apuntaron a la carpeta de trabajo existente `C:/Users/dialm/Documents/ChatGPT/Hackaton/.mvp-final/sdk-temp-final`. Los transportes, OAuth y backend keyring fueron dobles; estuvieron vetados DNS, sockets, navegador y credenciales personales. El resultado verifica compatibilidad instalada e integración simulada, **no una conexión de cuenta**.

Para repetir esta misma comprobación sin cuenta, desde la raíz y usando solo el entorno existente:

```powershell
$env:TEMP='C:/Users/dialm/Documents/ChatGPT/Hackaton/.mvp-final/sdk-temp-final'
$env:TMP=$env:TEMP
$env:PYTHONDONTWRITEBYTECODE='1'
& 'C:/Users/dialm/Documents/ChatGPT/Hackaton/.mvp-final/gmail-venv/Scripts/python.exe' -B scripts/verificar_gmail_sdk.py
```

## Permiso mínimo que se pedirá para Google — todavía NO concedido

La instalación temporal ya autorizada no concede ninguno de estos permisos. La futura decisión debe identificar la cuenta y el proyecto localmente, sin publicar direcciones, JSON ni secretos en el chat.

- [ ] Elegir o crear **una cuenta Gmail de pruebas**, vacía de datos personales, y confirmar que no es el Gmail personal. Para emitir los correos sintéticos, el usuario utilizará manualmente otra cuenta de pruebas; el asistente no enviará correo.
- [ ] Permitir crear o configurar **un proyecto Google Cloud del usuario**, habilitando únicamente Gmail API para esta prueba. No activar facturación, servicios de pago ni permisos de organización amplios. Si no hay permiso administrativo, registrar el bloqueo y conservar la demo manual.
- [ ] Configurar la pantalla de consentimiento y su audiencia. Para cuentas externas a una organización Workspace: audiencia External, pruebas/Testing y añadir explícitamente la cuenta de pruebas en Test users; si se utiliza una audiencia Internal, confirmar que la cuenta pertenece a esa organización. No publicar la aplicación para eludir una restricción. [Configuración oficial](https://developers.google.com/workspace/guides/configure-oauth-consent).
- [ ] Crear un cliente OAuth **Desktop app**, sin cuenta de servicio ni delegación de dominio, y descargar su JSON en una ubicación privada **fuera del repositorio y de la entrega**, por ejemplo `C:/Users/<usuario>/secretos-antifraude/client_secret_pruebas.json`. No leerlo ni incorporarlo al chat; indicar a la app solo su ruta. La validación local rechaza rutas dentro del repositorio. [Cliente de escritorio oficial](https://developers.google.com/workspace/gmail/api/quickstart/python).
- [ ] Conceder **solo** `https://www.googleapis.com/auth/gmail.readonly`. Es un scope restringido que permite lectura del correo; no está limitado por Google a mensajes nuevos. La selección de nuevos mensajes y la recuperación de hasta 20 recientes son límites de nuestra aplicación. No pedir `gmail.send`, `gmail.modify`, `gmail.compose` ni `https://mail.google.com/`; `gmail.metadata` no permite analizar el cuerpo. [Scopes oficiales](https://developers.google.com/workspace/gmail/api/auth/scopes).
- [ ] Permitir abrir el OAuth oficial de esa cuenta de pruebas y utilizar el almacén seguro de Windows/keyring **solo para la entrada del proyecto** (`hackaton-finance-antifraude-gmail` / `refresh-token`). No enumerar ni exportar otras credenciales. El backend real debe verificarse al ejecutar, antes de guardar. Si Google impide el flujo, se registra el mensaje seguro y no se desactivan controles.
- [ ] Autorizar **una sesión de prueba acotada**, hasta 10 minutos de diagnóstico, con los cuatro correos sintéticos de `docs/entrega/ejemplos/`, y retirar después el permiso local. Permitir la revocación remota desde la cuenta para comprobar el error de autorización y el cierre. Nada de esto autoriza transmitir mensajes a Claude.

La configuración futura usaría el intérprete del entorno Gmail ya autorizado, JSON externo, `APP_GMAIL_ENABLED=1` y, para reconocer Banco Ficticio en estos ejemplos, `APP_DEMO_MODE=1`. IA, presupuesto y Opus seguirían en cero. Los indicadores de pruebas reales solo se activarían para un caso de integración concreto si esa ejecución se incluye en el permiso; no ejecutar toda la carpeta de integraciones. Hasta que llegue esa decisión **todas las flags continúan a cero**.

## Plan de aceptación de la primera conexión real — pendiente

Registrar versión/commit, Python/SDK/Windows, alcance consentido y fecha; usar etiquetas como «cuenta de pruebas A», sin cuerpos, direcciones, códigos, cookies, credenciales ni tokens. Cada fila se marcará real, simulada o pendiente por separado.

| Comprobación tras la autorización | Evidencia para darla por superada |
|---|---|
| Consentimiento y cuenta correcta | El usuario identifica la cuenta de pruebas en Google; scope único readonly. No hay lectura al arrancar sin consentimiento del panel |
| Inicio sin buzón antiguo | La primera consulta fija el cursor y no genera alertas de mensajes previos. Se conoce la excepción acotada de resincronización: hasta 20 recientes si el cursor caduca |
| Flujo de extremo a extremo | El usuario envía manualmente, después de conectar, los cuatro correos sintéticos. Se observan recepción→minimización→riesgo→aviso: BAJO, ALTO, ALTO y NO CONCLUYENTE, con explicación, acción segura y limitaciones. Registrar latencia medida, sin inventarla |
| Deduplicación y permiso de solo lectura | Varias consultas no duplican el mismo mensaje. El asistente no envía, mueve, borra ni marca correo como leído |
| Separación y retención | Otro navegador emparejado no ve ni desconecta alertas ajenas. Se conserva como máximo el número de tarjetas documentado, sin cuerpos/asuntos/remitentes completos; el resumen de ALTO persiste dentro de esa conexión |
| Desconexión/caducidad/cierre | Se detienen nuevas lecturas; se descartan resultados en curso que pierdan consentimiento; se borran alertas y se comprueba el retiro del permiso local sin mostrarlo. Si OAuth se cancela o devuelve tarde, no comienza lectura y se retira cualquier token tardío |
| Fallo de autorización | Revocación explícita desde Google durante la prueba: estado comprensible; tras detectarse el error de autorización, sin nuevas lecturas ni reutilización entre sesiones. El fallo al retirar un permiso local no se considera éxito de limpieza |
| Renovación | Solo se marca real si se observa una renovación auténtica de credenciales de la cuenta autorizada. Si no ocurre dentro del bloque acotado, queda pendiente; una simulación o la selección de cuenta no prueba renovación |
| Cuotas y errores no provocables con seguridad | Se conservan como simulados los 403/429 y los fallos de almacenamiento ya cubiertos; no saturar Google ni manipular secretos para forzarlos. Anotar cualquier error real encontrado sin copiar contenido sensible |
| Revocación final | Retirar permiso local y revocar también el acceso en Google. Borrar el token local no acredita revocación remota; comprobar ambas por separado |

Si una fila no puede probarse en la sesión acotada, documentar por qué y mantenerla pendiente, sin una cadena de reintentos. Las operaciones ya iniciadas pueden terminar antes de descartarse: no se promete cancelación instantánea del SDK. No se autoriza todavía ejecutar este plan.

## Conexión posterior: autorización separada
1. El usuario elige/crea una cuenta de pruebas, distinta de su Gmail personal. No conectar ninguna cuenta en esta fase.
2. En un proyecto Google Cloud controlado por el usuario: habilitar Gmail API, consentimiento en Testing, añadir la cuenta como usuario de prueba; crear cliente OAuth de escritorio. Scope único: gmail.readonly. No habilitar facturación ni servicios de pago para este paso.
3. Guardar el JSON fuera del repositorio. No copiar el JSON, claves, códigos, cookies ni tokens al chat. La configuración de la app rechaza una ruta dentro del proyecto.
4. El entorno temporal opcional ya dispone de las dependencias, pero la conexión de una cuenta sigue necesitando autorización expresa. Hasta entonces mantener APP_GMAIL_ENABLED=0 (valor por defecto), IA=0, presupuesto=0, Opus=0 y ambas flags de pruebas reales=0. Solo tras autorizar la cuenta se configura APP_GMAIL_ENABLED=1 y APP_GMAIL_CLIENT_SECRET=<ruta externa> en el entorno aprobado para ejecutarla. El panel exige además consentimiento por sesión; activar la flag no inicia OAuth al arrancar. Una instalación en otro entorno requeriría permiso propio.
5. El botón exige elegir y consentir la cuenta en Google en cada nueva conexión del panel; antes retira el permiso local previo para evitar reutilizar una cuenta residual de otra sesión. Si falla ese borrado no se abre la conexión. El botón abre el consentimiento oficial; la espera local se acota a 120 s, en 127.0.0.1 con puerto efímero y sin imprimir URL OAuth. El código está preparado para guardar el token en Credential Manager/keyring seguro; el almacén real aún no se ha probado. Un OAuth cancelado puede terminar su petición ya en curso, pero se descarta el resultado y se retira cualquier token tardío; no comienza lectura de mensajes tras cerrar/caducar/desconectar.
6. Enviar desde otra cuenta de pruebas un correo sintético sin enlaces reales, observar recepción, nivel/evidencias/recomendación; repetir para duplicados, error y desconexión. Esa prueba solo se registra como REAL cuando se ejecute, con versiones y resultados, sin datos sensibles.
7. Desconectar detiene recepción, borra alertas y retira token local; revocar también acceso desde los permisos de la cuenta Google. Borrar token local no equivale a revocar remotamente. Si falla el borrado local se avisa y no se presta el permiso a otro navegador.

La demo manual funciona independientemente. Ninguna llamada a Anthropic queda autorizada por conectar Gmail. La compatibilidad local de los SDK está comprobada. Siguen pendientes y no autorizados OAuth real, la cuenta de pruebas, la lectura de mensajes reales y el keyring/Administrador de credenciales real. No presentar compatibilidad ni simulaciones como recepción verificada de una cuenta.
