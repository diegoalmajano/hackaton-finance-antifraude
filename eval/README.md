# Banco de evaluación del detector antifraude

> F0-08 (2026-11-08). **El detector todavía no existe**: aquí no hay resultados ni métricas, solo el formato, los casos de desarrollo y el procedimiento de medición. Nada de este directorio debe presentarse como rendimiento del sistema.

## 1. Estructura
```
eval/
├── README.md               este documento (formato, particiones, métricas)
├── SELLADO.md              procedimiento del conjunto final sellado (vive FUERA del repo)
└── datasets/
    └── dev/                conjunto de DESARROLLO (sí está en el repo)
        └── demo.jsonl      3 casos sintéticos de la demostración
```
Ignorados por Git (`.gitignore`): `eval/datasets/test_sealed/`, `eval/sealed/`, `eval/results/`, `eval/reports/local/`, `*.sealed.jsonl`.

## 2. Formato de los casos
- **Fuente de verdad:** el contrato Pydantic `backend/antifraude/contracts/evaluation.py` (`EvalCase`). Cualquier archivo de casos se valida con él (lo hacen las pruebas).
- **Archivos JSONL** (UTF-8): un caso por línea.
- Campos principales:
  - `case_id`: `dev-NNNN` o `test-NNNN`. `split`: `dev` o `sealed_test`.
  - `origin`: `synthetic_human`, `synthetic_ai` o `adapted_licensed`. `is_synthetic` es obligatorio si el origen es sintético.
  - `author`, `created`, `review_status` (`pending_human_review` / `reviewed`), `demo_order` (orden en la demo, opcional), `tags`.
  - `message`: medio (`email`/`sms`), fecha, remitente con resultados SPF/DKIM/DMARC **declarados**, `reply_to`, asunto, `body_text` y `body_html` opcional (para enlaces cuyo texto visible no coincide con su destino).
  - `expected` (la **etiqueta**, no un resultado):
    - `risk_level`: nivel esperado.
    - `acceptable_levels`: niveles que se considerarán correctos en casos ambiguos.
    - `must_alert`: verdadero si y solo si el nivel esperado es MEDIO o ALTO.
    - `fraud_categories`.
    - `expected_quotes`: subcadenas **literales** del mensaje que una buena explicación debería citar.
    - `key_signals`: señales que justifican la etiqueta.
  - `rationale_es`: justificación en español.
- Reglas comprobadas por el contrato y las pruebas:
  - Coherencia entre nivel, alerta y categorías: un caso que debe alertar nunca acepta BAJO.
  - Citas literales.
  - Prefijo de `case_id` coherente con la partición.

## 3. Datos ficticios (obligatorio)
- Solo **dominios reservados** para ejemplos y pruebas: `.example`, `.test`, `.invalid` y `example.com/.org/.net` (RFC 2606 y RFC 6761). Entidad ficticia: **Banco Ficticio** (`bancoficticio.example`).
- Sin nombres de personas reales, teléfonos, IBAN válidos, DNI ni direcciones reales. Las pruebas lo comprueban.
- Los casos generados con IA se marcan como `synthetic_ai` y sus métricas se informarán **por separado**, por riesgo de circularidad: la IA escribe los casos y la IA los detecta (R-26).

## 4. Casos de la demostración (`dev/demo.jsonl`)
| Orden | Caso | Nivel esperado | Aceptables |
|---|---|---|---|
| 1 | `dev-0001` Aviso legítimo: extracto mensual disponible | BAJO | BAJO |
| 2 | `dev-0002` Phishing evidente: bloqueo de cuenta y petición de usuario, contraseña y código SMS | ALTO | ALTO |
| 3 | `dev-0003` Estafa sofisticada: falso gestor, enlace con texto oficial y destino ajeno, respuesta a otro dominio, DMARC fallido | ALTO | MEDIO o ALTO |
Estado: **pendientes de revisión humana** del contenido completo (`review_status`; F0-08 aprobada, D-52).

Observaciones del usuario (D-52):
- En `dev-0001`, los resultados SPF/DKIM/DMARC son **datos simulados** declarados en el caso. Por sí solos **no equivalen a legitimidad**: un remitente autenticado puede enviar un fraude, y el motor nunca debe tratarlos como excepción absoluta (CLAUDE.md §4).
- Todos los enlaces y direcciones usan **dominios reservados** (RFC 2606/6761): `.example` y `example.com/.net/.org` (documentación), `.test` (pruebas) e `.invalid`. Nunca se resuelven ni se visitan; las pruebas lo comprueban, también con un análisis estático que verifica que el backend no hace consultas DNS ni peticiones HTTP salientes.
- **No se calculan métricas de detección** hasta que exista el detector y se autorice.

## 5. Particiones
- **Desarrollo (`dev`)**: en el repo; se usa para ajustar reglas y prompts. Objetivo realista: unos 24–36 casos (60 % de 40–60; `14` §11.1).
- **Evaluación final sellada (`sealed_test`)**: **fuera del repositorio** y no consultable por los agentes durante el desarrollo (D-40). **Todavía no existe**; su ubicación está pendiente (T-14). Procedimiento: `SELLADO.md`.

## 6. Métricas previstas (cuando exista el detector)
Clase positiva = **fraude** (`expected.must_alert = true`). Predicción positiva = el sistema alerta, es decir, MEDIO o ALTO.

| Métrica | Definición | Para qué |
|---|---|---|
| Verdaderos positivos (VP) | fraudes con alerta | — |
| Falsos positivos (FP) | legítimos con alerta | coste en confianza (personas mayores) |
| Falsos negativos (FN) | fraudes sin alerta (BAJO o NO CONCLUYENTE) | riesgo para el usuario |
| **Precision** | VP / (VP + FP) | cuántas alertas son reales |
| **Recall** | VP / (VP + FN) | cuántos fraudes se detectan |
| **F1** | 2 · P · R / (P + R) | equilibrio entre ambas |
| Tasa de falsos positivos | FP / nº de legítimos | molestias a usuarios con mensajes legítimos |
| Tasa de NO CONCLUYENTE | casos NO CONCLUYENTE / total | honestidad frente a utilidad. Se informa aparte y también con una variante que la cuenta como alerta |
| Acierto de nivel | nivel obtenido ∈ `acceptable_levels` | calidad fina por caso |
| Citas | proporción de `expected_quotes` presentes en las evidencias verificadas | calidad de la explicación |
| **Latencia** | p50 y p95 del filtro y del análisis completo (ms), medidos en la máquina de la demo | experiencia de usuario |
| **Coste por mensaje** | Σ(tokens de entrada × precio de entrada + tokens de salida × precio de salida) / nº de mensajes, desde `usage` real; precios de la tabla oficial **vigente el día de la medición** | viabilidad del modelo B2B |

Reglas:
1. Comparar siempre **reglas solas frente al sistema completo**, y también Sonnet frente a Opus (D-32), con presupuesto autorizado.
2. Informar el número de casos junto a cada métrica. Con pocos casos, añadir un **intervalo de confianza de Wilson** y no extrapolar.
3. Separar los resultados de los casos `synthetic_ai` de los escritos por personas.
4. Las métricas de `dev` son de **desarrollo**. Solo las del conjunto sellado, **ejecutado una vez** y sin modificar casos después, pueden presentarse como evaluación.
5. **Nunca** presentar como real un resultado simulado ni pregrabado.
6. Los resultados se guardarán en `eval/results/` (ignorado por Git) y solo se publicarán resúmenes revisados.
