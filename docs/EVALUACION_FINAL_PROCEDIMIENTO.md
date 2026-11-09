# Cierre operativo de la evaluación: guía para revisión humana

Estado: procedimiento preparado, **evaluación independiente no realizada**. No se han creado ni consultado casos finales sellados. Esta guía concreta la ejecución de [la metodología existente](../eval/METODOLOGIA_INDEPENDIENTE.md); no sustituye sus criterios ni el [contrato EvalCase](../backend/antifraude/contracts/evaluation.py).

## Responsables y puertas de entrada

| Responsable | Acción | Evidencia necesaria para cerrar |
|---|---|---|
| Usuario/custodio | Decide ubicación externa y quién redacta/etiqueta; conserva el archivo sin dar acceso a los agentes de desarrollo | Decisión explícita, ruta fuera del repositorio y control de acceso |
| Autores externos al desarrollo | Redactan los casos antes de conocer resultados o reglas; solo datos ficticios | Declaración de autoría/origen y ausencia de acceso al detector; declarar excepciones |
| Dos revisores | Etiquetan por separado, sin ver resultados del sistema; explican los desacuerdos y acuerdan la versión final | Dos etiquetas originales, acuerdo y kappa de Cohen; justificación de consenso |
| Custodio | Valida formato, dominios reservados, ausencia de datos personales, duplicados y fuga respecto a dev | Inventario y revisión documentados; ninguna exclusión basada en el resultado del detector |
| Responsable de ejecución autorizado | Congela versión limpia y ejecuta una vez la huella aprobada | Commit, árbol limpio, lock, Python/entorno, SHA-256 y configuración; informe agregado |

No basta con llamar a un archivo «sellado» para que sea independiente. Si sus autores conocían el detector o los casos se redactaron después de ver resultados, se declara esa limitación. La revisión humana pendiente del conjunto dev tampoco convierte sus métricas en evaluación independiente.

## Antes de la ejecución

1. Fijar las reglas de etiquetado y tratamiento de ambiguos de la metodología antes de analizar. Los fraudes que salen NO CONCLUYENTE cuentan como falsos negativos para la alerta binaria; las etiquetas ambiguas se informan aparte.
2. Cerrar casos y etiquetas; acordar cualquier exclusión por formato o datos privados antes de observar predicciones. Mantener la diversidad y los orígenes identificados.
3. Registrar solo metadatos públicos y huella según [SELLADO.md](../eval/SELLADO.md). No pegar casos, rutas privadas ni secretos en el chat.
4. El custodio verifica el commit limpio. Un informe con arbol_trabajo_sucio=true no acredita reproducibilidad de ese commit; con null no pudo comprobarse Git. El informe añade Python, plataforma y huella de requirements.lock, pero esos metadatos no demuestran por sí solos que todas las dependencias instaladas coincidan con el lock.
5. Decidir primero la configuración: solo reglas funciona sin API. IA sigue desautorizada con presupuesto cero; no ejecutar modos de pago ni instalar SDK sin permiso específico. Consultar los comandos en [EJECUCION.md](../eval/EJECUCION.md) solo cuando exista autorización de la evaluación final. No se ejecuta desde esta guía.

## Lectura del informe actual

- VP/FP/FN/VN, precisión, recall, F1 y tasa de FP: agregados globales y separados por origen y medio. F1 es cero cuando hay FP/FN pero ningún VP; null significa denominador vacío. Se añaden intervalos de Wilson para proporciones, no un supuesto intervalo binomial de F1.
- Casos ambiguos: número, acierto de nivel y alertas separados; tasa de NO CONCLUYENTE sobre todos los casos y número de análisis parciales.
- Citas: fracción de expected_quotes que aparecen literalmente dentro de citas verificadas de las evidencias. No evalúa por sí sola claridad, corrección de toda la explicación ni calidad de las recomendaciones. Los informes no guardan el texto de las citas.
- IA: solicitudes nuevas desde el contador del transporte de CostGuard; caché y bloqueos locales separados. Un adaptador sin esa telemetría tiene llamadas/coste null. Las simulaciones siguen siendo simulaciones aunque tengan uso de tokens ficticio.
- Coste: suma de usage disponible de solicitudes nuevas, sin duplicar caché. Si una solicitud no devuelve coste/usage, el total es null y se muestra aparte la suma conocida; el cargo pesimista permanece en el libro local. Ninguna cifra sustituye la factura del proveedor. Sin llamadas reales no se presenta como coste real medido.
- Latencia p50/p95: análisis local medido por caso. Registrar máquina y condiciones, sin extrapolar a otros equipos.

## Revisión de explicaciones y cierre ante el jurado

Dos revisores comprueban, sin modificar el detector: si cada evidencia corresponde al mensaje, si el consejo es seguro y aplicable, si se declara lo no comprobado y si el lenguaje responde a «¿es peligroso?, ¿por qué?, ¿qué hago?». Registrar cada criterio como correcto/incorrecto/no verificable y conservar desacuerdos. No convertir esta revisión cualitativa en una puntuación inventada.

El informe técnico final debe declarar tamaño, composición, origen, autoría, intervalos, ambigüedad, errores y configuración. No comparar reglas e IA si no se ejecutaron ambas de forma autorizada sobre la misma versión congelada. No retocar reglas tras ver el conjunto final y seguir presentando ese resultado como independiente: cualquier cambio posterior exige otra evaluación y un conjunto nuevo autorizado.

Pendientes externos: ubicación/custodia, autores y revisores humanos, casos y etiquetas independientes, autorización de una ejecución final; y, solo para la variante con IA, SDK/modelo/datos/privacidad/presupuesto aprobados. Esta guía no concede ninguna autorización ni registra esas tareas como realizadas.
