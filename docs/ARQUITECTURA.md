# Arquitectura del asistente antifraude (versión entregada)

> Resumen para el jurado. Las decisiones formales están en `docs/adr/` (ADR-0001–0015) y el detalle en `docs/contexto/13_ARQUITECTURA_TECNICA.md`.

## 1. Visión general
Aplicación **local** en un único proceso de Python 3.12 (monolito modular, ADR-0001). Escucha solo en `127.0.0.1` y no necesita Internet para analizar mensajes.

```
 Navegador (HTML + htmx local, CSP estricta)
        │  emparejamiento por código · cookie HttpOnly/SameSite=Strict · CSRF · Host/Origin
        ▼
 FastAPI (app)  ──►  Orquestador (app/pipeline.py)
                        │
   Entrada ─────────────┤  connectors: manual (texto/.eml) · simulado (etiquetado) · Gmail (preparado)
                        ▼
                  analysis/ingest   → limpieza, minimización de datos sensibles, extracción de enlaces (texto + HTML)
                  analysis/rules    → filtro rápido por reglas (señales con código estable)
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
| Enlaces sin abrir | Sin visitas, sin DNS a dominios sospechosos y sin seguir acortadores (ADR-0005). Una prueba estática lo verifica |
| La IA no decide | Aporta evidencias con **citas literales verificadas**. El nivel lo fija el motor determinista (ADR-0006/0007) |
| Mensajes = datos no confiables | Defensas frente a *prompt injection*: delimitadores aleatorios, sin herramientas ni red para el modelo, salida con esquema; los intentos de inyección cuentan como señal de riesgo |
| Privacidad | Minimización antes de guardar o usar IA. El texto de los mensajes no se guarda. Los registros no contienen códigos, cookies, tokens ni contenido |
| Accesibilidad | Español llano, texto y controles grandes, contraste ≥ 7:1, teclado, foco gestionado, icono + texto (nunca solo color) |

## 3. Contratos
Modelos Pydantic v2 en `backend/antifraude/contracts/` (fuente única, ADR-0003): `IncomingMessage`, `ScreeningResult`, `UrlAnalysis`, `AiFindings`, `Evidence`, `FraudAssessment`, `Alert`, `EvalCase`, `FinancialEntity`. Son inmutables, rechazan campos desconocidos y no repiten la entrada en los mensajes de error.

## 4. Seguridad de la aplicación local (ADR-0013)
- Emparejamiento con código de un solo uso: 8 caracteres, 5 minutos, 5 intentos con espera creciente.
- Sesión con cookie HttpOnly y SameSite=Strict, caducidad por inactividad (30 min) y absoluta (8 h).
- CSRF por cabecera; validación de Host, Origin y `Sec-Fetch-Site`; sin CORS; CSP estricta sin `unsafe-*`.
- Límite de tamaño de las peticiones y de análisis por sesión. Análisis fuera del bucle de eventos.
- Errores en español sin detalles técnicos. Las excepciones no controladas se registran sin su mensaje.

## 5. Calidad
- **674 pruebas automáticas** (contratos, seguridad, interfaz, motor, regresiones adversariales, control de gasto, IA y Gmail simulados), más 4 de integración real saltadas por defecto y 1 limitación conocida (`xfail`).
- Tres revisiones independientes con agentes de solo lectura (código, seguridad y accesibilidad), además de una revisión de etiquetas y una prueba adversarial. Cada hallazgo corregido tiene su prueba de regresión.

## 6. Qué es real, qué es simulado y qué falta
| Componente | Estado |
|---|---|
| Análisis manual, enlaces, reglas, motor, alertas e interfaz | **Real**, probado |
| Claude | Cliente completo, **probado con respuestas simuladas**, detrás de un control de gasto local (desactivado por defecto, 0 USD autorizados; `docs/CONTROL_COSTES_IA.md`). Activación pendiente del SDK y del presupuesto |
| Gmail | Conector y adaptador **probados con Gmail simulado**. OAuth pendiente |
| Bancos reales | 5 dominios web del Registro de Entidades del Banco de España, **cobertura parcial** (`docs/DOMINIOS_BANCARIOS.md`). La demo usa «Banco Ficticio» |
| RDAP y reputación | No configurados (opcionales; se declaran como no comprobados) |
| Escritorio (bandeja y notificaciones nativas) | No implementado |
| Evaluación independiente | Metodología preparada (`eval/METODOLOGIA_INDEPENDIENTE.md`); conjunto sellado pendiente |
