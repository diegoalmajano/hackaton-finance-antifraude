# Metodología de evaluación independiente (propuesta)

> Objetivo: medir con casos que no se hayan utilizado para ajustar el detector, con autoría/custodia documentadas y resultados reproducibles. **Evaluación independiente pendiente**. Este documento no crea casos finales ni autoriza su consulta; faltan ubicación, responsables y permiso de ejecución (T-14, D-40).

## 1. Por qué las cifras dev no validan el producto

Los **27 casos de desarrollo** se usaron para ajustar las reglas y todos declaran `synthetic_ai`: 17 email y 10 SMS. Su revisión humana sigue pendiente. Hay riesgo de circularidad y sesgo de selección; un resultado perfecto en esos casos no estima rendimiento con mensajes nuevos.

El tamaño también limita cualquier conclusión: hay 14 etiquetas que deben alertar, 10 legítimas y 3 ambiguas. Incluso 14/14 detecciones producen un intervalo de Wilson del recall aproximadamente [0,78; 1,00]. Los estratos aún más pequeños tienen mayor incertidumbre. No se cambian etiquetas ni origen para presentar mejores métricas.

## 2. Autoría y construcción, antes de usar el detector

1. **Autores:** personas que no hayan visto reglas/código ni resultados de los casos. Si no es posible, declarar la relación con el desarrollo y evitar llamar independiente a ese conjunto.
2. **Tamaño orientativo:** al menos 40 casos, con ≥15 fraudes, ≥15 legítimos y ≤10 ambiguos. No es una garantía estadística; registrar el tamaño y composición realmente conseguidos.
3. **Diversidad:** correo/SMS; banca, paquetería, administración, familia, inversión, soporte y facturas; estafas evidentes y sofisticadas, legítimos urgentes, con faltas y consejos de seguridad legítimos.
4. **Origen:** preferir `synthetic_human` o `adapted_licensed` con licencia registrada. Los `synthetic_ai` se informan por separado y no se presentan como autoría humana.
5. **Privacidad:** datos ficticios y dominios reservados. El custodio autorizado valida formato, duplicados, ausencia de datos personales y solapamiento con dev antes de cerrar. No copiar mensajes personales sin consentimiento.

Los agentes de desarrollo no redactan el conjunto final ni buscan ejemplos de él para ajustar el sistema. El conjunto dev continúa siendo dev aunque luego una persona revise sus etiquetas.

## 3. Etiquetado humano ciego

Dos personas etiquetan por separado nivel, niveles aceptables, `must_alert`, categorías y evidencias esperadas conforme a ADR-0006/D-29, sin observar predicciones. Se registra acuerdo inicial, kappa de Cohen y desacuerdos; el consenso final se justifica sin modificar casos para favorecer al detector. El acuerdo tampoco demuestra que las etiquetas sean universalmente correctas.

Las etiquetas NO CONCLUYENTE representan ambigüedad y se separan de la clasificación binaria. La política queda fijada antes de ejecutar: un fraude que no alerta, incluido un resultado NO CONCLUYENTE, cuenta como FN; una etiqueta ambigua con alerta no cuenta automáticamente como FP.

## 4. Sellado, ubicación y custodia

Archivo EvalCase JSONL con `split=sealed_test` e identificadores `test-NNNN`, fuera del repositorio y en la ubicación que determine el usuario. Hasta esa decisión no se crea ni se consulta. En [SELLADO.md](SELLADO.md) solo se registran metadatos aprobados: fecha, recuentos/origen y SHA-256.

El custodio restringe la lectura para los agentes y acuerda las medidas del entorno actual (T-18); no se ejecuta Claude Code/ECC ni se cambia configuración personal para ello. La huella detecta cambios respecto a un valor conocido, pero no acredita que nadie haya visto el contenido ni que sus autores sean independientes.

## 5. Ejecución planificada una sola vez

1. Congelar código, reglas y prompts en un commit limpio; registrar entorno/dependencias y validar la huella con el custodio.
2. Aprobar previamente la configuración: solo reglas, o reglas más **un** modelo aprobado en la misma ejecución `--modo ambos`. La IA sigue desautorizada con presupuesto cero; modelo exacto, SDK, datos transmitidos, privacidad, precios y presupuesto requieren permiso propio. No se autoriza Opus por citar comparativas históricas.
3. La CLI actual no ejecuta una matriz Sonnet/Opus bajo una misma huella. Cualquier comparación adicional debe diseñarse y autorizarse antes del cierre; no borrar marcas ni repetir para obtener mejores resultados.
4. Guardar informe y registro de ejecución sin textos en `eval/results/` (ignorado), con copia custodiada. Una interrupción posterior a la marca no habilita otra ejecución automática. La marca local no protege contra manipulación o copias en otros entornos: mantener la custodia sigue siendo necesario.
5. No modificar casos ni ajustar reglas al conocer el resultado final. Un cambio posterior exige una nueva evaluación y un conjunto nuevo autorizado para sostener una afirmación independiente.

El preflight de IA no autorizada o sin confirmación falla antes de leer o marcar el conjunto. No sustituye la autorización humana del propio conjunto. Instrucciones operativas: [EJECUCION.md](EJECUCION.md) y [guía de cierre humano](../docs/EVALUACION_FINAL_PROCEDIMIENTO.md).

## 6. Métricas y revisión de explicaciones

- VP/FP/FN/VN, precisión, recall, F1 y tasa de FP; cantidad de casos y denominadores. Wilson para proporciones de precisión, recall y tasa de FP; no se aplica como un supuesto intervalo binomial de F1.
- Tasa de predicciones NO CONCLUYENTE sobre todos los casos; etiquetas ambiguas, acierto de nivel y alertas aparte. F1 es cero si VP=0 con FP/FN y null solo con denominador vacío.
- Resultados separados por origen y medio. Análisis de cada FP/FN por revisores autorizados; no retirar errores ni aprender del conjunto final mientras se mantiene la misma afirmación de independencia.
- Latencias p50/p95 del análisis completo en la máquina y condiciones registradas. La CLI no mide por separado latencia del filtro.
- Cobertura literal de `expected_quotes` dentro de citas verificadas de evidencias. En dev solo reglas fue **0/62**: las evidencias deterministas actuales describen señales pero no adjuntan esos fragmentos. No acredita ni invalida por sí sola exactitud, claridad o utilidad de las explicaciones; se requiere revisión humana complementaria.
- Número de análisis parciales. La revisión humana verifica evidencia, incertidumbre declarada y consejo seguro; no se inventa una puntuación global de calidad.
- Coste por análisis solo a partir de solicitudes autorizadas y consumo completo, con precios vigentes verificados. Se excluye doble cargo de caché y se separan bloqueos. Con usage/telemetría incompletos, coste total null y suma conocida aparte; las reservas pesimistas del libro no son una factura. Tokens ficticios de un transporte simulado no son coste real medido.

## 7. Afirmaciones defendibles

Hoy solo hay resultados de desarrollo y pruebas técnicas, sin evaluación independiente ejecutada. Cuando se complete el procedimiento, describir tamaño, composición, origen, autoría, relación con el desarrollo, versiones, configuración, intervalos, ambigüedad y limitaciones. No atribuir a mensajes reales conclusiones de un pequeño conjunto sintético.

No basta con que el informe diga «sellado»: la independencia depende del proceso humano documentado. No publicar métricas dev como eficacia, ni porcentajes de acierto sin muestra/intervalo, ni simulaciones como integraciones reales. La publicación de resúmenes y cualquier uso de APIs reales mantienen sus autorizaciones separadas.
