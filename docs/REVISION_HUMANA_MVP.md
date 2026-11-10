# Revisión humana del MVP: hojas preparadas, resultados pendientes

Preparado el 10-11-2026. **No se han reclutado participantes, realizado revisiones humanas ni rellenado resultados en este documento.** Las filas vacías son una plantilla. Los 27 registros dev examinados conservan origen `synthetic_ai` y estado `pending_human_review`; revisar sus etiquetas no cambia su autoría ni los convierte en evaluación independiente.

Objetivo: comprobar por separado la coherencia de las etiquetas, la pertinencia de las señales/citas y si una persona entiende el nivel y la acción recomendada. Esta preparación no consulta ni crea ningún conjunto sellado y no autoriza APIs, cuentas reales, recopilación de mensajes privados ni publicación.

## 1. Preparación y consentimiento

Responsable/facilitador: __________. Revisores humanos R1/R2: __________ / __________. Adjudicador humano: __________. Son roles por asignar, no participantes ya confirmados. Usar códigos anónimos en los resultados; conservar cualquier identidad/consentimiento identificable fuera del repositorio bajo responsabilidad del organizador.

Antes de participar, explicar en lenguaje claro:

- Es una revisión voluntaria de un prototipo con mensajes ficticios; puede parar o no contestar, sin consecuencia.
- No se piden cuenta bancaria, claves, códigos, correos personales ni realizar pagos. No se abren enlaces de los ejemplos.
- Se anotarán respuestas sobre comprensión, tiempo, ayudas y errores; acordar con la persona qué se conserva, para qué, quién lo ve y cuándo se elimina. No grabar audio/vídeo/pantalla por defecto; cualquier grabación o publicación identificable requiere consentimiento propio.
- No se está midiendo inteligencia, salud ni capacidad de la persona. Los fallos sirven para mejorar el producto. No usar esta actividad para emitir conclusiones sobre la población mayor.

Registro previo, **a rellenar por una persona**: código anónimo __________; fecha __________; información explicada __________; consentimiento a participar sí/no __________; notas permitidas y plazo de conservación __________; retirada/interrupción __________. Si no hay consentimiento, no iniciar ni guardar respuestas. No marcar un sí por anticipado.

La sesión usa solo texto/archivos sintéticos del conjunto dev y la aplicación local con IA/presupuesto/Gmail/integraciones reales desactivados. El equipo elige quién revisa y cuándo; esta hoja **no solicita ahora pruebas manuales de Narrador, contraste elevado o recorrido completo de teclado**, que siguen diferidas por decisión del usuario. No incluye voz ni lectura automática.

## 2. Fijar la versión y separar las tres actividades

| Actividad | Quién y qué se muestra | Qué acredita |
|---|---|---|
| Etiquetado de desarrollo | R1/R2 revisan cada mensaje ficticio sin ver etiqueta existente, predicción o justificación del otro | Coherencia/revisión humana de dev; no generalización |
| Revisión de la salida | Tras guardar las etiquetas iniciales, revisores comparan señales, citas, nivel y acciones de esa versión | Errores o aciertos observados en esos casos conocidos |
| Comprensión del usuario | Persona consentida ve el resultado y responde con sus palabras, sin pistas del facilitador | Observaciones exploratorias de usabilidad; no eficacia antifraude independiente |

Registrar antes de comenzar: fecha __________; rama/commit __________; árbol limpio o cambios identificados __________; versión de reglas __________; configuración sin APIs __________; SO/navegador/ventana __________; orden de casos __________. Anotar si alguien conoce ya el código, las etiquetas o resultados: __________. Si no puede ser ciego, declararlo como revisión asistida, sin afirmar doble ciego.

Las fuentes del facilitador son [demo.jsonl](../eval/datasets/dev/demo.jsonl) y [casos_dev.jsonl](../eval/datasets/dev/casos_dev.jsonl). Esos archivos incluyen etiquetas y justificaciones: no entregarlos tal cual si se quiere preservar el etiquetado ciego.

El facilitador prepara para R1/R2 una vista del mensaje dev sin `expected`, `rationale_es`, señales esperadas ni salida del detector; no cambia los JSONL originales. Guardar primero las dos respuestas por separado. Los tres casos de demo no bastan para dar los 27 por revisados.

## 3. Criterios de etiquetado y revisión

Usar el [contrato EvalCase](../backend/antifraude/contracts/evaluation.py), ADR-0006/D-29 y la [metodología](../eval/METODOLOGIA_INDEPENDIENTE.md). Para cada caso, cada revisor registra:

1. Interpretación: legítimo / fraude / ambiguo, y qué información faltaría para decidir. No convertir falta de información en prueba de legitimidad.
2. Un nivel principal entre BAJO, MEDIO, ALTO y NO CONCLUYENTE; conjunto de niveles aceptables y motivo. BAJO no significa garantía; MEDIO indica precaución; ALTO exige evidencia grave suficientemente corroborada; NO CONCLUYENTE declara límites.
3. Evidencia concreta del mensaje y su procedencia: texto, remitente declarado o enlace pasivo. Una cabecera importada o un dominio parecido no son autenticación verificada. Indicar si la evidencia sustenta la conclusión o solo genera duda.
4. Acción segura que correspondería aconsejar y acciones que nunca deberían inducirse; comprobar especialmente peticiones de pago, credenciales y códigos. El usuario sigue decidiendo; no se ejecutan acciones bancarias.
5. Tras registrar lo anterior, comparar con la salida: nivel aceptable sí/no/no verificable; señal pertinente sí/no; incertidumbre declarada sí/no; recomendación segura y comprensible sí/no. Justificar cada discrepancia sin retocar el caso para favorecer al detector.

La etiqueta existente se conserva como referencia inicial. El consenso de esta hoja no modifica automáticamente datos, reglas ni `review_status`. Un responsable debe revisar y autorizar cualquier corrección posterior, preservando el rastro y explicando por qué; no cambiar etiquetas para obtener métricas verdes.

## 4. Hoja maestra de los 27 casos dev — en blanco

Cada celda remite a la ficha de caso de la sección siguiente. R1/R2 completan sus fichas sin compartir respuestas; el facilitador transcribe después. En «acuerdo» comparar el nivel principal inicial, antes del consenso. No usar la ausencia de respuesta como acuerdo.

| Caso | Ficha R1 | Ficha R2 | Acuerdo inicial | Consenso/adjudicación | Estado y fecha |
|---|---|---|---|---|---|
| dev-0001 |  |  |  |  |  |
| dev-0002 |  |  |  |  |  |
| dev-0003 |  |  |  |  |  |
| dev-0004 |  |  |  |  |  |
| dev-0005 |  |  |  |  |  |
| dev-0006 |  |  |  |  |  |
| dev-0007 |  |  |  |  |  |
| dev-0008 |  |  |  |  |  |
| dev-0009 |  |  |  |  |  |
| dev-0010 |  |  |  |  |  |
| dev-0011 |  |  |  |  |  |
| dev-0012 |  |  |  |  |  |
| dev-0013 |  |  |  |  |  |
| dev-0014 |  |  |  |  |  |
| dev-0015 |  |  |  |  |  |
| dev-0016 |  |  |  |  |  |
| dev-0017 |  |  |  |  |  |
| dev-0018 |  |  |  |  |  |
| dev-0019 |  |  |  |  |  |
| dev-0020 |  |  |  |  |  |
| dev-0021 |  |  |  |  |  |
| dev-0022 |  |  |  |  |  |
| dev-0023 |  |  |  |  |  |
| dev-0024 |  |  |  |  |  |
| dev-0025 |  |  |  |  |  |
| dev-0026 |  |  |  |  |  |
| dev-0027 |  |  |  |  |  |

Ficha de caso, copiar una por caso y revisor:

```text
ID dev: ____________________  Revisor anónimo: ______  Fecha: ______
¿Había visto antes etiquetas/código/resultados?: ____________________
Interpretación legítimo / fraude / ambiguo: ________________________
Nivel principal: __________  Niveles aceptables: ___________________
Evidencia literal o referencia concreta: __________________________
Información que falta / explicación de incertidumbre: _____________
Acción segura esperada: ___________________________________________
Justificación sin mirar la predicción: ____________________________

SOLO DESPUÉS de guardar la etiqueta inicial:
Nivel obtenido dentro de aceptables sí/no/no verificable: __________
Señales pertinentes y errores observados: _________________________
Cita mostrada literal/correcta, ausente o no verificable: ___________
Recomendación segura/comprensible, y defecto concreto: _____________
```

Ficha de desacuerdo/adjudicación, sin borrar respuestas anteriores:

```text
ID: ______  Diferencia entre R1 y R2: ______________________________
Evidencia y criterio discutidos: __________________________________
Adjudicador humano: ______  Decisión / queda abierto: _______________
Motivo y datos que siguen faltando: _______________________________
¿Afecta a etiqueta, explicación o detector?: _______________________
Fecha / responsable de revisar una eventual corrección: ___________
```

Informar cobertura: casos con ambas fichas / 27, desacuerdos iniciales, adjudicaciones y casos abiertos. Acuerdo simple = niveles principales iniciales iguales / pares completos. Si se informa kappa de Cohen, usar las cuatro categorías del nivel principal y frecuencias iniciales, no el consenso: `(acuerdo observado - acuerdo esperado)/(1 - acuerdo esperado)`. Sin pares completos o con denominador cero, indicar no calculable. No inventar un valor ni extrapolar a la población.

## 5. Comprensión: nivel, motivo, acción, tiempo y errores

La persona ve el resultado de un caso sintético; el facilitador no enseña la respuesta ni corrige durante el primer intento. Usar siempre estas preguntas:

- «¿Qué le dice este resultado sobre el riesgo del mensaje?»
- «¿Cuál es el motivo principal que ha entendido?»
- «¿Qué haría ahora y qué evitaría hacer?»

Evaluación previamente acordada por los revisores: nivel comprendido si distingue la conclusión de una garantía; motivo comprendido si identifica al menos una razón realmente mostrada; acción segura si coincide con las recomendaciones y no introduce una acción peligrosa. Una respuesta que contradice una alerta importante se registra como error crítico. No atribuir a la persona un error causado por la propia explicación incorrecta: anotarlo como defecto del producto.

Medir desde que el resultado está totalmente visible hasta que la persona expresa su acción. Separar ese tiempo de la latencia del detector. Anotar interrupciones, abandono y ayuda solicitada; no asignar cero segundos a una tarea incompleta. Cualquier tiempo objetivo o regla de aprobación se fija antes: __________. Si no se fijó, describir los tiempos observados sin afirmar objetivo superado.

| Persona anónima | Caso/orden | Riesgo entendido | Motivo entendido | Acción segura | Tiempo (s) | Ayuda / errores / interrupción |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |

Códigos de registro: correcto / incorrecto / no verificable; anotar la frase observada sin datos identificables. Errores críticos propuestos: interpretar NO CONCLUYENTE como seguro; aceptar una petición de pago para cobrar por entender que la app lo recomienda; facilitar credenciales/códigos pese al aviso. Otras dificultades —no encontrar el motivo o necesitar explicación del facilitador— se registran por separado.

Resultados que se podrán resumir cuando existan: número real de personas y tareas, respuestas correctas por criterio y denominador, acciones peligrosas, tareas sin terminar, ayudas y mediana de tiempo de tareas completadas. Mantener abandonos/errores en el informe. Varias tareas de la misma persona no equivalen a varias personas independientes; una muestra pequeña de conveniencia no valida a todas las personas mayores. **Hoy todas estas medidas están pendientes.**

## 6. Casos humanos nuevos: exploración y futuro sellado son vías distintas

| Vía | Qué está permitido preparar | Qué no permite afirmar |
|---|---|---|
| Exploratoria humana | Hoja vacía para casos ficticios nuevos con autoría/origen y etiquetas previas; ejecutarlos solo cuando se acuerde y registrar lo observado | Si sirven para ajustar reglas/prompts, pasan a desarrollo; no reutilizarlos como prueba final independiente |
| Final custodiada | Únicamente plan de responsables, criterios y permisos; ubicación externa/custodia/congelación pendientes | Esta hoja no crea, lee, autoriza ni registra un conjunto sellado real |

Ficha vacía de un futuro caso exploratorio, sin inventar mensajes ni etiquetas:

```text
ID exploratorio: ______  Autor/código: ______  Fecha: _______________
Origen declarado: humano / IA / adaptado con licencia: _____________
¿El autor conocía reglas o resultados? ____________________________
Consentimiento/permiso para usar y compartir el caso: ______________
¿Solo datos ficticios y dominios reservados? Revisión: _____________
Medio y mensaje sintético (a redactar por persona autorizada): _____
Etiquetas iniciales R1/R2 y evidencia: _____________________________
Consenso / desacuerdo abierto: ____________________________________
¿Se usó para cambiar el detector? Sí/no, versión y motivo: __________
Destino: exploratorio / desarrollo; nunca sellado por reutilización: _
```

Si intervino IA en la redacción, declararlo; la revisión humana no convierte un origen IA en humano. No copiar correos personales ni casos de licencia incierta. Para una evaluación final independiente hacen falta autores separados del ajuste, doble etiquetado previo, ubicación/custodio y autorización expresas, huella y versión congelada. Mantener ese conjunto fuera del acceso de los agentes de desarrollo. Seguir [SELLADO.md](../eval/SELLADO.md) y la [guía operativa](EVALUACION_FINAL_PROCEDIMIENTO.md); no dar por concedidos esos permisos.

## 7. Tres evidencias que no deben confundirse

- La suite técnica comprueba condiciones del código; las métricas dev describen casos conocidos.
- La cobertura literal de citas esperadas se ha medido como **0/62** en modo reglas: las descripciones deterministas actuales no adjuntan esos fragmentos como citas. Es distinto de juzgar si la señal es pertinente y de que una persona entienda la explicación. No ocultar el cero ni inventar citas.
- La comprensión requiere observación humana consentida, y la eficacia ante casos nuevos requiere una evaluación independiente custodiada. Ambas permanecen pendientes; ninguna se deduce de las plantillas preparadas.

Cierre humano de esta hoja: solo marcar revisión completa cuando haya dos fichas reales por cada uno de los 27 casos, desacuerdos resueltos o declarados, versión y consentimiento registrados y resumen fiel de pendientes. Esta preparación no marca casos como revisados ni constituye por sí misma aceptación del MVP.
