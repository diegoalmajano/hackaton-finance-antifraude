# Decisión de candidata — LLM Council, 10-11-2026

> Estado vigente: rules-0.3.9, reparación local tras revisión técnica. Matriz: 104 focalizadas; resultados finales y paquete en «Estabilización 0.3.9» al final. Las conclusiones anteriores son históricas. Sin commit ni publicación.

> Estado histórico: reparación rules-0.3.7, 951 Python / 11 JS / 8 SDK simuladas. Los apartados de la primera candidata (937 pruebas, rules-0.3.6) son históricos y su recomendación de publicación quedó bloqueada por la revisión posterior. Véase «Reparación tras revisión» al final. Sin commit ni publicación.

**Recomendación: combinación (C), implementada y validada técnicamente en copia limpia.** Candidata técnica; no entrega final validada ni enviada. No commits ni publicación autorizados en esta misión.

## Evidencia actual y procedencia
Equipo A: c013f5b77e1703d202a9356237bb78bd62fb8b53. Cierre B: 615b4a9b924722fc191bcc04535ee63fc95829b4. Ambos contrastados con el remoto al inicio. Ancestro común=A; A no tiene commits exclusivos. B añade 33099d7 y 615b4a9; se compararon 26 archivos distintos. No hay conflictos textuales de historia divergente. El conflicto es funcional: normalización por párrafos frente a detección de credenciales fragmentadas.

Suites reejecutadas en fuentes aisladas y mismo entorno ya instalado: A: 899 passed / 4 skipped / 1 xfail / 1 warning (23,42s), B: 926 passed / 4 skipped / 1 xfail / 1 warning (23,78s). Prueba de correo de 5 MiB < 3 s correcta en ambas ahora. No se presupone superioridad por contador, nombre o fecha.

Reproducción decisiva: «Introduzca\n\nsu contraseña.» y «Envíame\n\nel código de verificación.» dan MEDIO con señales en A, BAJO sin señales en B. A conserva consejo Bizum incompleto y falsa alarma del consejo «no debes aceptar»; la referencia sensible queda BAJO sin escalar. B mejora esos tres puntos. Los controles cotidianos y peticiones con un salto simple son comparables.

## Council real y alcance
Cinco asesores nuevos e independientes: crítico, primeros principios, expansionista, mirada externa y ejecutor. Después cinco revisores nuevos con respuestas A–E anonimizadas mediante una permutación aleatoria única, sin revelar roles ni opiniones previas. Coordinador como presidente. Contextos del mismo modelo heredado de Codex; no cinco modelos/proveedores ni evaluación experimental independiente. Sin API externa de modelos, claves o gasto de la aplicación.

Todos leyeron el mismo expediente, no el código directamente. Sus conclusiones son recomendaciones sobre evidencia recogida por el coordinador. El expediente, respuestas y revisiones se conservan en active/council-transcript-2026-11-10.md. La coincidencia no se trata como una prueba adicional de seguridad.

## Veredicto del presidente
### Acuerdos del Council
Conservar las mejoras verificables de Bizum y revisión contextual, bloquear B intacta por la regresión reproducida y exigir pruebas de variantes y de legítimos. Una suite verde no compensa un falso negativo conocido.
### Desacuerdos del Council
Hay distintos énfasis en comprensión, equivalencia de normalización y rapidez de integración. Cuatro respuestas proponen A como respaldo si C falla; ese respaldo no se acepta automáticamente: A también tiene omisiones conocidas. Si ninguna candidata satisface los controles mínimos, se comunica el bloqueo y no se declara lista.
### Puntos ciegos detectados
La demo y el consenso no sustituyen suite ni comprensión humana. Invocar un espía no demuestra que Claude analice bien. Debe comprobarse qué nivel, motivo y acción aparecen con IA apagada. La congelación debe dejar margen antes del 11 nov, 23:59 Madrid. Formulario rellenado no demuestra envío.
### Recomendación
Seleccionar C: preservar la base del equipo y las correcciones de B, recuperando detección de peticiones sensibles entre párrafos sin unir instrucciones y objetos ajenos. No restaurar sin más el plegado global antiguo: una regresión de B exige que «Envíe el formulario del club\n\nLa contraseña de la sala…» permanezca BAJO. El mecanismo elegido une solo una continuación gramatical directa de verbo/determinante y objeto sensible, o una negación directa con esa petición sensible; Bizum y referencias contextuales mantienen su vista limitada por párrafos. Es una corrección acotada, no comprensión semántica general.
### Primera acción
Reproducir el fallo de párrafos con variantes y controles legítimos antes de editar. Se añadieron nueve casos: seis fallaron y tres pasaron en B sin corregir. La decisión se implementa y se vuelve a medir antes de recomendar entrega.

## Selección concreta
| Origen | Conservar | Descartar o modificar | Dependencia y validación |
|---|---|---|---|
| Equipo A, ya incluido en B | App, reglas previas y Bizum original, flujo manual/.eml, UI, conectores, seguridad, contratos y locks | Sus consejos Bizum incompletos y falsa alarma no se restauran | Suite base, demo y controles de seguridad |
| Cierre B | Categoría/consejo de pago, negación por acción, disparador contextual, limpieza de espacios, 27 regresiones y preparación humana | Corte universal de párrafos que vuelve invisible una petición directa | Once nuevas regresiones de formato y controles, equivalencia y rendimiento |
| Cierre B, materiales | Diseño, estructura PPTX/PDF y explicaciones honestas de límites | Contadores/versiones y estados de publicación desactualizados | Fuentes y binarios regenerados, inspección visual y coherencia |

Sobre la base aislada B se modifica el mecanismo necesario de rules.py y se corrige el reflujo del HTML de bienvenida. No se copian archivos de otras sesiones ni se aplican commits indiscriminadamente. Contratos, dependencias, proveedor, conectores, CSS y controles de seguridad permanecen iguales. El único cambio adicional de interfaz agrupa el texto de las tres ventajas en spans y separa palabras alrededor de br ocultos en móvil.

## Puertas de aceptación y pendientes
Suite completa y JS; SDK Gmail simulado; mismos sondeos A/B/C; rendimiento5MiB bajo límite original; servidor real, pairing, .eml, legítimos/fraudes/ambiguos, errores/cierre/reinicio; casos visibles con IA apagada; cabeceras y revisión de accesibilidad de los estados afectados. Lector, zoom real y contraste humano solo se acreditan si se realizan; no se sustituyen por estática/emulación.

No hay cuentas, Gmail real, SDK Anthropic, gasto ni datos sellados autorizados. Métricas dev no son evaluación independiente; comprensión humana y accesibilidad completa siguen pendientes. Cierre confirmado por el usuario: 11-11-2026, 23:59 Madrid; duración y envío del formulario no confirmados.

Resultados de la candidata y localización de la huella del ZIP: bloque de cierre siguiente. Publicación futura requiere permiso explícito del commit/rama que se decida, descarga del ZIP oficial y ensayo de esa misma versión. No se autoriza ningún commit por esta recomendación.

## Comparación explícita de alternativas, por prioridad
| Criterio | A: equipo sin cambios | B: cierre sin cambios | C: selección y corrección |
|---|---|---|---|
| Seguridad y regresiones | Controles locales conservados; referencias sensibles no escalan y consejo Bizum incompleto | Mismos controles; petición sensible entre párrafos puede acabar en BAJO | Corrige esos casos conservando controles; no garantiza detección semántica universal |
| Flujo y explicación | Demo principal correcta; consejo legítimo Bizum da falsa alarma | Mejora consejo Bizum y referencias; negación fragmentada puede perderse | Mejoras B y once regresiones nuevas, con negaciones de formato conservadas |
| Reproducción | 899 Python actuales | 926 Python actuales | 937 Python desde extracción nueva; JS, SDK simulado y CLI correctos |
| Accesibilidad y errores | UI y controles comunes; validación humana parcial | UI idéntica; mismas limitaciones | UI conservada con corrección mínima de reflujo de bienvenida, revisada en IAB y HTTP; límites humanos explícitos |
| Materiales | Cifras y detector anteriores | Coherentes con .5, sin la corrección nueva | README, guion, JSON, PPTX y PDF reconciliados con .6/937 |
| Esfuerzo y plazo | Bajo esfuerzo, deja omisiones conocidas | Bajo esfuerzo, deja regresión conocida | Cambio del detector acotado a rules.py y ajuste del HTML de bienvenida; once casos añadidos, sin dependencias ni arquitectura nueva |

No se elige por suma de puntuaciones ni por mayoría. A y B intactas quedan descartadas por los casos reproducidos. B ya contiene A: no hay código exclusivo del equipo que importar ni dos historiales que fusionar. «Combinación» significa conservar esa base común, las mejoras justificadas de B y recuperar la detección de formato de A con límites que evitan asociar párrafos ajenos.

## Implementación y validación final, 10-11-2026
Reglas rules-0.3.6. Once pruebas nuevas: las seis peticiones fallaron antes de la primera corrección; tres controles pasaban. Después se reprodujeron dos falsas alarmas de negación antes del verbo («No\n\nintroduzca su contraseña» y «Nunca\n\nenvíes el código de verificación»), se añadieron y se corrigieron. Los once casos pasan; no se eliminan ni cambian etiquetas, pruebas anteriores o límites de rendimiento.

| Verificación ejecutada | Resultado y alcance |
|---|---|
| Python, extracción final fuente-congelada | **937 passed, 4 skipped, 1 xfailed, 1 warning, 26,14 s**. Saltadas: tres Claude real y una Gmail real, todas bloqueadas. Xfail «facilítesela» y aviso Starlette/httpx conservados |
| JavaScript | **11/11**, sin skips |
| SDK Gmail instalado previamente | **8/8**, OAuth, HTTP y keyring simulados, red/DNS/navegador vetados; sin cuenta ni credencial personal |
| Texto normalizado A/C | 1003 cadenas sintéticas, semilla 617003: salida y contador de invisibles idénticos. No prueba todos los Unicode ni eficacia antifraude |
| Rendimiento | Prueba existente del correo de 5 MiB correcta, conservando el límite <3 s |
| CLI desde copia extraída | Cuatro .eml: BAJO / ALTO / ALTO / NO CONCLUYENTE; tres ejemplos de panel: BAJO / ALTO / ALTO; texto del guion: ALTO |
| Texto y acción visibles por HTTP real | Bizum y doble negación MEDIO, con «No haga pagos»; consejo Bizum BAJO; referencia sensible NO CONCLUYENTE; contraseña/OTP entre párrafos MEDIO, con «No facilite contraseñas»; dos negaciones fragmentadas y párrafos ajenos BAJO |
| Errores y recuperación | Vacío y extensión inválida 400, luego análisis correcto. Host ajeno 400, Origin ajeno y CSRF ausente 403. Cierre 204 y sesión 401; proceso detenido, desconexión detectada, reinicio y nuevo pairing correctos |
| Cabeceras sobre HTTP de loopback | CSP con script/style propios y frame-ancestors none, nosniff y no-store comprobados. Controles de seguridad y contratos sin cambios |
| IAB, alcance acotado | Bienvenida, pairing, MEDIO de contraseña partida, NO CONCLUYENTE de referencia, BAJO del consejo y MEDIO Bizum con aviso de no pagar; ejemplo 2 ALTO y cierre. A 320×800 CSS, documento 305/305 sin desbordamiento en estados inspeccionados. Tab/Enter sobre detalles y foco de 4 px. Sin errores/avisos de consola observados en ese recorrido |
| Desarrollo sintético | 27/27 niveles aceptables, VP14/FP0/FN0/VN10, tres ambiguos aparte. **No evaluación independiente**, revisión humana pendiente; no se abrió ni creó conjunto sellado |
| Entregables | JSON y textos cotejados con las doce diapositivas; paquete, geometría y reimportación correctos. Diapositiva de cifras comparada con original y render final inspeccionado; repaso de contacto completo. PDF A4 de una cara, extracción y render final inspeccionados |

El IAB se ejecutó antes del último ajuste de negación; sus casos positivos y UI de resultados no cambian y se repitieron por HTTP en la fuente final. Las dos negaciones nuevas se verificaron por HTTP y suite, no se atribuyen a una prueba manual auditiva. IAB no aporta versión de motor confirmada. Se cerró la pestaña propia y se restauró el viewport. Las pruebas del CLI terminan sus procesos en finally.

La primera ejecución de suites en sandbox se interrumpió al no terminar; la repetición con loopback autorizado pasó. Un ensayo privado esperaba equivocadamente403 para Host ajeno; se cotejó la política existente y se corrigió a400 sin tocar el producto. Las extracciones ya usadas contienen cachés generadas; se creó una extracción nueva para la validación final, sin incluir esos cachés en el ZIP.

Se reutilizaron Python 3.12 y entornos existentes: **no es una instalación nueva desde cero** y no se instaló nada. AI_ENABLED=0, presupuesto 0, Opus 0, Gmail 0 y pruebas reales 0; clave/modelo retirados del entorno de ejecución. Proveedor sin cambio. No Claude Code/ECC/hooks ni API externa de modelos. El Council usa contextos de Codex de esta sesión; no se presenta como cinco proveedores independientes ni como servicio externo gratuito.

## Límites que siguen abiertos
- Pronombres como «facilítesela», ingeniería social implícita y asociaciones arbitrarias entre párrafos: la corrección cubre continuaciones directas, no comprensión general. BAJO no garantiza legitimidad.
- Comprensión humana de los niveles y revisión de los 27 casos; evaluación independiente sellada pendiente.
- Narrador audible, contraste elevado Windows, teclado manual completo y zoom real 200 % del diseño final **no verificados**. Se conserva el resultado humano anterior sin ampliarlo a esta versión; no se implementa audio ni se solicitan nuevas pruebas ahora.
- Gmail real/OAuth y Claude real/valor añadido sin verificar ni autorización; gasto 0. Directorio bancario parcial. Demostración principal manual y sintética.
- Duración oficial de presentación y envío del formulario sin confirmar. Fecha confirmada: 11-11-2026, 23:59 Europe/Madrid. Candidata técnica preparada; **no entrega final validada ni enviada**.

## Candidata, evidencia y publicación posterior
Carpeta aislada: C:/Users/dialm/Documents/ChatGPT/Hackaton/council-version-final-2026-11-10/repo. Rama local codex/candidata-council en 615b4a9, con cambios sin commit y sin índice preparado. Se conservaron ambas referencias remotas y los cambios originales AGENTS.md/.agents de la carpeta del escritorio.

El ZIP **CANDIDATO LOCAL** se genera de los archivos actuales seguidos y nuevos públicos de esta carpeta, incluyendo los cambios sin commit; no solo desde HEAD. 192 archivos, sin .git, entornos, cachés, temporales, claves, mensajes privados, skill local ni sellado. Se escanearon 283 unidades, incluidos XML de PPTX y texto/streams/metadatos de PDF: tres literales ficticios revisados, ningún hallazgo sin revisar; no es garantía absoluta para todo formato de secreto.

ZIP y SHA-256 quedan juntos en C:/Users/dialm/Documents/ChatGPT/Hackaton/council-version-final-2026-11-10/output/Antifraude_CANDIDATO_LOCAL_council_2026-11-10.zip y su archivo .sha256, fuera del repositorio. El manifiesto externo manifest-candidato.json registra cada archivo y la huella exacta. La huella no se incrusta dentro del propio ZIP para evitar autorreferencia. Evidencias reproducibles externas: validacion-limpia.json, cli-smoke-final.json, equivalencia-normalizacion.json y scan-candidato.json. El transcript completo del Council se incluye en active/council-transcript-2026-11-10.md. Tras documentar resultados solo cambian textos; se contrasta que código, tests, contratos, locks, HTML final, fuentes de entrega y binarios sean idénticos a la copia validada al volver a empaquetar.

Decisión exacta pendiente del usuario: **autorizar crear un commit con las rutas explícitas de esta candidata y subir únicamente codex/candidata-council** al repositorio indicado. Solo tras ese permiso se revisarán de nuevo remoto/diff, se publicará sin force y se descargará/ensayará el ZIP oficial de ese SHA. Integrar en feat/fase-0, crear PR, enviar el formulario o desplegar necesitan autorización propia; no se realizan como parte de esta misión. Antes de presentar siguen la revisión humana y las validaciones reservadas para esa fase.


### Corrección final de reflujo de bienvenida
La revisión visual de la captura detectó un desbordamiento previo común a A/B a 320 px: el texto con strong era un elemento flex separado y, al ocultar br por CSS, «responder,compruebe» quedaba unido. Se envolvió el texto de cada ventaja en span y se añadieron espacios junto a los dos br. No cambia contenido, diseño, CSS, scripts ni seguridad. IAB real, instancia propia 8795 con pairing no emitido: **clientWidth 305 / scrollWidth 305** tras recargar; frase y negrita juntas y encabezado separado en el árbol accesible. Captura externa bienvenida-corregida-320.png; pestaña cerrada y viewport restaurado. Se repitió la suite desde otra extracción de la fuente actual, incluyendo este HTML: 937 Python / 11 JS / 8 SDK simuladas, CLI y desarrollo correctos. Esto no sustituye zoom real ni contraste Windows.


## Reparación tras revisión — rules-0.3.7
Se conservó el árbol sucio completo: 16 archivos modificados y tres nuevos, rama codex/candidata-council, HEAD 615b4a9b924722fc191bcc04535ee63fc95829b4. Referencias remotas del equipo/cierre conservadas; candidata aún no publicada. Esta reparación no crea commits ni prepara el índice.

Antes del cambio se añadieron trece casos a los once existentes. Resultado: **8 fallaron y 16 pasaron**, incluidos los dos falsos BAJO reproducidos por la revisión: «Introduzca\n\npor favor su contraseña.» y «Envíame\n\npor favor el código de verificación.». Después: **24/24**. Se añaden peticiones con PIN/credenciales, verbo partido, contraseña partida, cortesía fragmentada, negaciones directas y Evite, y párrafos ajenos. No se elimina ni cambia ninguna expectativa anterior.

La vista de reglas reconstruye dos fragmentos de palabras separadas por saltos solo si forman un verbo de petición reconocido o una palabra sensible de una lista explícita. Después une whitespace dentro de la gramática verbo + «por favor» opcional + determinante opcional + objeto sensible. No admite objetos ajenos o puntuación intermedia. Se conserva la vista por párrafos para Bizum y referencias; la negación sigue pasando por el mecanismo existente. Mensaje original, minimización, citas literales, proveedor y contratos no cambian. No equivale a comprensión general: palabras con más fragmentos, conectores arbitrarios, pronombres y formulaciones no cubiertas pueden escapar. BAJO nunca garantiza legitimidad.

Suite completa del árbol reparado: **950 passed / 4 skipped / 1 xfailed / 1 warning**, 21,20s; JS11/11, SDK8/8 con transporte/OAuth/keyring simulados y red vetada. El límite original del correo de 5 MiB < 3 s pasa sin modificarlo. Saltos: tres Claude real y una Gmail real. Xfail «facilítesela» y aviso Starlette/httpx conservados. Las suites cubren también Bizum, referencias, citas y negaciones previas. Sin APIs, instalaciones ni claves reales; flags de IA/presupuesto/Opus/Gmail/integraciones reales a 0.

SHA histórico corregido únicamente por coincidencia exacta: 71c59178a9a20a8f55495d39399601c123c9357c, confirmado como commit en Git. Cuatro apariciones del identificador erróneo acabado en 9377c: dos en TRASPASO_CODEX.md y una en cada 09_PENDIENTES.md y 15_SEGUIMIENTO.md. No se alteraron otras cifras o fechas mediante sustitución de identificadores.

Materiales: fuentes de presentación/PDF, README, guion y cabeceras de seguimiento actualizados por cadenas de métricas, sin sustitución global de números en SHAs. PPTX y PDF se regeneran con runtime existente, sin instalar paquetes. Se conservan fuera del repositorio el ZIP y evidencias de la candidata anterior.

El nuevo paquete es **CANDIDATO LOCAL**, generado desde el árbol actual con cambios sin commit. Ruta externa: council-version-final-2026-11-10/reparacion-0.3.7/output/Antifraude_CANDIDATO_LOCAL_rules-0.3.7.zip. Su SHA exacto queda en el archivo .zip.sha256 y manifest-candidato.json, fuera del propio ZIP para evitar autorreferencia. El empaquetador existente coteja contenidos, exclusiones y escanea fuentes más XML PPTX y texto/streams PDF. Fuente extraída nueva para repetir validación; informes en reparacion-0.3.7/validacion-limpia.json y cli-smoke-final.json. No es ZIP oficial de GitHub.

Quedan pendientes revisión independiente de esta reparación, validación humana de casos, Narrador/contraste Windows/teclado completo/zoom real del diseño final, integraciones reales y confirmación del formulario. No se repiten ni se dan por superadas pruebas humanas. Estado técnico local, no entrega final validada. Próximo paso: revisar esta candidata y, solo después, decidir si se autoriza crear un commit y publicar exclusivamente su rama; merge/PR/formulario siguen separados.


### Cierre de la reparación: 951 pruebas
Se añadió un control adicional de solapamiento: «Introduzca su\n\ncontra\n\nseña.». El reconocimiento de pares mira también el siguiente par si el primero no es una palabra reconocida: «su/contra» no oculta «contra/seña». Catorce regresiones nuevas respecto a 937 y 25 casos de formato en total. Las cifras950 del primer ensayo de reparación se conservan como historia; el estado vigente es **951 Python / 11 JS / 8 SDK simuladas**, con 4 integraciones reales saltadas, 1 xfail y 1 aviso. La nueva extracción fuente-951 contiene el código final y todos los cambios sin commit; su validación completa y el ensayo CLI quedan en los informes externos de reparación. Los dos casos originales dan MEDIO con recomendación de no compartir, y Evite con cortesía da BAJO, también por HTTP real de loopback. Sigue sin afirmarse cobertura universal ni validación humana/real. Dictamen técnico tras esta validación: lista para una revisión independiente; publicación no autorizada.


Validación observada de fuente-951: **951 passed, 4 skipped, 1 xfailed, 1 warning en22,12s**, **11 JS** y **8 SDK simuladas** correctas. CLI desde esa copia: cuatro .eml, tres ejemplos, ambas frases con cortesía MEDIO y recomendación de no compartir, verbo fragmentado MEDIO, Evite con cortesía BAJO, Bizum y doble negación, referencia sensible NO CONCLUYENTE, párrafos ajenos BAJO, errores400, rechazos Host400/Origin-CSRF403, cierre204/sesión401 y recuperación tras reinicio correctos. Desarrollo27/27 niveles aceptables, sin evaluación independiente ni sellado. PDF A4 una cara y PPTX12 diapositivas regenerados, textos cotejados con fuentes y renders de cifras inspeccionados; no se afirma apertura en PowerPoint. Tras estas pruebas solo se completa documentación; el contenido restante se coteja con el manifiesto probado antes del empaquetado final. Paquete192 archivos, escaneo283 unidades con tres literales ficticios revisados, sin hallazgos sin resolver en ese alcance. Sin archivos ignorados ni secretos/temporales añadidos. La huella exacta queda en el manifiesto y sidecar externos.


## Reparación 0.3.8 — cuatro hallazgos de la revisión
Se verificó la candidata REAL en council-version-final-2026-11-10/repo; la ruta comunicada reparacion-0.3.7/repo no existe y solo era una referencia incorrecta. Rama codex/candidata-council, HEAD 615b4a9b924722fc191bcc04535ee63fc95829b4, 16 archivos modificados y tres nuevos sin preparar al comenzar. Se preservan cambios anteriores, HTML de bienvenida y transcript; sin tocar las ramas del equipo/cierre ni la carpeta original del escritorio.

Antes de editar la implementación se añadieron veinte casos. Focalizadas sobre 0.3.7: **12 fallaron y 33 pasaron**, incluidos los cuatro casos de la misión. Con 0.3.8 pasan **45/45**. Se mantienen sin cambios las expectativas anteriores; controles negativos añaden además ausencia de señales de petición de credenciales/OTP. Hay solicitudes en una línea, verbo partido, mayúsculas/acentos, coma/dos puntos, OTP, negaciones con/sin pronombres y salto simple/doble, y párrafos ajenos.

| Caso observado por AnalysisPipeline, IA desactivada | Equipo 0.3.4 | 0.3.6 | 0.3.7 | 0.3.8 |
|---|---|---|---|---|
| Introduzca: + párrafo + su contraseña | MEDIO | BAJO | BAJO | MEDIO y no compartir |
| Introduzca + párrafo + por favor, su contraseña | MEDIO | BAJO | BAJO | MEDIO y no compartir |
| No + párrafo + le envíe su contraseña | BAJO | MEDIO | MEDIO | BAJO, sin señal de petición |
| Mensaje para Te + párrafo + Cleopatra: nunca comparta su contraseña | BAJO | BAJO | MEDIO | BAJO, sin señal de petición |

No son cuatro regresiones nuevas: los tres primeros defectos ya existían en 0.3.6, pero no en la base del equipo; el cuarto apareció con la reconstrucción léxica 0.3.7. Se repitió esta comparación ahora, con datos sintéticos. Evidencia externa: reparacion-0.3.8/cuatro-casos-comparados.json.

Cambio mínimo en rules.py: la gramática de petición sensible admite coma o dos puntos opcionales de maquetación antes del objeto y junto a «por favor». No admite punto/punto y coma ni palabras intermedias arbitrarias. La unión de negación reconoce los mismos pronombres acotados del mecanismo existente antes del verbo; no aplana párrafos en general. La reparación de palabras usa un conjunto finito de alternativas literales del vocabulario existente más formas verbales explícitas: no aplica tecle\w* ni otras raíces abiertas como diccionario de reconstrucción. Las reglas generales no cambian su vocabulario, el motor no cambia y el mensaje original/citas no se reescriben. El falso verbo «tecleopatra» deja de reconstruirse.

Validación del árbol actual: **971 passed, 4 skipped, 1 xfailed, 1 warning en 25,86 s**, **11 JS** y **8 SDK simuladas** correctas. Los cuatro saltos siguen siendo tres Claude real y una Gmail real; xfail «facilítesela» y deprecación Starlette/httpx conservados. Pasan controles existentes de Bizum inverso, referencias sensibles, dobles negaciones cubiertas, citas y correo de 5 MiB bajo el límite original < 3 s. No se quitan pruebas ni se añaden skips/xfails. Se repite desde extracción del paquete antes de cerrar la reparación.

Límites residuales: no hay cobertura universal de gramática, palabras de más de dos fragmentos, conectores arbitrarios o pronombres referidos. La doble negación «No evite facilitar su contraseña» era BAJO en la base y 0.3.7 y sigue siendo una limitación preexistente fuera de esta reparación; no se presenta como corregida. Tampoco se promete eliminar todas las falsas alarmas léxicas/contextuales. La nueva revisión debe centrarse en esos límites además de los cuatro casos corregidos.

README, cabeceras activas de seguimiento y fuentes de PPTX/PDF se reconcilian con 0.3.8 y 971; cifras previas de 950/951 quedan como historia identificada. Materiales se regeneran con herramientas ya disponibles, sin instalar dependencias. Se cotejan textos y se inspeccionan renders. Se conserva el paquete 0.3.7 fuera del repositorio; no se sobrescribe.

El ZIP nuevo es CANDIDATO LOCAL: reparacion-0.3.8/output/Antifraude_CANDIDATO_LOCAL_rules-0.3.8.zip. Se genera con los archivos actuales, incluidos todos los cambios sin commit. Manifiesto externo y archivo.zip.sha256 registran su huella sin autorreferencia dentro del propio ZIP. Se comprueban igualdad con árbol, exclusiones y escaneo, y se valida extracción nueva. No es ZIP oficial de GitHub.

IA, presupuesto, Opus, Gmail e integraciones reales a 0; claves/modelo retirados de los procesos. Sin APIs de pago, credenciales reales, paquetes nuevos, Claude Code/ECC/hooks ni lectura del sellado. La revisión humana de casos, evaluación independiente, Narrador audible, contraste Windows, teclado completo y zoom real siguen pendientes, igual que Claude/Gmail reales y confirmación del formulario. Ninguna métrica de desarrollo se presenta como evaluación independiente. Dictamen acotado tras los criterios técnicos: lista para NUEVA revisión independiente, no para publicación automática ni entrega final validada.


### Evidencia de cierre 0.3.8
Primer ensayo de extracción nueva: **971 passed, 4 skipped, 1 xfailed, 1 warning en26,57s**, **11 JS** y **8 SDK simuladas** correctas; CLI real con los cuatro casos da MEDIO/MEDIO/BAJO/BAJO y recomendaciones correctas, sin claves ni cuentas reales. Cuatro .eml BAJO/ALTO/ALTO/NO CONCLUYENTE, errores, cabeceras Host/Origin/CSRF, cierre y reinicio correctos. Desarrollo27/27 niveles aceptables, solo dev, sin evaluación independiente. Después se añadió la comprobación explícita de alerta preventiva ausente a todos los controles negativos; focalizadas45/45 correctas. Se repiten suites y CLI desde la extracción del paquete final; sus resultados definitivos están en reparacion-0.3.8/validacion-limpia.json. Código del detector y binarios no cambian tras el primer ensayo; se coteja el resto del manifiesto.

PPTX12 diapositivas: textos cotejados con JSON, integridad/geometría y reimportación correctas; render de cifras comparado con la versión anterior. PDF A4 de una cara regenerado y render inspeccionado. No se afirma apertura en PowerPoint ni prueba humana. El paquete incluye192 archivos públicos, incluidos todos los cambios locales sin commit; escaneo283 unidades, tres literales ficticios revisados y ningún hallazgo sin revisar en ese alcance. Excluye secretos, .env, .claude, entornos, resultados y temporales; .env.example es una plantilla. No es garantía absoluta para cualquier secreto. La huella exacta queda junto al ZIP en el sidecar y manifest-candidato.json externos para evitar autorreferencia.

Diff revisado: la reparación afecta a rules.py, tests/test_j_council_version.py y documentación/materiales necesarios. Contratos, motor, proveedor, CSS, controles de seguridad y locks no cambian. Se conserva el HTML previo de bienvenida y el transcript anterior, además del resto del trabajo local. Índice vacío, sin commit/push/PR/merge/despliegue/formulario. Dictamen acotado: lista para nueva revisión independiente de los cuatro hallazgos corregidos; no aprobación de publicación y no cobertura universal.


### Matriz final completa: 973 pruebas
Se añadieron dos controles explícitos de negación sin pronombre con salto simple («No\nintroduzca su contraseña» y «Nunca\nenvíes el código de verificación»), además de los controles ya cubiertos con pronombres y párrafos en blanco. Son **22 casos añadidos respecto a0.3.7**, **47 focalizadas correctas**. No cambia el detector tras el primer ensayo0.3.8. Las cifras971 anteriores identifican ensayos intermedios reales, no el total actual.

Suite completa del árbol actual: **973 passed, 4 skipped, 1 xfailed, 1 warning en20,91s**, **11 JS** y **8 SDK simuladas** correctas. Se repiten desde el ZIP final en fuente-038-final; el registro definitivo está en reparacion-0.3.8/validacion-limpia.json. Los controles negativos exigen nivel BAJO, ausencia de señales de credenciales/OTP y ausencia de alerta preventiva. Los positivos exigen señal sensible, al menos MEDIO y rec.do_not_share. Los cuatro casos originales se comprobaron también con el servidor CLI de loopback, con MEDIO/MEDIO/BAJO/BAJO. Ninguna integración real ni API de pago activada; no hay claves reales ni dependencias instaladas.

README apunta ahora a esta decisión como estado vigente. Fuentes y binarios de presentación/PDF reflejan973; los apartados previos y sus tiempos se conservan como historia. Se cotejan fuentes, renders y paquete final y se preservan los cambios locales previos. El dictamen sigue siendo lista para nueva revisión independiente de esta reparación, no autorización de publicación ni afirmación de cobertura universal; siguen los límites residuales y comprobaciones humanas descritos arriba.


### Consolidación definitiva de la matriz 0.3.8: 978 pruebas
Al comprobar que el catálogo cerrado no perdiera flexiones válidas se añadieron cinco casos: positivos «Tecle\n\náis su contraseña», «Neces\n\nitaría su contraseña» y «Tec\n\nléeme su contraseña», y dos consejos negativos. Tres positivos fallaban en la reparación intermedia (3 fallos/49 correctas); esto no se ocultó ni se cambió su expectativa. Se corrigió ampliando el catálogo con una regla morfológica FINITA: terminaciones regulares explícitas de teclear/necesitar/comunicar y pronombres enclíticos enumerados. No se admiten sufijos arbitrarios de tipo \w*, y «tecleopatra» continúa rechazado. Es un lenguaje acotado, no comprensión general. No cambian las reglas generales, el motor ni el texto/citas del mensaje original.

Son **27 casos añadidos respecto a0.3.7**, **52 focalizadas correctas**, incluyendo los controles completos con/sin pronombre y salto simple/doble. El estado vigente es **978 Python / 11 JS / 8 SDK simuladas**, sin ocultar fallos ni modificar etiquetas. Los ensayos971/973 anteriores documentan pasos intermedios, no el total vigente.

Resultado completo observado del árbol final: 978 passed, 4 skipped, 1 xfailed, 1 warning in 21.24s. JavaScript11/11 y SDK8/8 simuladas correctas. Se valida a continuación la extracción final fuente-038-final978 y se registra su resultado en reparacion-0.3.8/validacion-limpia.json; su ZIP incluye el código final, pruebas y documentación vigentes. Los cuatro casos exigidos dan MEDIO/MEDIO/BAJO/BAJO, comprobados también por HTTP de loopback con las recomendaciones correspondientes. Los negativos exigen además ausencia de señal sensible y de alerta preventiva.

README, fuentes y binarios de entrega reflejan978 y esta decisión identifica la versión0.3.8. Manifiesto y sidecar externos se regeneran junto al ZIP candidato local y se cotejan con el árbol actual, sin agregar archivos al índice. Se conservan los artefactos0.3.7 y los cambios previos. Continúan los límites residuales descritos (incluido «No evite facilitar…», preexistente), los controles humanos pendientes y la prohibición de publicación. Dictamen acotado: lista para nueva revisión independiente de la reparación de los cuatro casos, no entrega final validada ni cobertura universal.


## Estabilización 0.3.9 — 10-11-2026

Repositorio real: `C:/Users/dialm/Documents/ChatGPT/Hackaton/council-version-final-2026-11-10/repo`, rama `codex/candidata-council`, HEAD `615b4a9b924722fc191bcc04535ee63fc95829b4`. Se conservaron los 16 archivos modificados y tres nuevos iniciales, sin preparar el índice. La reparación añade tests/test_k_normalizacion_sensible.py y actualiza limitaciones; no toca otros repositorios. El usuario aclara que es su repositorio personal; no se trabaja sobre el proyecto separado de compañeros.

Antes de cambiar reglas se ejecutaron 43 regresiones nuevas: 20 fallaron y 23 pasaron. Pipeline IA0: OTP fragmentado, número secreto fragmentado y «No evite facilitar su contraseña» daban BAJO/sin señal/sin no compartir/sin preventiva; «Documento firmado con\n\nfirma electrónica; nunca comparta su contraseña» daba MEDIO con petición de credenciales, no compartir y preventiva. Los dos primeros y la falsa unión son heredados de la reconstrucción por párrafos; la doble negación es anterior. Evidencia externa: reparacion-0.3.9/antes.jsonl y regresiones-antes.txt.

Se conserva la separación de párrafos para Bizum y referencias y se simplifica el puente gramatical: los objetos sensibles completos admiten whitespace interno, sin aplanar todo el mensaje. Dos puntos y comas solo se retiran al reconocer una petición sensible completa o su negación inmediata. Las peticiones sensibles españolas no atraviesan puntuación de cláusula; se conserva inglés y un complemento de destinatario acotado con cortesía. No se abre un regex de palabras arbitrarias. La reconstrucción léxica exige objeto sensible directo después del verbo reconstruido, catálogo finito y límites entre palabras completas; se permiten clíticos legítimos. «No evite/evita» inmediato invierte la interpretación de «Evite/evita» para esa petición. Se incorpora la forma explícita «enviarme». No cambian motor, contratos, proveedor, seguridad, minimización ni el mensaje original; normalización solo en la vista de reglas.

Revisión separada: un agente Codex de solo lectura, sin APIs externas ni Council nuevo; no auditoría externa. Encontró regresiones intermedias de inglés, destinatario y clíticos y dos defectos heredados con «con/firme» y «Evite:». Se corrigieron y añadieron controles, sin eliminar expectativas. La segunda pasada detectó cortesía antes de «al gestor»; ambas variantes se añadieron y pasan. Son 52 casos nuevos, 104 focalizadas junto a los 52 anteriores. Diez casos adversariales adicionales posteriores al diseño también pasan (adversarial.jsonl), sin convertirlos en evaluación independiente. El vocabulario Bizum implícito («acepta el Bizum que te mandé») es una limitación previa distinta; no se amplía aquí.

Resultados finales observados: 1030 Python / 11 JS / 8 SDK Gmail SIMULADAS. Las cuatro integraciones reales siguen saltadas; xfail del pronombre referido y aviso Starlette/httpx conservados. Se valida el ZIP final desde una extracción nueva y se registra salida completa en reparacion-0.3.9; la suite incluye Bizum, referencias, citas y el límite original del correo de 5 MiB <3s. No se cambian umbrales ni se añaden skips/xfails. HTTP CLI real de loopback prueba los cuatro hallazgos, cuatro correcciones0.3.8, consejos, ejemplos y archivos sintéticos, Host/Origin/CSRF, cierre y reinicio. No es Gmail ni Claude real.

Único candidato vigente: `reparacion-0.3.9/output/Antifraude_CANDIDATO_LOCAL_rules-0.3.9.zip`. Manifiesto `manifest-candidato.json` y `.zip.sha256` externos registran rutas, bytes y huellas; no se incluye la huella dentro del ZIP para evitar autorreferencia. Incluye árbol público actual con cambios sin commit, excluye ignorados, secretos, .env, configuración personal, cachés y temporales. Artefactos anteriores se conservan como historia, no son la candidata vigente. README y fuentes de presentación/PDF reflejan1030; binarios regenerados con runtime existente, cotejados y renders revisados, no apertura humana en PowerPoint.

Límites: lenguaje acotado; no comprensión universal, diccionario completo ni resolución de pronombres arbitrarios. La fragmentación en más de dos partes y complementos fuera del vocabulario pueden escapar. No se promete ausencia absoluta de falsas alarmas ni de falsos negativos. BAJO no garantiza legitimidad. Quedan revisión humana de27 casos dev, evaluación independiente sellada (no leída), accesibilidad manual final, integraciones reales, duración oficial y confirmación del formulario. Candidata técnica local, no entrega final validada. IA/presupuesto/Opus/Gmail/pruebas reales0, sin claves, instalaciones, APIs externas, commit, push, PR, fusión, despliegue ni envío.


### Cierre observado 0.3.9
Extracción nueva: **1030 passed,4 skipped,1 xfailed,1 warning en26,88s**; correo5MiB1,65s frente al umbral original<3s. JS11/11 y SDK Gmail8/8 simuladas correctas. HTTP CLI local completo correcto:28 escenarios, tres ejemplos, protecciones Host/Origin/CSRF, errores, cierre y reinicio. La ampliación del cliente alcanzó429; se conservó ese control del producto y se introdujeron pausas de61s en el ensayo, sin modificar servidor ni expectativas. El error de sintaxis intermedio fue del script externo de ensayo y quedó corregido antes del recorrido completo. Informe dev CLI ejecutado sin sellado; solo desarrollo. Evidencia completa externa en validacion-limpia.json y cli-smoke-final.json.

La revisión separada final comprobó9/9 casos de sus hallazgos con señales, acciones y preventiva coherentes. Son datos de revisión asistida de Codex, no Council nuevo ni auditoría externa. Tras la validación se completa solo esta nota documental; el paquete final se extrae de nuevo y se coteja byte a byte con el árbol y, salvo esta nota, con la extracción probada. Código, pruebas, materiales y configuración permanecen idénticos. Paquete193 archivos; escaneo284 unidades, tres literales ficticios identificados, ningún hallazgo sin revisar en ese alcance. No es garantía absoluta de ausencia de secretos. SHA exacto externo en manifiesto y sidecar.

Dictamen acotado: **reparación validada, candidata preparada para decidir su publicación**. La decisión de publicación corresponde al usuario y requiere autorización propia. No entrega final validada, no commit/push/PR/fusión/despliegue/formulario.
