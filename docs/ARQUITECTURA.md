# Arquitectura del asistente antifraude (versión local actual)

> Resumen para el jurado. Las decisiones formales están en `docs/adr/` (ADR-0001–0015) y el detalle en `docs/contexto/13_ARQUITECTURA_TECNICA.md`.

## 1. Visión general
Aplicación **local** en un único proceso de Python 3.12 (monolito modular, ADR-0001). Escucha solo en `127.0.0.1` y el análisis manual funciona sin Internet ni SDK de Google o Anthropic. Las integraciones externas son opcionales y requieren autorización.

```
 Navegador (HTML + htmx local, CSP estricta)
        │  emparejamiento por código · cookie HttpOnly/SameSite=Strict · CSRF · Host/Origin
        ▼
 FastAPI (app)  ──►  Orquestador (app/pipeline.py)
                        │
   Entrada ─────────────┤  connectors: manual (texto/.eml) · simulado (etiquetado) · Gmail (integrado en panel, apagado por defecto)
                        ▼
                  analysis/ingest   → limpieza, minimización de datos sensibles, extracción de enlaces (texto + HTML)
                  analysis/rules    → rules-0.3.5, filtro rápido (señales con código estable)
                  intel/urls        → análisis PASIVO de enlaces + intel/entities (directorio de bancos)
                  ai/claude         → (opcional) Claude con salida JSON estricta y citas verificadas
                  risk/engine       → motor DETERMINISTA: BAJO / MEDIO / ALTO / NO CONCLUYENTE
                        │
                        ▼
                  Alertas: preventiva → definitiva (con evidencias, incertidumbres y recomendaciones)
```

## 2. Principios de diseño
| Principio | Cómo se cumple |
|---|---|
| El usuario decide | El sistema solo informa: no paga, no responde y no abre nada |
| Sin porcentajes inventados | 4 niveles. Nivel, evidencias e incertidumbre separados (D-14) |
| Un error nunca da «BAJO» | Las comprobaciones obligatorias que fallan llevan a «análisis parcial». El contrato `FraudAssessment` lo impide por construcción |
| Petición de claves u OTP = nunca seguro | Mínimo MEDIO, aunque venga de un dominio aparentemente oficial (D-29) |
| Enlaces sin abrir | Sin visitas, sin DNS a dominios sospechosos y sin seguir acortadores (ADR-0005). Hay regresiones con red y DNS bloqueados |
| La IA no decide | Aporta evidencias con **citas literales verificadas**. El nivel lo fija el motor determinista (ADR-0006/0007) |
| Mensajes = datos no confiables | Defensas frente a *prompt injection*: delimitadores aleatorios, sin herramientas ni red para el modelo, salida con esquema; los intentos de inyección cuentan como señal de riesgo |
| Privacidad | Minimización antes de guardar o usar IA. El texto de los mensajes no se guarda. Los registros no contienen códigos, cookies, tokens ni contenido |
| Accesibilidad | Español llano, controles grandes, foco gestionado e icono + texto. Diseño bosque/crema con reflujo 320 px comprobado y teclado parcial; zoom 200 % del diseño actual, Narrador, contraste elevado y recorrido manual completo pendientes |

## 3. Contratos
Modelos Pydantic v2 en `backend/antifraude/contracts/` (fuente única, ADR-0003): `IncomingMessage`, `ScreeningResult`, `UrlAnalysis`, `AiFindings`, `Evidence`, `FraudAssessment`, `Alert`, `EvalCase`, `FinancialEntity`. Son inmutables, rechazan campos desconocidos y no repiten la entrada en los mensajes de error.

## 4. Seguridad de la aplicación local (ADR-0013)
- Emparejamiento con código de un solo uso: 8 caracteres, 5 minutos, 5 intentos con espera creciente.
- Sesión con cookie HttpOnly y SameSite=Strict, caducidad por inactividad (30 min) y absoluta (8 h).
- CSRF por cabecera; validación de Host, Origin y `Sec-Fetch-Site`; sin CORS; CSP estricta sin `unsafe-*`.
- Límite de tamaño de las peticiones y de análisis por sesión. Análisis fuera del bucle de eventos.
- Errores en español sin detalles técnicos. Las excepciones no controladas se registran sin su mensaje.

## 5. Calidad
- **926 pruebas Python automáticas** (contratos, seguridad, interfaz, motor, regresiones adversariales, control de gasto, IA y Gmail simulados), más 4 de integración real saltadas por defecto, 1 limitación conocida (`xfail`) y 1 aviso de deprecación. Se registran por separado 11 pruebas JavaScript y 8 comprobaciones de SDK con transportes HTTP/OAuth/keyring simulados; estas últimas no acreditan una cuenta real.
- Revisiones asistidas de código, seguridad, accesibilidad y etiquetas, además de pruebas adversariales y regresiones. Se distinguen de la evaluación independiente, cuyo conjunto sellado sigue pendiente.

## 6. Qué es real, qué es simulado y qué falta
| Componente | Estado |
|---|---|
| Análisis manual, enlaces, reglas, motor, alertas e interfaz | **Real**, probado |
| Claude | Cliente **probado con respuestas simuladas**, detrás de un control de gasto local (IA desactivada, 0 USD autorizados; `docs/CONTROL_COSTES_IA.md`). Sin llamadas reales; activación pendiente de autorización de SDK, clave y presupuesto |
| Gmail | Conector, sondeo, consentimiento de sesión, avisos y desconexión integrados en el panel, **probados con Gmail simulado**. SDK comprobados con servicios HTTP/OAuth/keyring simulados. Real apagado (`APP_GMAIL_ENABLED=0`); OAuth, cuenta de pruebas y extremo a extremo real pendientes |
| Bancos reales | 5 dominios web del Registro de Entidades del Banco de España, **cobertura parcial** (`docs/DOMINIOS_BANCARIOS.md`). La demo usa «Banco Ficticio» |
| RDAP y reputación | No configurados (opcionales; se declaran como no comprobados) |
| Escritorio (bandeja y notificaciones nativas) | No implementado |
| Evaluación independiente | Metodología preparada (`eval/METODOLOGIA_INDEPENDIENTE.md`); conjunto sellado pendiente |


## 7. Integraciones opcionales y alcance de verificación
- Gmail no se conecta al arrancar: además de la configuración externa, el panel exige el consentimiento de la sesión. La recepción pasa por normalización y el pipeline común; en el flujo Gmail actual no se envían los correos a una IA externa. Las alertas conservan explicaciones y recomendaciones, sin cuerpos completos; la desconexión y la caducidad retiran el acceso de esa sesión. El borrado local del permiso no equivale a revocación remota en Google.
- La instalación manual base usa `requirements.lock`. El bloqueo opcional `requirements-gmail.lock` reúne 53 versiones, incluidas las de base, comprobadas únicamente en Windows/Python 3.12; no es una dependencia obligatoria del análisis manual. La instalación temporal autorizada y las 8 comprobaciones de SDK no sustituyen OAuth real ni autorizan instalaciones en otros entornos.
- El reflujo a 320 px se comprobó en los cuatro niveles y Gmail simulado. La confirmación humana previa de zoom 200 % pertenece al diseño anterior; no demuestra el resultado del diseño actual. Accesibilidad manual y evaluación independiente permanecen identificadas como pendientes.
