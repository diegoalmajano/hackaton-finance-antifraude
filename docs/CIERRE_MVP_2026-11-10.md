# Estado vigente del cierre — 10-11-2026

## Base, plazo y permisos
Base compartida c013f5b en feat/fase-0; cambios locales en codex/cierre-mvp. Se conserva el trabajo del equipo y main. El repositorio figura público en la consulta GitHub de esta misión; no se cambia visibilidad.

**Cierre confirmado por el usuario: miércoles 11-11-2026 a las 23:59, hora de Madrid.** Sustituye la previsión 12nov y el lapsus 9nov. Formulario rellenado según el usuario; envío no confirmado. Duración de presentación pendiente; remitente indiferente. Propuesta operativa: congelar antes de 18:00 para reservar margen; no altera el plazo.

El prompt autoriza cambios, pruebas y commits locales revisados. No autoriza nuevos pushes, PR, merge compartido, instalaciones adicionales, cuentas ni gasto. El usuario indicó no tener API de Claude; no concedió la instalación temporal propuesta. IA, presupuesto, Opus, Gmail real y pruebas de integración reales se mantienen apagados. Coste real de API en esta misión: 0 USD. Sin claves, cuentas reales ni conjunto sellado.

## Criterios fijados y cambios verificados
- H1: Bizum inverso con categoría PAYMENT_FRAUD y recomendación explícita de no pagar aun siendo la única señal. Conserva MEDIO aislada y puede corroborar un señuelo existente; no se eleva todo a ALTO.
- H2: consejos negativos por persona/impersonales y adversativas comprobados. «No debes dejar de aceptar» mantiene la señal de pago; su doble negación no se confunde con un consejo de no aceptar.
- H3: antecedente sensible cercano y envío pronominal a tercero/canal generan una señal contextual BAJA y revisión profunda acotada. El espía recibe una llamada; sin IA da NO CONCLUYENTE parcial. No hay resolución semántica general ni eficacia de Claude demostrada. Mensajes cotidianos, código postal y uso en app no escalan por ese criterio.
- H4: salto simple de maquetación conserva peticiones sensibles y la continuidad asunto/cuerpo; párrafos en blanco cortan asociaciones. La negación se comprueba en la acción emparejada, no en otra frase. No se altera fold público ni el pipeline.
- Rendimiento: clean_text evita millones de callbacks por espacios simples mediante traducción y colapso de espacios múltiples. Igual salida que la versión previa en 1003 casos sintéticos. No se modifica el límite de 3 s del correo de 5 MiB ni sus criterios de parcialidad.

27 regresiones nuevas en test_i_cierre_detector.py. Se conservan tests previos, xfail conocido, etiquetas y casos dev; sin nuevos skips. La revisión detectó antes de finalizar la regresión de peticiones partidas y la doble negación; ambas se reprodujeron y corrigieron. Solo 3 archivos de producto: rules.py, text.py y risk/engine.py. Versión **rules-0.3.5**.

## Pruebas y límites
Suite definitiva: **926 passed, 4 skipped, 1 xfailed, 1 warning**, 23,53 s. Los cuatro saltos son tres Claude y un Gmail reales; xfail de «facilítesela» y deprecación Starlette/httpx conocidos. 11 pruebas JS correctas con DOM/temporizadores simulados. Gmail: 8 comprobaciones SDK correctas con HTTP/OAuth/keyring falsos; 53 paquetes fijados y 26 base conservados, pip check correcto, sin nuevas instalaciones.

Historial de rendimiento: primera repetición basal falló a 3,42 s (898 correctas); aislada pasó 2,19 s. Otra suite intermedia falló en el mismo umbral. Tras perfilar y optimizar, la prueba pasó 2,01 s aislada y 2,15 s en una suite intermedia verde. La última suite completa pasa sin relajar el límite. Los tiempos dependen del equipo/carga, no son SLA.

Dev repetido con .5: 27 casos sintéticos, 14 VP / 0 FP / 0 FN / 10 VN y 3 ambiguos aparte; 27/27 niveles aceptables, 17 parciales y 1 NO CONCLUYENTE. p50=4ms/p95=7ms del motor local en esa ejecución, sin navegador ni IA. No generalización ni evaluación independiente. Citas esperadas 0/62: las descripciones de reglas no son citas literales; separar pertinencia de señal, exactitud de cita y comprensión humana.

## Estado de integraciones y revisión humana
Gmail real, OAuth, lectura de cuenta, renovación y keyring Windows siguen no probados y sin permiso. El permiso readonly permite lectura amplia aunque la aplicación procese solo nuevos; la conexión necesita consentimiento explícito. Borrado local de token no equivale a revocación remota. Preparación concreta y matriz de aceptación en GMAIL_PREPARACION_REAL.md.

Claude sigue sin SDK instalado, clave ni gasto. PLAN_PILOTO_SONNET.md revalida las fuentes oficiales y propone un piloto, no lo autoriza. No se cambia proveedor. OAuth de Gmail no concede envío a IA.

REVISION_HUMANA_MVP.md contiene 27 IDs y fichas vacías, doble revisión, consenso y comprensión de nivel/motivo/acción/tiempo/errores. No participantes ni resultados inventados. VALOR_DIFERENCIAL.md compara documentación oficial sin superioridad ni ventas/ahorro demostrados. Evaluación independiente y custodia de sellado pendientes.

Linux/axe del 09nov son evidencia reportada del compañero sobre su versión, no una auditoría repetida ahora ni evaluación independiente de eficacia. Narrador audible, contraste Windows, zoom real final y teclado manual completo siguen no verificados y diferidos por el usuario; no se solicitan de nuevo. No audio.

## Entrega y siguiente paso
Se actualizan README, estado, arquitectura, guion y fuentes existentes; PPTX/PDF se renderizan y validan conservando diseño. No se añaden canales, escritorio, personalización, SQLite ni rediseño. Cinco dominios web bancarios siguen siendo cobertura parcial, no un directorio completo de correo. Cabeceras Authentication-Results importadas son datos declarados, no autenticidad verificada por el prototipo.

El ZIP candidato local se revisa sin secretos, privados, entornos ni sellados y se ensaya desde extracción limpia con un entorno previamente autorizado. El ZIP oficial debe descargarse desde GitHub después de una publicación autorizada de esta revisión; ese paso y el envío del formulario siguen pendientes. La demo y los materiales deben corresponder al mismo commit final.

## Evidencia final de extracción y materiales
- Candidato local: 189 archivos publicables, CRC y SHA-256 por archivo comprobados. Escaneo de 280 unidades incluidas partes PPTX y texto/streams PDF: 3 avisos revisados (ruta de plantilla y valores explícitamente falsos), ningún secreto real detectado en ese alcance. No es una garantía universal de ausencia de secretos.
- Extracción limpia con entorno Gmail existente autorizado (sin reinstalar): 926 passed, 4 skipped, 1 xfailed, 1 warning en 26,86 s; 11 JS y 8 SDK Gmail correctas. Solo cambia este registro documental tras esas pruebas; el código se conserva idéntico.
- CLI real importado de la extracción, solo loopback en puerto efímero: cuatro .eml sintéticos→BAJO/ALTO/ALTO/NO CONCLUYENTE; Bizum→MEDIO y consejo de no pagar visible; consejo negativo→BAJO; referencia sensible→NO CONCLUYENTE. Logout protegido, desconexión del servidor y segundo arranque con nuevo emparejamiento correctos. Códigos/tokens solo en memoria; procesos propios terminados.
- PPTX: 12 diapositivas renderizadas e inspeccionadas; textos cotejados con JSON; paquete, geometría y reimportación correctos. No abierto en PowerPoint. SHA-256:8c1291661e5d1bc71441985895f79999dc2b6faec06dcc0c376c3cf110bc2582.
- PDF: 1 página A4 desde HTML con ReportLab incluido, texto y render inspeccionados. SHA-256:76e83afa7ced2ecfc118c166c3f05338d5504e882319b7b00d6ac8f72192dcc0. Ambos archivos del repo coinciden byte a byte con los validados.
- Rama codex/cierre-mvp conserva feat/fase-0 y main. Commit local autorizado tras revisión; no push/PR/merge/release. La referencia exacta se obtiene con git log -1. ZIP oficial remoto y envío siguen pendientes de su permiso/confirmación; no se marcan completados.
