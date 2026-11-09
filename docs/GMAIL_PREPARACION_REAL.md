# Preparación de Gmail real — estado 09-11-2026

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

## Conexión posterior: autorización separada
1. El usuario elige/crea una cuenta de pruebas, distinta de su Gmail personal. No conectar ninguna cuenta en esta fase.
2. En un proyecto Google Cloud controlado por el usuario: habilitar Gmail API, consentimiento en Testing, añadir la cuenta como usuario de prueba; crear cliente OAuth de escritorio. Scope único: gmail.readonly. No habilitar facturación ni servicios de pago para este paso.
3. Guardar el JSON fuera del repositorio. No copiar el JSON, claves, códigos, cookies ni tokens al chat. La configuración de la app rechaza una ruta dentro del proyecto.
4. El entorno temporal opcional ya dispone de las dependencias, pero la conexión de una cuenta sigue necesitando autorización expresa. Hasta entonces mantener APP_GMAIL_ENABLED=0 (valor por defecto), IA=0, presupuesto=0, Opus=0 y ambas flags de pruebas reales=0. Solo tras autorizar la cuenta se configura APP_GMAIL_ENABLED=1 y APP_GMAIL_CLIENT_SECRET=<ruta externa> en el entorno aprobado para ejecutarla. El panel exige además consentimiento por sesión; activar la flag no inicia OAuth al arrancar. Una instalación en otro entorno requeriría permiso propio.
5. El botón exige elegir y consentir la cuenta en Google en cada nueva conexión del panel; antes retira el permiso local previo para evitar reutilizar una cuenta residual de otra sesión. Si falla ese borrado no se abre la conexión. El botón abre el consentimiento oficial; la espera local se acota a 120 s, en 127.0.0.1 con puerto efímero y sin imprimir URL OAuth. El código está preparado para guardar el token en Credential Manager/keyring seguro; el almacén real aún no se ha probado. Un OAuth cancelado puede terminar su petición ya en curso, pero se descarta el resultado y se retira cualquier token tardío; no comienza lectura de mensajes tras cerrar/caducar/desconectar.
6. Enviar desde otra cuenta de pruebas un correo sintético sin enlaces reales, observar recepción, nivel/evidencias/recomendación; repetir para duplicados, error y desconexión. Esa prueba solo se registra como REAL cuando se ejecute, con versiones y resultados, sin datos sensibles.
7. Desconectar detiene recepción, borra alertas y retira token local; revocar también acceso desde los permisos de la cuenta Google. Borrar token local no equivale a revocar remotamente. Si falla el borrado local se avisa y no se presta el permiso a otro navegador.

La demo manual funciona independientemente. Ninguna llamada a Anthropic queda autorizada por conectar Gmail. La compatibilidad local de los SDK está comprobada. Siguen pendientes y no autorizados OAuth real, la cuenta de pruebas, la lectura de mensajes reales y el keyring/Administrador de credenciales real. No presentar compatibilidad ni simulaciones como recepción verificada de una cuenta.
