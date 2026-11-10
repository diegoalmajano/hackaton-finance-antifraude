# Accesibilidad: comprobación parcial y protocolo de aceptación

Fecha: 08-11-2026. Base de código: `71c5917`, rama `feat/fase-0`.
Pendientes: R-58, R-43, V-26 y V-25. Estado vigente: **abiertos; verificación parcial en navegador y correcciones locales**.

## Primera revisión: alcance anterior a la prueba en navegador

- Línea base local: **674 passed, 4 skipped, 1 xfailed, 1 warning** (11,07 s).
- IA desactivada y presupuesto cero; integraciones reales de Claude y Gmail desactivadas. Clave Anthropic y modelo retirados del proceso. No se instalaron dependencias ni se ejecutaron Claude Code/ECC.
- Revisión estática de `tests/test_d_accesibilidad.py`, plantillas, CSS y JavaScript. Las nueve regresiones existentes están incluidas en la línea base; no equivalen a operar un navegador o escuchar un lector de pantalla.
- Contraste calculado con Python estándar sobre los valores hexadecimales de `backend/antifraude/app/static/css/app.css`. No se midieron estilos computados en navegador, controles nativos, modos del sistema ni todos los estados posibles.
- No se abrió un navegador, no se leyó el conjunto sellado y no se cambiaron reglas, contratos ni comportamiento.
- El primer intento de pytest bajo el aislamiento de este chat produjo errores y se interrumpió. La ejecución posterior con acceso al repositorio terminó correctamente. No se atribuyen esos errores a una regresión del producto.

## Contraste de la paleta declarada

Método: cada canal sRGB se divide entre 255; si c <= 0,04045 se usa c/12,92 y, en otro caso, ((c+0,055)/1,055)^2,4. L = 0,2126 R + 0,7152 G + 0,0722 B. Relación = (L mayor + 0,05)/(L menor + 0,05). Valores mostrados redondeados a cuatro decimales; los umbrales se comparan sin redondear.

Como criterio de aceptación del proyecto, todo texto activo revisado deberá alcanzar 4,5:1; los límites e indicadores necesarios para reconocer controles o estados, 3:1. WCAG permite 3:1 para texto grande; aquí se conserva 4,5:1 como objetivo para el texto. Fuentes: [W3C, contraste de texto](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) y [W3C, contraste no textual](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html), consultadas el 08-11-2026.

| Uso / primer color | Fondo / segundo color | Relación |
|---|---|---:|
| Texto `#0b1f33` | Blanco `#ffffff` | 16,6928:1 |
| Texto `#0b1f33` | Página `#f2f5f8` | 15,2555:1 |
| Texto secundario `#2f4255` | Blanco | 10,3381:1 |
| Texto secundario `#2f4255` | Página | 9,4479:1 |
| Enlace `#0b4f9c` | Blanco | 8,0377:1 |
| Blanco | Botón principal `#0b4f9c` | 8,0377:1 |
| Blanco | Cabecera / botón en hover `#073a73` | 11,2793:1 |
| Botón secundario `#073a73` | Hover `#e6f0fb` | 9,7870:1 |
| Éxito `#0f5c2e` | `#e3f4e8` | 7,0916:1 |
| Aviso `#6b4a00` | `#fff4d6` | 7,3573:1 |
| Error `#8a1414` | `#fde8e8` | 8,1633:1 |
| Información `#0b3d73` | `#e6f0fb` | 9,4447:1 |
| Texto `#0b1f33` | Fondos bajo / medio / alto | 14,6036 / 15,2328 / 14,2162:1 |
| Texto secundario `#2f4255` | Fondos bajo / medio / alto | 9,0442 / 9,4339 / 8,8043:1 |
| Borde de campo `#5a6b7d` | Blanco | 5,4774:1 |
| Borde MEDIO `#b37400` | Fondo de aviso / blanco | 3,5390 / 3,8782:1 |
| Contorno de foco `#0b1f33` | Halo amarillo `#ffbf00` | 10,0986:1 |
| Contorno de foco `#0b1f33` | Cabecera `#073a73` | 1,4799:1 |
| Halo amarillo `#ffbf00` | Cabecera `#073a73` | 6,8236:1 |

Los pares de texto y bordes revisados superan sus objetivos. El contorno oscuro por sí solo tiene poco contraste sobre la cabecera, pero el foco también declara un halo amarillo con mayor contraste: **revisar en navegador su visibilidad completa y que no quede recortado**. En colores forzados el CSS sustituye el foco por `Highlight` y elimina el halo; esa variante requiere comprobación propia. Estos cálculos no certifican conformidad WCAG ni cierran R-43/R-58.

## Siguiente trabajo concreto y criterios de aceptación

**Trabajo:** ejecutar el flujo local completo con teclado y zoom, revisar los anuncios con lector de pantalla y comprobar consola/cabeceras reales. Registrar resultado por fila; no marcar una prueba como correcta por inspección del código.

Preparación: usar `.venv` existente; `AI_ENABLED=0`, `AI_BUDGET_USD=0`, `AI_ALLOW_OPUS=0`, `ANTIFRAUDE_PRUEBAS_REALES=0` y `ANTIFRAUDE_PRUEBAS_REALES_GMAIL=0`; retirar del proceso `ANTHROPIC_API_KEY` y `CLAUDE_MODEL`. No cargar `.env`. Para ejemplos sintéticos, `APP_DEMO_MODE=1`, manteniendo visible su etiqueta. Arrancar desde `backend` con `..\.venv\Scripts\python.exe -m antifraude`; utilizar únicamente `http://127.0.0.1:8790/`. No abrir enlaces del contenido, resolverlos ni seguir redirecciones. No registrar códigos de emparejamiento, cookies ni tokens CSRF en el informe.

| Paso | Criterio observable de aceptación | Estado inicial |
|---|---|---|
| Bienvenida y salto | Tab muestra el enlace de salto; Enter lleva al contenido; foco visible y orden comprensible | Pendiente |
| Emparejamiento | Etiqueta/ayuda legibles; código incorrecto informa del error y permite corregirlo; código válido abre el panel | Pendiente |
| Panel con teclado | Tab/Shift+Tab recorren controles sin trampas; Enter/Espacio activan botones y desplegables; foco siempre localizable | Pendiente |
| Validación de análisis | Envío vacío anuncia el error y enfoca el texto; corregir y reenviar permite analizar | Pendiente |
| Texto y archivo sintéticos | Texto y .eml se pueden seleccionar/enviar con teclado; resultado, citas y recomendaciones son legibles; archivo tiene prioridad si hay ambos | Pendiente |
| Resultado dinámico | Se anuncia la espera y el resultado sin duplicaciones molestas; foco llega al título; se pueden explorar explicación e historial | Pendiente |
| Zoom 200 % | Registrar tamaño de ventana y zoom del navegador; completar el flujo sin solapamientos, controles cortados ni pérdida de contenido o funcionalidad | Pendiente |
| Reflujo estrecho | Repetir a 320 px CSS de ancho; mensajes largos, selector de archivo y NO CONCLUYENTE no obligan a desplazamiento horizontal de la página | Pendiente |
| Contraste visual | Confirmar los pares efectivos de texto/bordes/foco, hover y modo de alto contraste; registrar cualquier estado ausente de la tabla | Parcial: solo paleta CSS |
| Lector de pantalla | Registrar lector, versión y navegador; comprobar idioma español, encabezados, etiquetas, ayudas, errores, espera, resultado y cierre de sesión; iconos no duplican el significado | Pendiente |
| CSP y peticiones reales | Consola sin infracciones CSP del flujo; recursos/peticiones de la aplicación solo locales; POST con Origin y Sec-Fetch-Site admitidos; X-CSRF-Token presente en operaciones protegidas, sin copiar su valor | Pendiente |
| Cierre | Cerrar sesión con teclado devuelve al flujo de conexión; acceso posterior a /panel queda protegido | Pendiente |

Evidencia por prueba: fecha, versión de código, navegador/lector y versión, tamaño de ventana, zoom, pasos, resultado observado, aprobado/fallo y referencia a incidencia. Usar solo contenido sintético; evitar capturas con secretos o texto privado. La revisión humana de los 27 casos (R-47) y la evaluación independiente siguen separadas y pendientes.

Cierre de R-58/V-26: todas las filas verificadas en el entorno declarado, fallos corregidos y repetidos; R-43 requiere además confirmar los estados renderizados. Si cambia el comportamiento, fijar antes el caso reproducible y su resultado esperado, conservar controles de seguridad y añadir regresiones cuando corresponda. No se ha autorizado commit, push ni PR.


## Segunda revisión: navegador local y correcciones — 08-11-2026

Esta sección es el estado vigente; la primera revisión y su tabla se conservan como registro previo. Base: HEAD `71c5917` más cambios locales sin confirmar. Se conservaron los cinco documentos pendientes al inicio, incluidos `AGENTS.md` y el traspaso actualizado por otra sesión.

### Entorno y límites

- Navegador integrado de ChatGPT (IAB), sobre este ordenador Windows. La interfaz de control no expuso una versión del motor; no se atribuye la prueba a una versión concreta de Chrome/Edge ni a un lector de pantalla.
- Ventana inicial: **674 × 828 px CSS**. Reflujo adicional: **320 × 800 px CSS**. Se restableció el tamaño original al terminar.
- Servidor normal del proyecto con `.venv`, solo en `127.0.0.1:8790`, modo demostración etiquetado, IA desactivada, presupuesto cero y ambas integraciones reales bloqueadas; sin claves ni modelo en el proceso. Se cerraron la pestaña temporal y los servidores propios de prueba al terminar.
- Contenido manual sintético y ejemplo de demostración ya existente; sin enlaces abiertos, DNS, redirecciones sospechosas, instalación, APIs de pago ni acceso al conjunto sellado.
- La lectura del árbol de accesibilidad y de la región de estado **no sustituye escuchar un lector de pantalla**.

### Hallazgos corregidos

1. **A11Y-01 — espera que permanece tras un fallo.** Antes: al fallar un envío, se mostraba el error pero `#estado-sr` seguía diciendo «Analizando el mensaje, espere por favor». Reproducido inicialmente en un envío de archivo; confirmado después mediante desconexión deliberada del servidor propio. Ahora se cancela el anuncio diferido anterior y se limpia la espera en errores de transporte, timeout, HTTP y sesión caducada. El resultado definitivo también sustituye el anuncio pendiente de espera. Tras recargar el JS corregido, se repitió la desconexión real: error visible y región de estado vacía, también en la observación posterior.
2. **A11Y-02 — errores sin relación con el campo.** El campo de conexión tenía `aria-invalid=true` al fallar, pero su descripción solo referenciaba la ayuda. Ahora incluye `mensaje-emparejar`; se confirmó en el DOM tras repetir un código incorrecto. El selector de archivo también referencia `mensaje-analisis`, igual que el campo de texto. No se modifican límites de intentos, sesión, CSRF ni mensajes de riesgo.

Criterios fijados antes de corregir: un fallo cancela la espera sin que un temporizador la reponga; un resultado rápido solo deja el anuncio definitivo; los errores quedan relacionados con sus campos. No se han cambiado CSS, reglas, niveles de riesgo ni contratos.

### Resultados por criterio

| Criterio | Resultado observado | Estado vigente |
|---|---|---|
| Bienvenida y salto | Primer Tab enfoca el enlace de salto, visible en captura; Enter enfoca `#contenido`; siguiente Tab llega a Empezar | Comprobado en IAB |
| Emparejamiento | Código incorrecto informa, selecciona/enfoca el campo y lo marca inválido; descripción incluye el error tras corregir. Código correcto abre el panel. Se observó y respetó también el límite temporal 429 | Comprobado en IAB |
| Teclado en panel | Recorrido Tab: salto, marca, cerrar sesión, texto, archivo, Analizar y tres ejemplos. Shift+Tab vuelve al control anterior. Enter analiza; desde el título del resultado, Tab llega a Más detalles y Espacio lo abre | Comprobado para este recorrido; selector nativo completo pendiente |
| Envío vacío | Error visible, foco en texto y `aria-invalid=true`; escribir un texto permite analizar | Comprobado en IAB |
| Texto y .eml | Texto manual y ejemplo etiquetado producen resultado. El selector automatizado de .eml terminó en error de envío; causa sin confirmar. La importación por TestClient existente pasa, pero no demuestra el flujo de navegador ni la prioridad cuando hay texto y archivo | Parcial; .eml y prioridad pendientes |
| Resultado dinámico | Foco en `#t-resultado`, texto de estado con riesgo ALTO, explicación, recomendaciones e historial disponibles en el árbol; recuperación tras error verificada | Comprobado DOM/teclado; anuncios audibles pendientes |
| Zoom 200 % | Los atajos enviados al navegador integrado no cambiaron `innerWidth`/`innerHeight`; no se pudo acreditar zoom real. No se usa el cambio de viewport como sustituto | Pendiente |
| Reflujo 320 px | Panel y resultado ALTO: ancho de documento/clientWidth **305/305**, sin desplazamiento horizontal de página; se revisó también la explicación de los cuatro niveles, incluido NO CONCLUYENTE | Parcial: faltan otros resultados, nombres de archivo y zoom real |
| Selector de archivo estrecho | Botón Seleccionar archivo visible y enfocable, pero el control nativo mide scrollWidth **460** frente a clientWidth **212**; no se acreditó la lectura visual del nombre seleccionado | Pendiente de completar en navegador normal; sin corrección especulativa |
| Contraste y foco | Colores computados de conexión (marca, ayuda, campo, botones) coinciden con los de la tabla inicial; foco del campo y título de resultado visibles en capturas. Contorno/halo de cabecera comprobados por estilo computado | Parcial; faltan cobertura completa de estados y colores forzados |
| Lector de pantalla | Ningún lector se activó ni se escuchó | Pendiente |
| CSP y cabeceras reales | No aparecieron infracciones CSP en los registros de consola revisados. Hubo 401/429 deliberados de emparejamiento y errores de transporte esperados. Los POST protegidos de análisis/cierre funcionaron; no se capturaron ni inspeccionaron sus cabeceras reales | Parcial: inspección de Origin/Sec-Fetch-Site/X-CSRF-Token y tráfico completo pendiente |
| Cierre | Enter en Cerrar sesión vuelve a bienvenida; navegar después a /panel exige conectar y no muestra el panel | Comprobado en IAB |

La importación de archivo requiere repetir el flujo fuera de la automatización antes de atribuir el fallo al producto. La ausencia de infracciones CSP en los registros revisados no implica consola sin errores ni auditoría completa de tráfico. R-58/V-26/R-43/V-25 **siguen abiertos** por las verificaciones pendientes.

### Regresiones y evidencia

- Python: `python -B -m pytest -ra -p no:cacheprovider` con entorno seguro → **675 passed, 4 skipped, 1 xfailed, 1 warning** en 10,62 s. Una regresión nueva verifica los vínculos de error en el HTML renderizado. Se mantienen el xfail conocido y el aviso de Starlette/httpx.
- JavaScript: `node --test tests/ui/test_accesibilidad.cjs` → **9 correctas**. Node v24.15.0 ya estaba instalado; no se añade dependencia de ejecución a la aplicación ni se instala nada. Es una comprobación adicional manual, no incluida automáticamente en pytest.
- Esas nueve pruebas ejecutan `app.js` real en una VM con DOM y temporizadores simulados: no hacen red ni usan navegador. Antes de corregir fallaban ocho; después pasan todas. Cubren errores de transporte/timeout antes y después de anunciar la espera, error HTTP, sesión caducada y resultado rápido.
- Captura local del resultado sintético con foco, sin códigos/cookies/tokens: `C:/Users/dialm/.codex/visualizations/2026/11/08/01a1bcf3-fa41-7500-933c-cd1f3bc3c6ec/accesibilidad-resultado.png`. Artefacto local fuera del repositorio; no se publica.
- Sin commit, push ni PR. Siguiente comprobación: navegador de escritorio con zoom real 200 %, selector de .eml/nombre/prioridad, lector de pantalla y modos de alto contraste; después completar V-25 con inspección de cabeceras sin guardar valores secretos.


## Tercera revisión: misión de demo y comprobación manual del usuario

Estado vigente: **parcial; cierre obligatorio pendiente**. Se conservan las evidencias y los límites de las revisiones anteriores. No se ha realizado el rediseño visual definitivo ni se ha cambiado el CSS de la interfaz.

### Evidencia manual comunicada por el usuario

Fuente: respuesta del usuario en esta misión, 08-11-2026. Sin captura ni versiones comunicadas; se registra como confirmación humana, no como medición automatizada ni prueba propia del agente.

| Comprobación | Resultado comunicado | Alcance / pendiente |
|---|---|---|
| Bienvenida y acceso al panel | Funcionan | Confirmación manual |
| Formulario vacío | Error comprensible | Confirmación manual |
| Narrador ante error de formulario vacío | Anunció el error según la comprobación realizada | Confirmado solo este anuncio; versión de Narrador sin registrar |
| Ejemplo sintético 2 | RIESGO ALTO; aviso preventivo, explicación, recomendaciones y limitaciones visibles | Confirmación manual |
| Zoom real del navegador al 200 % | Texto legible; botones visibles y utilizables; desplazamiento vertical; sin barra horizontal | Confirmado en las páginas/escenario revisados; tamaño de ventana y versión de navegador sin registrar; no extender automáticamente a todos los archivos/resultados |
| Anuncios «Analizando» y «Riesgo ALTO» | El usuario no puede escuchar audio ahora | **Pendientes**; el texto en el DOM no acredita su anuncio audible |
| Recorrido completo por teclado | No verificado por el usuario | **Pendiente**; se conserva el recorrido parcial de IAB previo |
| Consola CSP y cabeceras reales del navegador | No comprobadas por el usuario | **Pendientes**; solo registros IAB parciales y pruebas HTTP propias disponibles |
| Lector completo y registro de versiones | No completados | **Pendientes** |
| Contraste elevado de Windows | No probado | **Pendiente**; no confundir con la paleta CSS medida |

El control nativo de Brave se detuvo porque la herramienta no pudo determinar la URL con confianza suficiente. No se sorteó ese bloqueo ni se cambió a otra automatización de navegador. Se solicitó la comprobación manual y se continuó con trabajos independientes.

### Evidencia automática nueva y límites

- `tests/test_demo_http_local.py`: cinco pruebas contra Uvicorn **real en loopback**, sin TestClient; importación de cuatro .eml sintéticos, prioridad del archivo frente al texto, validaciones, historial, CSRF/Origin y cierre protegido. Resultados: BAJO, ALTO, ALTO y NO CONCLUYENTE. Las cabeceras de autenticación del correo son **simuladas**.
- La solicitud HTTP sintética usa Origin/Sec-Fetch-Site/CSRF generados en el cliente de prueba. Esto no demuestra qué cabeceras emitió el navegador: **V-25 sigue abierto**.
- Arranque CLI desde copia temporal e instalación nueva: cuatro archivos, desconexión detectada por cliente HTTP y recuperación con reinicio/nuevo emparejamiento. Sin códigos ni tokens guardados en el informe.
- Suites actuales: **709 passed, 4 skipped, 1 xfailed, 1 warning** (Python); **9 JS correctas** con DOM/temporizadores simulados. Sin llamadas de IA ni integraciones reales.
- Reflujo 320 px: no se amplía la evidencia previa; siguen pendientes los demás resultados/archivos y todo el recorrido relevante. La prueba HTTP no renderiza.

### Mínima comprobación manual restante

Cuando pueda escucharse audio, registrar navegador/versión, Narrador/versión, tamaño de ventana y zoom. Recorrer conexión, ayudas y errores; analizar el ejemplo 2 y confirmar los anuncios de espera/resultado y el foco; cerrar sesión y escuchar la transición. Repetir el recorrido con Tab/Shift+Tab/Enter/Espacio y el selector .eml (01–04 de `docs/entrega/ejemplos/`), incluyendo error de archivo y recuperación.

Completar reflujo a 320 px en los cuatro resultados y archivo seleccionado; probar tema de contraste de Windows con foco visible. En herramientas del navegador, verificar consola CSP y las cabeceras de las peticiones protegidas: registrar solo presencia/validez, **nunca valores de cookies, códigos ni tokens**. No repetir como pendiente lo ya confirmado, salvo que un cambio posterior lo afecte.

Hasta disponer de esta evidencia, R-58/V-26/R-43/V-25 y el criterio de accesibilidad de la meta permanecen abiertos. No se declara conformidad WCAG general.


## Cuarta revisión: archivos, teclado, reflujo y cabeceras reales en IAB

La meta sigue abierta. Se completaron comprobaciones automatizadas adicionales sobre **la aplicación real** con el navegador integrado (IAB), viewport explícito de **320 × 800 px CSS**. Esta evidencia no sustituye Narrador audible, el tema de contraste de Windows ni el diálogo nativo manejado enteramente a mano.

### Defectos corregidos y comprobados

- **A11Y-03: nombre del archivo oculto.** El selector nativo tenía más contenido que ancho visible. Se importaba el correo pero no se veía su nombre. Se añadió un texto asociado mediante aria-describedby que muestra el nombre completo con textContent y permite ajustarlo al ancho. Se comprobó un nombre sintético de más de cien caracteres: clientWidth/scrollWidth del texto **217/217**, sin truncar ni desbordar. Una prueba JS usa además un nombre con apariencia de HTML y verifica que permanece texto literal; otra comprueba retirar la selección. Esa retirada se simula en la prueba JS: la API del selector del navegador no admite setFiles([]), por lo que no se presenta como prueba nativa superada.
- **A11Y-04: etiqueta NO CONCLUYENTE partida dentro de la palabra.** Se reprodujo a 320 px. El relleno de la alerta y el espaciado adicional dejaban poco sitio al texto. Se ajustaron solo en ventanas estrechas, conservando **24,3 px** de fuente. Tras recargar, NO y CONCLUYENTE ocupan dos líneas completas; antes el nombre ocupaba tres. No se hizo el rediseño visual definitivo.

### Matriz de evidencia nueva

| Comprobación | Resultado observado | Alcance |
|---|---|---|
| .eml en navegador | 01: BAJO; 02: ALTO; 03: ALTO; 04: NO CONCLUYENTE. Nombre seleccionado visible; foco en t-resultado y texto final correcto en estado-sr | IAB real, apertura del selector con Enter; selección por API de filechooser, no navegación manual del diálogo nativo |
| Prioridad del archivo | Correo 01 seleccionado más texto de contraste que pide contraseña: resultado BAJO correspondiente al archivo | Comprobado en navegador; datos sintéticos |
| Extensión no admitida | .txt sintético devuelve 400, error comprensible, descripción del control vinculada al mensaje y estado-sr vacío | Comprobado. Recuperación mediante recarga y análisis de texto R-64: MEDIO. No se afirma retirada nativa del archivo |
| Reflujo | Documento/clientWidth **305/305** a viewport 320: bienvenida, emparejamiento, panel, validaciones, cuatro .eml, nombre largo, guía de niveles y resultados BAJO/MEDIO/ALTO/NO CONCLUYENTE | Resultado NO CONCLUYENTE revisado visualmente tras el ajuste; BAJO y ambos fraudes repetidos también con CSS final |
| Teclado y foco | Tab/Shift+Tab recorren marca, cierre, texto, archivo, Analizar, tres ejemplos y Más detalles; Espacio abre y Enter cierra el desplegable; contorno computado de 4 px; halo de cabecera visible en captura | Automatizado con teclas reales de la pestaña. Se conserva pendiente la verificación manual completa con lector y diálogo nativo |
| Bienvenida y conexión estrechas | Salto al contenido con Tab/Enter; Empezar; código caducado/usado informa y devuelve foco a código; ayuda se abre con Espacio y Tab alcanza Pedir código nuevo | Comprobado a 320 px. No se ejecutó regenerar código en esta comprobación |
| Cabeceras del navegador | Origin coincide con la instancia local; Sec-Fetch-Site es same-origin; CSRF presente en análisis, ejemplos y cierre; no requerido en pairing; CSP de respuesta coincide con la política existente | **V-25 comprobado en las operaciones IAB ensayadas**, no inferido de un cliente HTTP sintético |
| Consola | Sin infracciones CSP en el recorrido. Registra solo los 400/401 deliberados de archivo y código | No se dice «consola sin errores» ni se certifica todo navegador/version |
| Cierre y protección | Enter en Cerrar sesión vuelve a bienvenida; /panel exige conectar otra vez | Comprobado; pestaña propia cerrada y viewport restablecido |

Para observar las cabeceras se usó un envoltorio ASGI temporal fuera del repositorio que conserva la aplicación y su seguridad intactas. Solo emite ruta de prueba, estado, validación de Origin, enum Sec-Fetch-Site y booleanos de presencia de CSRF/CSP. No registra cuerpos, códigos, cookies ni valores de tokens. Se observaron pairing, análisis, ejemplos y logout; la instancia propia de loopback 8791 se detuvo al terminar.

Evidencia local fuera del repositorio: `.mvp-build/browser-320-casos-final.json` (niveles, geometría y recorrido de foco), `browser-headers-audit.json` (13 respuestas de la última lectura; las dos respuestas iniciales pairing 204 y análisis 200 se observaron antes), y capturas `archivo-largo-320.png` / `no-concluyente-320.png` en la carpeta de visualizaciones de este chat. Solo contenido sintético, sin credenciales.

### Lo que aún impide cerrar la accesibilidad

- Narrador completo: versiones, etiquetas/ayudas, anuncios audibles de espera y resultado, nombre seleccionado, errores y cierre. El usuario ya confirmó el anuncio del error vacío; no se vuelve a presentar como pendiente.
- Tema real de contraste elevado de Windows y foco. No se activó ni se sustituyó por emulación.
- Verificación manual completa de teclado/diálogo .eml y ampliación de la confirmación humana de zoom 200 % a los cambios de espaciado recientes, cuando afecten a su viewport. La confirmación previa se conserva como tal.
- Versiones de navegador/Narrador y condiciones de ventana en el registro manual.

No se declara conformidad WCAG general. R-58/V-26/R-43 siguen abiertos; V-25 y la consola CSP tienen evidencia acotada a IAB. Suites tras la corrección: **710 passed, 4 skipped, 1 xfailed, 1 warning** (Python) y **11 JS correctas**; dos regresiones JS y una Python nuevas, sin skips nuevos ni cambios de proveedor.


### Inventario local y revalidación de la cuarta revisión
- Lectura de metadatos, sin lanzar apps ni activar Narrador: `C:/Windows/System32/Narrator.exe` → ProductVersion **10.0.26100.9949**; ejecutable de Brave instalado → ProductVersion **157.1.99.55**. Son las versiones instaladas observadas ahora, no confirmación de cuáles se usaron en la comprobación humana. IAB no expuso su versión de motor mediante las interfaces utilizadas.
- Copia actual `clean-fuente-2` (162 archivos, sin .git ni .venv copiados), mismo entorno limpio previamente autorizado: **710 passed, 4 skipped, 1 xfailed, 1 warning** en 13,25 s y **11 JS correctas**. Arranque CLI, cuatro .eml, protección del cierre, desconexión y recuperación tras reinicio correctos con el intérprete nuevo. Sin nuevas instalaciones.
- Desde esa validación solo se ajusta la documentación de evidencia; no se modifican código ni pruebas. Los materiales mantienen las cifras 710/11 y accesibilidad parcial. Se han solicitado comprobaciones manuales concretas de anuncios, nombre seleccionado/cierre, teclado nativo y contraste elevado. No se presupone su resultado.


## Decisión del usuario: accesibilidad diferida a fase final
- No implementar lectura de pantalla propia, voz ni reproducción de audio. Se conserva compatibilidad básica con lectores mediante HTML semántico, etiquetas y atributos accesibles.
- No dedicar más tiempo por ahora a Narrador ni solicitar pruebas manuales de accesibilidad. Los anuncios auditivos pendientes, el tema de contraste elevado y el recorrido manual completo siguen **no verificados**, no superados.
- Simplificación visual y diseño definitivo reservados para la etapa final. La validación completa de accesibilidad/usabilidad se retomará antes de presentar el proyecto.
- Estas comprobaciones **no bloquean el trabajo técnico autorizado actual**. Prioridad: detector, fiabilidad, seguridad y preparación de integraciones. Esto no autoriza APIs de pago, claves reales, OAuth real, SDK nuevos, cambiar proveedor ni publicación; continúan las restricciones existentes.

## Revisión del diseño final — 09-11-2026

Posteriormente el prompt maestro autorizó ejecutar el diseño final tras estabilizar los flujos. En IAB se verificaron bienvenida, emparejamiento, envío vacío con foco en texto, cuatro .eml sintéticos (BAJO/ALTO/ALTO/NO CONCLUYENTE), prioridad del archivo, extensión no admitida con 400 explicado y sin espera residual, y resultado MEDIO por descarga ejecutable. A viewport 320×800 CSS: documento clientWidth/scrollWidth 305/305 en los cuatro niveles. Tab alcanza Más detalles y Enter lo abre; contorno de foco de 4 px. Cierre vuelve a bienvenida y /panel exige conectar. Consola: solo el 400 deliberado; sin infracciones CSP observadas.

Gmail simulado se verificó aparte en IAB: etiqueta explícita, consentimiento obligatorio, alerta ALTO explicada, contador de ALTO, actualización sin perder foco/desplegable cuando no cambia el estado, reflujo 305/305, desconexión y cierre. Son servicios falsos inyectados, no Google real. Servidores y pestañas propios de las pruebas funcionales detenidos/cerrados.

El zoom real 200 % fue confirmado por el usuario **antes del diseño final** y no se revalidó ahora; no ampliarlo automáticamente. Narrador audible, tema Windows de contraste y recorrido manual completo siguen no verificados y diferidos; no bloquean las otras tareas autorizadas. No se declara conformidad WCAG ni se solicita una nueva prueba manual en esta etapa.

## Revisión acotada de candidata Council — 10-11-2026
Interfaz conservada, cambio del detector rules-0.3.6; detalle vigente en DECISION_VERSION_FINAL.md. IAB: pairing, contraseña partida MEDIO, referencia sensible NO CONCLUYENTE, consejo BAJO, Bizum MEDIO con recomendación de no pagar, ejemplo 2 ALTO y cierre. Viewport 320×800 CSS: clientWidth/scrollWidth 305/305 en los estados inspeccionados; Tab/Enter abre detalles, foco de 4 px; consola sin errores/avisos observados en el recorrido. Pestaña propia cerrada y viewport restaurado. Fuente final repetida mediante HTTP: dos negaciones de formato nuevas y casos anteriores; no se atribuyen a verificación manual en navegador.

Las 11 pruebas JS pasan y los controles HTML/ARIA existentes permanecen. Cabeceras y rechazos Host/Origin/CSRF comprobados con cliente HTTP real de loopback; esta revisión no captura cabeceras del tráfico IAB. Narrador audible, tema de contraste elevado Windows, teclado manual completo y zoom real 200 % del diseño final siguen NO VERIFICADOS. La confirmación humana de la versión anterior se conserva con su alcance. Sin conformidad WCAG declarada ni audio propio; no se pide otra intervención manual ahora.

### Reflujo final de bienvenida
Corregido un desbordamiento común previo a ambas ramas: se agrupa texto/negrita en una sola unidad flex y se separan palabras cuando los br se ocultan en móvil. Sin rediseño ni cambio CSS. IAB a320×800 CSS, tras recargar: documento305/305; lectura visual de la frase y orden semántico correctos. Captura bienvenida-corregida-320.png fuera del repositorio. Instancia propia detenida, pestaña cerrada y viewport restaurado. Siguen pendientes las comprobaciones humanas anteriores.
