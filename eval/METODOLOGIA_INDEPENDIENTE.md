# Metodología de evaluación independiente (propuesta)

> Objetivo: medir el detector con casos que **no se hayan usado para ajustarlo**, de forma reproducible y honesta. Esta metodología **no crea el conjunto sellado**: su ubicación sigue pendiente (T-14, D-40) y ningún agente lo ha consultado.

## 1. Por qué las cifras actuales no sirven como evaluación
- Los 27 casos de desarrollo se usaron para **ajustar** las reglas. Tras el ajuste dan precisión, recall y F1 de 1,00 en esos casos, y eso **no dice nada** del rendimiento con mensajes nuevos.
- 26 de 27 casos son **sintéticos** y los redactaron modelos de IA. Hay riesgo de circularidad: la IA escribe los casos y el sistema, que también usa IA, los detecta (R-26).
- El tamaño es pequeño: con 14 fraudes, el intervalo de Wilson del recall va de 0,78 a 1,00 incluso con un acierto perfecto.

## 2. Construcción del conjunto sellado
1. **Autores:** personas que **no hayan visto las reglas ni el código** del detector. Por ejemplo, otro miembro del equipo o personas externas con instrucciones escritas. Si no es posible, el autor escribe los casos **antes** de mirar los resultados del detector, y se declara esta limitación.
2. **Tamaño recomendado:** al menos 40 casos (≥ 15 fraudes, ≥ 15 legítimos, ≤ 10 ambiguos). Más casos estrechan los intervalos de confianza.
3. **Diversidad:** correo y SMS; bancos, paquetería, administración, familia, inversión, soporte técnico y facturas; estafas evidentes y sofisticadas; legítimos urgentes, legítimos con faltas de ortografía y avisos de seguridad legítimos («nunca le pediremos…»).
4. **Origen:** preferiblemente `synthetic_human`, o casos adaptados de fuentes públicas con licencia (`adapted_licensed`). Los `synthetic_ai` se informan **por separado**.
5. **Datos ficticios:** solo dominios reservados y ningún dato personal. Se comprueba con las mismas pruebas que el conjunto de desarrollo.

## 3. Etiquetado
- **Doble etiquetado ciego:** dos personas etiquetan cada caso por separado (nivel, niveles aceptables, `must_alert`, categorías). Se calcula el acuerdo (porcentaje y **kappa de Cohen**) y los desacuerdos se resuelven por consenso. Ambos datos se registran.
- La política de niveles es la de ADR-0006 y D-29. Se etiqueta por el contenido, **nunca mirando la salida del detector**.

## 4. Sellado y custodia
1. Archivo JSONL con formato `EvalCase` (`split = "sealed_test"`, `case_id = test-NNNN`) **fuera del repositorio**, en la ubicación que decida el usuario (T-14).
2. Se calcula el SHA-256 y en `eval/SELLADO.md` se registran solo la fecha, el número de casos por tipo y origen, y la huella.
3. Recomendado: añadir en `.claude/settings.local.json` una regla que **impida a los agentes leer** esa ruta (T-18). Requiere la aprobación del usuario.

## 5. Ejecución (una sola vez)
1. Congelar el commit del detector; no tocar las reglas a partir de ese momento.
2. Comprobar el SHA-256 del archivo sellado.
3. Ejecutar dos configuraciones: **solo reglas** y, si hay presupuesto aprobado, **reglas + IA** (Sonnet 5.5 y Opus 5.5, D-32).
4. Guardar los resultados en `eval/results/` (ignorado por Git) y **no modificar casos después**.

## 6. Métricas e informe
- Clase positiva: `must_alert = true`. Predicción positiva: MEDIO o ALTO.
- Los casos con etiqueta **NO CONCLUYENTE** se excluyen de la precisión y de la tasa de falsos positivos, y se informan aparte (nivel aceptable y alertas).
- Se informan: VP, FP, FN, VN, precisión, recall, F1 y tasa de falsos positivos, **con intervalos de Wilson y el número de casos**; la tasa de NO CONCLUYENTE; el acierto de nivel (dentro de `acceptable_levels`); y las citas esperadas presentes en las evidencias.
- **Latencia** (p50 y p95) en la máquina de la demo. **Coste por mensaje** a partir del `usage` real y de los precios vigentes ese día.
- Resultados separados por origen (`synthetic_human`, `synthetic_ai`, `adapted_licensed`) y por medio (correo y SMS).
- Análisis de errores: cada FN y FP, con su causa.

## 7. Qué se puede afirmar después
- Solo las cifras del conjunto sellado, con su tamaño, sus intervalos y su origen. Por ejemplo: «En 40 mensajes de prueba escritos por personas que no vieron el detector, detectó X de Y estafas (IC95 % …)».
- **Nunca** porcentajes de eficacia sin intervalo, ni cifras de desarrollo presentadas como evaluación.
