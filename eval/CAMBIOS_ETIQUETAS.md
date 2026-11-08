# Registro de cambios de etiquetas (conjunto de desarrollo)

> Regla: una etiqueta solo se cambia por una incoherencia **con el contenido del mensaje o con la política** (ADR-0006, D-29), nunca para que coincida con lo que devuelve el detector. Cada cambio queda registrado aquí.

## 2026-11-08 — Revisión independiente de los 27 casos
Revisor: subagente sin acceso al código ni a los resultados del detector (solo leyó los casos, el contrato `EvalCase`, `eval/README.md`, ADR-0006 y `11` §7–§12). Resultado: 24 casos correctos y 3 cambios justificados. El nivel esperado de ningún caso ha cambiado.

| Caso | Antes | Después | Justificación |
|---|---|---|---|
| dev-0009 | Señales y justificación basadas en que «el usuario acaba de solicitar el código» | Señales que se sostienen con el texto: entrega el código, advierte de no compartirlo y no pide nada. Nivel BAJO sin cambios | La etiqueta no debe depender de un contexto que no está en el mensaje |
| dev-0015 | `fraud_categories`: payment_fraud, phishing_link, bank_impersonation | payment_fraud, phishing_link | Su propia señal dice «remitente genérico sin identificar la entidad», y Bizum no es un banco |
| dev-0027 | `acceptable_levels`: NO CONCLUYENTE, BAJO, MEDIO | NO CONCLUYENTE, MEDIO | La justificación y las señales recogen tres indicios. BAJO («sin indicios») las contradice |

## Cambio de método asociado
- Los casos con nivel esperado **NO CONCLUYENTE** (dev-0024, 0025, 0027) ya no cuentan como «legítimos» en la precisión ni en la tasa de falsos positivos. Se informan aparte: nivel aceptable y si hubo alerta. Antes, un MEDIO aceptado en esos casos se contaba como falso positivo.
- Convención: las categorías de fraude **no se evalúan** en los casos NO CONCLUYENTE.

## Discutibles que no se han cambiado
- **dev-0025:** acepta 3 de los 4 niveles, así que mide poco.
- **dev-0014 y dev-0018:** aceptan MEDIO pese a pedir claves o tarjeta en un dominio ajeno (defendible según ADR-0006).
- **dev-0015:** podría aceptar también MEDIO.
- **dev-0016:** fraude de factura entre empresas, poco realista para el usuario final. La etiqueta «fraude_del_ceo» es inexacta: es fraude de proveedor.
- **dev-0017:** `credential_theft` es discutible (el código es de acceso remoto, no una credencial bancaria).
- **dev-0010, 0025 y 0027:** correos sin asunto.
Quedan para la **revisión humana** (R-47).
