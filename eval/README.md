# Banco de evaluación del detector antifraude

> Estado revisado el 09-11-2026: el detector y el evaluador están implementados. Los datos actuales son **de desarrollo** y se han usado para ajustar el motor; sus resultados **no son una evaluación independiente**. No hay conjunto final registrado ni evaluación independiente realizada. No se han creado ni consultado casos sellados en esta revisión.

## 1. Estructura y estado comprobado

```text
eval/
├── README.md                    formato, particiones y métricas
├── EJECUCION.md                 comandos y alcance de los controles
├── METODOLOGIA_INDEPENDIENTE.md  autoría, etiquetado, custodia e interpretación
├── SELLADO.md                   registro/procedimiento del conjunto externo
└── datasets/dev/
    ├── demo.jsonl               3 casos sintéticos para la demostración
    └── casos_dev.jsonl          24 casos adicionales de desarrollo
```

Los 27 casos validados declaran `origin=synthetic_ai`, `is_synthetic=true` y `review_status=pending_human_review`: **17 email y 10 SMS**. Las etiquetas distinguen 14 casos que deben alertar, 10 legítimos y 3 ambiguos. No se cambian origen, etiquetas ni estado de revisión para mejorar las cifras.

Ignorados por Git: `eval/datasets/test_sealed/`, `eval/sealed/`, `eval/results/`, `eval/reports/local/` y `*.sealed.jsonl`. El conjunto final debe vivir fuera del repositorio, en una ubicación y con una autorización decididas por el usuario (T-14, D-40).

## 2. Formato de los casos

Fuente de verdad: [EvalCase](../backend/antifraude/contracts/evaluation.py). Archivos JSONL UTF-8, un caso por línea.

- `case_id`: `dev-NNNN` o `test-NNNN`; `split`: `dev` o `sealed_test`.
- `origin`: `synthetic_human`, `synthetic_ai` o `adapted_licensed`; los orígenes sintéticos exigen `is_synthetic=true`.
- `author`, `created`, `review_status`, `demo_order` opcional y `tags`.
- `message`: medio, fecha, remitente, SPF/DKIM/DMARC declarados, respuesta, asunto y texto/HTML.
- `expected`: etiqueta, niveles aceptables, `must_alert`, categorías, citas esperadas literales y señales que justifican la etiqueta.
- `rationale_es`: justificación de la persona que etiqueta, sin observar la predicción.

El contrato comprueba coherencia de nivel/alerta/categorías, prefijo de partición y literalidad de las citas esperadas. Las etiquetas no contienen resultados del detector. Los tests validan también la unicidad y las restricciones de datos del conjunto dev; el custodio debe realizar esas comprobaciones en cualquier conjunto final autorizado.

## 3. Datos ficticios y ausencia de fugas

Solo dominios reservados de documentación/pruebas: `.example`, `.test`, `.invalid` y `example.com/.org/.net`. Sin datos personales, IBAN válidos, teléfonos, DNI ni tarjetas reales. Las pruebas revisan los casos dev.

Los resultados de autenticación de los correos sintéticos son **simulados**. Un remitente autenticado no convierte un mensaje en seguro: las peticiones sensibles conservan sus mínimos de riesgo. El análisis de enlaces es pasivo; no se resuelven sus dominios, descargan archivos ni siguen redirecciones. Esto es distinto de las integraciones externas autorizadas de la aplicación, que permanecen desactivadas en esta evaluación sin gasto.

Los casos `synthetic_ai` se separan de los redactados por personas para declarar el riesgo de circularidad. Revisarlos manualmente no cambia su autoría ni los convierte en una muestra independiente.

## 4. Demostración y desarrollo

| Orden | Caso | Nivel esperado | Aceptables |
|---|---|---|---|
| 1 | `dev-0001`, extracto mensual informativo | BAJO | BAJO |
| 2 | `dev-0002`, bloqueo y petición de claves/código | ALTO | ALTO |
| 3 | `dev-0003`, falso gestor y enlace engañoso | ALTO | MEDIO o ALTO |

El contenido completo de los 27 casos sigue pendiente de revisión humana. Los tres ejemplos pueden usarse para demostrar el producto, siempre etiquetados como sintéticos; no prueban generalización.

La ejecución local sin IA revisada mantiene niveles aceptables en los 27 casos. Es un resultado del conjunto usado para desarrollar, no una estimación de rendimiento ante mensajes reales. Las suites y la versión actual se registran en [seguimiento](../docs/contexto/15_SEGUIMIENTO.md), sin fijar aquí un número global de tests que cambia durante el desarrollo.

## 5. Particiones y custodia

- **Desarrollo:** los 27 casos del repositorio se pueden inspeccionar para desarrollar y comprobar regresiones.
- **Evaluación final:** archivo externo custodiado, no accesible a los agentes durante el desarrollo y no autorizado todavía. No crear, consultar ni ajustar un conjunto final a partir de este documento. Antes de ejecutar se necesitan ubicación, autoría/etiquetado, huella, versión congelada y autorización específica.

La huella y una marca local de ejecución no acreditan por sí solas la independencia del conjunto, que nadie lo haya visto antes ni que el código se haya congelado. Véanse [metodología](METODOLOGIA_INDEPENDIENTE.md), [ejecución](EJECUCION.md) y [guía operativa humana](../docs/EVALUACION_FINAL_PROCEDIMIENTO.md).

## 6. Métricas implementadas y límites

Clase positiva: `expected.must_alert=true`; predicción positiva: MEDIO o ALTO. Las etiquetas NO CONCLUYENTE quedan fuera de VP/FP/FN/VN y se informan aparte. Un fraude predicho BAJO o NO CONCLUYENTE cuenta como FN.

| Métrica | Definición/alcance |
|---|---|
| VP, FP, FN, VN | Conteos de alerta binaria, excluyendo etiquetas ambiguas |
| **Precision** | VP/(VP+FP); null si no hay predicciones positivas |
| **Recall** | VP/(VP+FN); null si no hay casos positivos |
| **F1** | 2VP/(2VP+FP+FN); cero si hay FP/FN sin VP, null si el denominador está vacío |
| Tasa de falsos positivos | FP/(FP+VN), solo etiquetas legítimas |
| NO CONCLUYENTE | Número y tasa de predicciones sobre todos los casos |
| Ambiguos | Número, niveles aceptables y alertas separados, sin llamarlos FP |
| Acierto de nivel | Predicción dentro de `acceptable_levels` |
| Citas | Citas esperadas cubiertas literalmente dentro de citas verificadas de evidencias |
| Análisis parcial | Número de casos con comprobaciones incompletas |
| **Latencia** | p50/p95 del análisis completo, medidos localmente; no latencia separada del filtro |
| **Coste por mensaje** | Solo calculable a partir de consumo completo autorizado y número de análisis; no está medido con API real |

El JSON incluye desgloses por origen y medio e intervalos de Wilson para precisión, recall y tasa de FP. No se genera un intervalo de Wilson de F1. Los grupos sin denominador producen null; no se sustituyen por aciertos perfectos.

En la revisión local solo reglas, la cobertura literal fue **0 de 62 citas esperadas**: las evidencias deterministas actuales explican señales pero no adjuntan esos fragmentos como citas. Esto no prueba que todas las explicaciones sean incorrectas; tampoco acredita su calidad. La comprobación de citas debe complementarse con revisión humana de exactitud, claridad y recomendaciones. No se añaden citas ni se cambian expectativas para maquillar esa cifra.

La telemetría de IA cuenta transportes nuevos verificados por CostGuard, separa bloqueos/caché y no duplica usage reutilizado. Si falta usage o telemetría, el total de coste es null; se informa aparte la suma conocida. Las simulaciones con tokens ficticios no constituyen una medición de gasto real. Antes de una futura prueba de pago deben aprobarse modelo, datos, privacidad, número de peticiones, precios vigentes y presupuesto.

Los informes dev siguen siendo de desarrollo aunque las métricas sean perfectas. Solo una evaluación con autoría/custodia independiente documentadas permite formular conclusiones limitadas por su tamaño, composición e intervalos. No se autorizan llamadas reales, publicación ni acceso al sellado mediante estos documentos.
