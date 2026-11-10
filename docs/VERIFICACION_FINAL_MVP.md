# Verificación final local del MVP — 09-11-2026

> Estado vigente de cierre, 10-11-2026: rules-0.3.5, 926 Python / 11 JS / 8 SDK Gmail simulados. Rama codex/cierre-mvp, base compartida c013f5b, sin publicación nueva. Evidencia y pendientes: [CIERRE_MVP_2026-11-10.md](CIERRE_MVP_2026-11-10.md). Las secciones fechadas anteriores son históricas.

## Alcance y resultado
Prototipo de hackatón, no producto bancario comercial. Continuación desde dd3e4fb en feat/fase-0. No se modifica main, no se publica ni se llama a APIs de pago. Coste real de API durante esta misión: 0 USD. IA/Opus/presupuesto e integraciones reales apagados; no se usan claves ni cuentas reales.

## Pruebas realizadas
- Suite base completa: 877 passed, 4 skipped, 1 xfailed, 1 warning (21,17 s). Los saltos son tres Claude y un Gmail reales. El xfail de «facilítesela» sigue identificado. Aviso deprecación Starlette/httpx sin actualizar dependencias.
- 11 pruebas JS con DOM/temporizadores simulados. Ocho comprobaciones SDK Gmail separadas con librerías instaladas y transporte/OAuth/keyring falsos y red vetada. No son verificaciones de una cuenta real.
- Instalación nueva autorizada solo en un entorno temporal Gmail: 53 paquetes fijados, las 26 versiones base idénticas a requirements.lock; pip check sin conflictos. Entorno del proyecto sin cambios; SDK Anthropic y OpenAI ausentes.
- Navegador IAB y servidores locales reales: emparejamiento, formulario vacío, cuatro archivos .eml, prioridad del archivo, error .txt y recuperación, resultados BAJO/MEDIO/ALTO/NO CONCLUYENTE, detalles, cierre protegido. A 320×800 CSS, documento 305/305 sin desbordamiento horizontal. Consola sin infracciones CSP observadas; error 400 deliberado identificado.
- Gmail SIMULADO en navegador: consentimiento, alerta ALTO explicada, contador, foco/desplegable estable entre sondeos sin cambios, reflujo, desconexión y cierre. Pruebas de carreras de limpieza/reconexión, caducidad, errores y autorización antes de cada página. Los procesos propios se detuvieron.
- PPTX existente reconciliado: 12 diapositivas renderizadas e inspeccionadas, texto contrastado con JSON, paquete/geometría/reimportación correctos. No se abrió en PowerPoint. PDF A4 de una página, texto extraído y render inspeccionado.

## Fiabilidad y evaluación
rules-0.3.3 añade 38 regresiones: solicitudes de transferencia/OTP con clíticos, manipulación formal y negaciones coordinadas, sin rebajar el motor. Son pruebas de regresión, no muestra representativa de fraude.

Desarrollo: 27 casos synthetic_ai pendientes de revisión humana, 14 VP / 0 FP / 0 FN / 10 VN y 3 ambiguos aparte; 27/27 niveles aceptables según etiquetas actuales, 17 análisis parciales y 1 NO CONCLUYENTE. Precisión/recall/F1 de 1 en este pequeño banco ajustado no predicen rendimiento externo. Las reglas no adjuntan las citas literales esperadas del banco: cobertura 0/62; la calidad de explicación requiere revisión humana. No evaluación independiente, no conjunto sellado leído/creado. Procedimiento en EVALUACION_FINAL_PROCEDIMIENTO.md y eval/.

## Seguridad corregida
Consumo remoto malformado conserva cargo pesimista; libro inconsistente falla cerrado; caché aislada por usuario y contexto. No se promete resistir borrado/sustitución coherente de ambos libros bajo control del SO; antes de gasto debe existir límite externo de Console. Gmail conserva consentimiento por sesión, guardia por página y limpieza; un error no produce BAJO. Se mantienen Host/Origin/CSRF, cookie HttpOnly/SameSite Strict, CSP local, minimización y enlaces pasivos sin DNS ni visitas.

## No verificado / pendiente
- OAuth y recepción/renovación reales de Gmail; keyring Windows real; requiere cuenta de pruebas y proyecto/JSON OAuth fuera del repo. Desconectar elimina permiso local, no revoca el consentimiento remoto en Google.
- Claude real y compatibilidad SDK Anthropic: instalación y gasto no autorizados. PLAN_PILOTO_SONNET.md propone un ensayo acotado, sin concederlo. Sin comparativa real Sonnet/Opus.
- Narrador audible, tema Windows de contraste, teclado manual completo y zoom real 200 % del diseño final. Zoom de versión anterior confirmado por el usuario; no extrapolar. No más solicitudes de esas pruebas por ahora; sin declaración WCAG.
- Revisión humana dev/directorio y evaluación independiente; cobertura bancaria parcial, anáforas e ingeniería social implícita limitadas. Nombre del producto y hora exacta de cierre pendientes.
- ZIP oficial descargado desde GitHub tras una futura publicación autorizada. El candidato local es revisión interna, no artefacto remoto publicado.

## Reproducción y entrega
Instalar requirements.lock para el flujo manual sin APIs. requirements-gmail.lock es opcional, validado en Windows/Python 3.12, no autorización para conectar cuentas. Bloque seguro del README para la demo. El ZIP se genera fuera del repo mediante lista de fuentes actuales revisada; excluye .git, entornos, ignorados, datos privados, credenciales y sellados. Evidencia técnica de manifiestos, escaneo y comprobación extraída conservada fuera del repo. Resultados de la extracción limpia registrados a continuación.

## Evidencia de la extracción limpia
- ZIP candidato: 181 archivos publicables revisados. Extracción nueva sin .git, .venv ni datos privados; manifiesto SHA-256 por archivo y verificación de CRC/contenido. Escaneo de 272 unidades (incluye XML de PPTX y texto/streams PDF): tres avisos revisados, todos ruta de plantilla o secretos explícitamente sintéticos; no se detectaron secretos reales mediante esta revisión.
- Desde el ZIP extraído y el entorno Gmail recién instalado autorizado: **877 passed, 4 skipped, 1 xfailed, 1 warning** en 22,25 s; **11 JS correctas**; **8 SDK correctas**. Sin nuevas instalaciones ni llamadas reales. pip check correcto. Código/pruebas idénticos a la fuente; los ajustes posteriores solo completan esta documentación y su manifiesto.
- CLI real importado desde esa extracción, puerto efímero de loopback: cuatro .eml → BAJO, ALTO, ALTO, NO CONCLUYENTE; cierre protegido, proceso detenido, desconexión observada y segundo arranque con nuevo emparejamiento y análisis correcto. Códigos solo en memoria; procesos propios terminados.
- Los dos materiales entregados coinciden byte a byte con los validados: PPTX SHA-256 31a786229f4c3d91eac78fe34180f940abc9fb1e8ac69adb9e6b8696862d488a; PDF SHA-256 38d16d8238a2dd37ed1c0f37018f01f551413d67688b71a23a39c40c8ee6e793.
- Base Git dd3e4fb y main 2f27d7f preservados. Consolidación local autorizada tras revisión; ningún push, PR, release ni cambio de visibilidad. La identidad del commit que contiene este informe se consulta con git log -1. El ZIP es candidato local, no descarga oficial remota.
