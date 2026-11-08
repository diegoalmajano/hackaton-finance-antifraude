# 14 — Plan de ejecución: equipo, calendario, Git, pruebas, riesgos y costes (propuesta)

> **Copia de trabajo del repositorio** (2026-11-08, sesión 5): adaptada del documento homónimo de la memoria original; referencias ajustadas para no depender de carpetas externas. Cambios marcados con «(sesión 5)».

Sesión 4 (2026-11-08). Pendiente de aprobación del usuario. Capacidad estimada: **5 personas × 3–5 h/día ≈ 15–25 h-persona/día**; del domingo 8 (tarde) al jueves 12 ≈ **60–90 h-persona** en total. Eso obliga a P0 + P1 esenciales; P2 solo si sobra.

## 1. Reparto (adaptado a perfil Python/IA)
| Persona | Módulos | Primer entregable (día 1) | Interfaz con otros |
|---|---|---|---|
| **P1 Backend y arquitectura** | contratos (dueño), B Ingestion, J Persistence, orquestador, API FastAPI + SSE, G (almacenamiento de perfil/feedback) | contratos + `/analyze` con mocks + SQLite con `user_id` | todos consumen contratos |
| **P2 IA y detección** | C Screening, E AI Analysis, F Risk Engine, K runner de evaluación | reglas v1 + cliente Claude simulado + tabla de decisión con tests | usa D y G |
| **P3 Inteligencia de amenazas** | D (URL pasivo, directorio de entidades, RDAP, reputación), L (minimización, guardas, adversariales) | normalizador de URL + `entities_es.json` con fuentes | entrega `UrlAnalysis` a F |
| **P4 Interfaz Windows** | I UI (React/TS o htmx — decide el día 0), H Notifications, bandeja, accesibilidad | **spike de escritorio (2 h)** + pantalla principal + análisis manual | API de P1 |
| **P5 Integraciones y QA** | A Gmail/OAuth, tests de integración/E2E, **custodia del test sellado**, casos de demo, README/PDF/PPTX | Google Cloud + conector con mocks; plantilla del banco | orquestador de P1 |
**Todos:** escriben **15–25 casos** del banco de pruebas cada uno (texto propio o adaptado de fuentes con licencia), con etiqueta y justificación.
Conflictos: cada persona trabaja en su carpeta de módulo; los contratos solo los modifica P1 por PR.

## 2. Calendario (hora de cierre **⏳ por confirmar** con BEST UC3M — no está publicada)
| Día | Fase | Objetivos | Criterio de salida |
|---|---|---|---|
| **Dom 8** (tarde) | **0 Auditoría y decisiones** | Aprobar MVP y ADR; crear/clonar repo; Python 3.12/3.13; estructura y contratos; spike escritorio (P4); proyecto GCP + cuenta Gmail de pruebas (P5, con autorización); directorio inicial (P3); catálogo de señales (P2); todos empiezan casos | Repo con esqueleto, contratos y `pytest` en verde; decisión de stack de UI |
| **Lun 9** | **1 Motor + 2 Enlaces** (paralelo con 3 y 4) | Normalización, filtro, Claude con mocks, motor de riesgo, URL pasivo + RDAP + reputación (mock), UI base + análisis manual, Gmail OAuth y lectura contra cuenta de pruebas | Mensaje pegado en la UI → `FraudAssessment` explicado (con mocks) |
| **Mar 10** | **3 Interfaz + 4 Gmail + 5 Integración** | Claude real sobre el **dev**; polling Gmail real → alertas preventiva/definitiva (toasts + panel); historial, feedback, sensibilidad, retención; correlación simple; adversariales; **re-autorizar Gmail** (caducidad 7 días) | **E2E real**: correo enviado → alerta en el escritorio |
| **Mié 11** | **5 Integración y estabilización + 6 Presentación** | **Congelación de funcionalidades a las 14:00**; ejecutar **una vez** el test sellado (con autorización de coste); métricas; guion de demo y ensayo; README, PDF de una cara, PPTX; ZIP desde GitHub probado en carpeta limpia (y a ser posible en otro PC) | Entregables completos en el repo |
| **Jue 12** | Entrega | Solo correcciones críticas; envío por el formulario oficial **antes del cierre**; presentación | Entrega enviada |
Reserva: ≥30 % del tiempo de los días 10–11 para integración y pruebas. Nada nuevo tras la congelación.

## 3. Procedimiento por fase (aplicable por Claude Code)
Plan → Contrato → Código → Pruebas → Revisión → Documentación (`08`) → **Aprobación** del usuario antes de la siguiente fase importante. Informes con estados: **Implementado · Probado · No probado · Bloqueado · Simulado · Pendiente**.

## 4. Git y trabajo paralelo
- `main` protegida (solo PR con ≥1 revisión y tests en verde). Ramas `feat/<modulo>-<tema>`, `fix/...`, `docs/...`. PR pequeños y frecuentes (≥1 al día por persona).
- Prohibido: force-push, borrar ramas, reescribir historial, subir secretos. Claude Code **pide autorización** antes de cualquier operación remota (push, PR) y no toca trabajo de otros sin revisión.
- `.gitignore` desde el primer commit (`.env`, `client_secret*.json`, `*.db`, `eval/datasets/test_sealed/` si se decide mantenerlo fuera del repo ⏳).
- Estado actual (sesión 6): repositorio **independiente** `hackaton-finance-antifraude` (rama `main`, primer commit local, remoto `origin` accesible y vacío, push pendiente). Traslado fuera de la carpeta original: ✅ hecho (D-23).

## 5. Estrategia de pruebas
**Banco de evaluación (K):** objetivo ≥150 casos en 10 tipos: legítimos (incl. urgentes legítimos y con faltas), phishing evidente, sofisticado, suplantación bancaria, robo de credenciales, pagos fraudulentos (cambio de IBAN/«CEO»), ambiguos, enlaces engañosos, variaciones adversariales, manipulación del agente. Origen marcado por caso: `humano` / `adaptado_de_fuente_con_licencia` / `generado_con_IA` (este último reportado aparte). Partición **dev (60 %) / test sellado (40 %)** que custodia P5; P2 y P3 ajustan **solo** con dev; el test se ejecuta al final, sin modificar casos para mejorar métricas.
**Métricas:** fraudes detectados (TP), falsas alarmas (FP), fraudes no detectados (FN), proporción de alertas correctas (precisión), recall, F1, tasa de NO CONCLUYENTE, latencia filtro y análisis profundo (p50/p95), coste por mensaje (desde `usage`), fallos de API. Matriz de confusión por nivel (MEDIO/ALTO cuentan como alerta). Comparativa: reglas solas vs sistema completo.
**Por módulo:** unitarias (URL, homoglifos, directorio, reglas, tabla de decisión de F, enmascarado, verificación de citas, aislamiento por `user_id`, reversibilidad de reglas); integración con mocks (Gmail falso, Anthropic falso, respx para RDAP/reputación); E2E (fixtures → evaluación → notificación); adversariales; humo del ZIP.
**Coste de pruebas reales:** las ejecuciones con Claude real del banco completo se piden con autorización y presupuesto.

## 6. Criterios de aceptación (no basta con que exista el código)
| Funcionalidad | Aceptada cuando… |
|---|---|
| Gmail | un correo enviado a la cuenta de pruebas autorizada se recibe y analiza automáticamente; desconectar revoca y borra el token |
| Motor de riesgo | en dev, clasificación y evidencias coherentes; tests de la tabla de decisión; errores nunca dan BAJO |
| URL | dominio registrable, lookalikes, discrepancia texto/destino y acortadores correctos en los casos de prueba; ninguna petición a la URL sospechosa (verificado con mocks/red) |
| Notificaciones | preventiva y definitiva distinguibles y en orden; la definitiva siempre cierra una preventiva |
| Interfaz | flujo completo con teclado; textos sin tecnicismos; riesgo con texto + icono; contraste verificado |
| Personalización | aislamiento entre dos `user_id`; «falsa alarma» reversible; no suprime señales críticas |
| App Windows | inicio, bandeja, pausa, salida limpia (sin procesos huérfanos); autoarranque desactivado por defecto |
| Integración final | mensaje de prueba procesado de extremo a extremo en la máquina de la demo |

## 7. Registro de riesgos (sin probabilidades numéricas)
| Riesgo | Impacto | Causa | Mitigación | Alternativa | Resp. | Estado |
|---|---|---|---|---|---|---|
| OAuth Google bloqueado/lento | Alto | Configuración GCP, app no verificada | Empezar el día 0; usuarios de prueba; guía paso a paso | Conector simulado **etiquetado** + importar .eml | P5 | Abierto |
| Token Gmail caduca (Testing, 7 días) | Medio | Política de Google | Re-autorizar el 10–11 | — | P5 | Abierto |
| Correos de prueba a SPAM | Bajo | Filtros Gmail | Analizar también SPAM | — | P5 | Abierto |
| Stack de escritorio falla | Alto | pywebview/pystray/Python 3.14 | Spike día 0; Python 3.12/3.13 | Navegador + bandeja; Electron | P4 | Abierto |
| Retraso de integración | Alto | Paralelismo, contratos cambiantes | Contratos el día 0; integración diaria; congelación | Recortar P1 | P1 | Abierto |
| Falsos positivos | Alto (UX mayores) | Reglas agresivas | Ajuste en dev; sensibilidad; legítimos urgentes en el banco | — | P2 | Abierto |
| Falsos negativos | Alto | Fraudes sofisticados | IA contextual; correlación; casos sofisticados | Mostrar incertidumbre | P2 | Abierto |
| Prompt injection | Alto | Contenido del atacante | 10 defensas (`13` §10) | — | P3 | Abierto |
| Refusals del modelo con contenido de phishing | Medio | Clasificadores de seguridad | Manejo de `refusal` → NO CONCLUYENTE; fallback | Reglas | P2 | Abierto |
| Filtración de datos | Alto | Logs, tokens, envío a nube | Minimización, keyring, logs sin contenido | — | P3 | Abierto |
| Errores de URL | Medio | Parseo complejo | PSL local, tests | — | P3 | Abierto |
| Problemas de Git | Medio | 5 personas en paralelo | Ramas por módulo, PR pequeños | — | P1 | Abierto |
| Costes elevados | Bajo | Ejecuciones repetidas | Mocks; límite de gasto en consola; registro de `usage` | — | P2 | Abierto |
| Falta de tiempo | Alto | 3–5 h/día | P0 primero; congelación miércoles 14:00 | Recortar P1/P2 | Todos | Abierto |
| API externa caída en la demo | Alto | Red/servicio | Modo **sin IA real etiquetado** (reglas + técnica, IA «no disponible» → análisis parcial); sin resultados pregrabados | — | P5 | Abierto |
| Pérdida de puntos en IA frontera por no usar audio | Medio | Voz aplazada | Medir impacto en accesibilidad/comprensión | Revisar con el usuario | Equipo | Aceptado por el usuario |
| Hora de cierre desconocida | Alto | No publicada | Preguntar hoy | Planificar entrega el miércoles noche | Equipo | Abierto |

## 8. Costes estimados (a sustituir por medidos)
Precios oficiales ✅: Sonnet 5.5 $2 entrada / $10 salida por M tokens (lectura de caché $0,20); Haiku 5.5 $0,10 / $0,50.
Supuestos ⚖ por análisis profundo: ~3 500 tokens de entrada (≈1 500 de prompt de sistema cacheable) y ~1 000–2 000 de salida (JSON + razonamiento facturado como salida).
- Análisis profundo con Sonnet 5.5: **≈ 0,02 $** (rango 0,015–0,03 $).
- Filtro con reglas: 0 $; con Haiku 5.5 opcional: **≈ 0,0002 $**.
- Una ejecución del banco completo (~150 casos, ~60 % escalados): **≈ 2 $**; diez ejecuciones ≈ 20 $.
- Si se eligiera `claude-opus-5-5` ($4/$20 ✅), con los mismos supuestos el coste por análisis sería aproximadamente el doble (≈ 0,04 $; **estimación, a medir**; D-24, sesión 5).
- Orientativo producto: usuario con 40 correos/día y 10 % escalados ≈ 0,08 $/día ≈ **2,4 $/mes** de inferencia → dato clave para el precio B2B (a medir).
Controles: límite de gasto en la consola de Anthropic, registro de `usage` por análisis, mocks en tests, autorización antes de ejecuciones masivas.

## 9. Entregables (contrastados con el PDF oficial)
Repo GitHub (público o compartido) · **ZIP descargado de GitHub** (versión oficial) · README (descripción, requisitos, instalación, configuración, ejecución, **prueba**) · PDF de una cara (problema, solución, valor diferencial) · PowerPoint · formulario oficial de BEST UC3M · demo = versión entregada.

## 10. Primera fase de programación recomendada (tras aprobación)
**Fase 0 técnica (domingo):** usar el repo independiente ya creado (sesión 5) · fijar Python · esqueleto del monolito · **contratos Pydantic** + tests de validación · `.gitignore`/`.env.example` · spike de escritorio · plantilla del banco de pruebas · ADR 001–011 en `docs/adr/`. Después, **Fase 1: motor de análisis** (normalización → filtro → URL pasivo → Claude con mocks → motor de riesgo) con análisis manual desde la API.
