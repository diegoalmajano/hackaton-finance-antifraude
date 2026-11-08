# 11 — PRODUCTO: asistente de IA para prevenir estafas financieras en mensajes (v2.0)

> **Copia de trabajo del repositorio** (2026-11-08, sesión 5): adaptada del documento homónimo de la memoria original; referencias ajustadas para no depender de carpetas externas. Cambios marcados con «(sesión 5)».

**Fuente:** «Prompt maestro definitivo v2.0» del usuario (2026-11-08, sesión 4). Sustituye a la v1 de la sesión 3 (que incluía voz, índice 0–100 y entidad ficticia). Arquitectura técnica y contratos: `13_ARQUITECTURA_TECNICA.md`. Plan, equipo, riesgos, tests: `14_PLAN_EJECUCION.md`. Límites por plataforma y fuentes: `12_VIABILIDAD_PLATAFORMAS.md`.
Estado: **idea aprobada (D-09); arquitectura APROBADA con modificaciones (D-26, sesión 6; `docs/adr/`)**; Fase 0 aprobada (D-38) y en curso por etapas. Modelo de Claude pendiente (D-24, D-32). ~~arquitectura e implementación pendientes de aprobación (D-10, D-25)~~ (histórico).

## 1. Identidad
**Asistente de IA que previene estafas financieras en mensajes y comunicaciones digitales escritas.** Capa de protección personal: el usuario autoriza canales y el agente analiza **proactivamente** los mensajes nuevos que puede recibir legal y técnicamente.
Flujo: detectar mensaje → filtro rápido → señales → **alerta preventiva** (si procede) → investigar contenido, enlaces y remitente → riesgo con evidencias verificables → **alerta definitiva** comprensible → recomendación segura → **decisión del usuario** → personalización individual controlada con sus correcciones.
El verificador fiscal queda descartado (histórico).

## 2. Alcance de esta fase
**Sí:** correos, mensajes escritos, SMS por vías legales (importar/compartir), mensajería compatible, enlaces sospechosos, suplantación de entidades financieras, phishing, robo de credenciales, ingeniería social escrita, **fraudes en varios mensajes**, personalización individual, notificaciones y explicaciones.
**NO (fase 2, no implementar ni instalar nada):** llamadas, videollamadas, micrófono, transcripción, voz, agentes de voz, deepfakes de voz. Solo se deja un **adaptador de entrada genérico** para que un futuro módulo de voz envíe eventos al motor común.
⚠ Nota de rúbrica (⚖): el criterio de IA frontera (15 %) menciona «lenguaje **y audio**». Sin audio, ese 15 % se defiende con lenguaje y con **impacto medible en accesibilidad** (p. ej. prueba de comprensión de las alertas con personas mayores). Riesgo aceptado por el usuario al aplazar la voz; registrar en riesgos.

## 3. Público y modelo de negocio
- **Protegidos:** cualquier persona; foco en mayores, vulnerables a ingeniería social, poca experiencia digital, clientes bancarios.
- **Modelo B2B:** cliente comercial = **entidad financiera española**; usuario final = cliente protegido. Futuro: app **white-label** distribuida por el banco con su marca.
- **Fuera del hackatón:** panel de bancos, multiempresa, sistema comercial B2B.
- **Datos y bancos:** el banco **no** recibe mensajes personales; solo alertas concretas que el usuario comparta expresamente (requisito futuro).
- **GPTadvisor:** sin integración oficial (no afirmarla). Posible complemento como capa de protección de clientes de entidades; el producto es independiente.
- Encaje regulatorio orientativo (⏳ no es asesoramiento): el AI Act excluye de la categoría de alto riesgo de solvencia (anexo III 5.b) los sistemas para **detectar fraude financiero**; los comentaristas lo leen de forma estricta (no cubre acciones automáticas aguas abajo). Nuestro sistema **no actúa**: solo informa.

## 4. Principios obligatorios
Consentimiento por canal · mínimo privilegio · detección proactiva donde la plataforma lo permita · análisis por etapas (filtrar antes de usar modelos avanzados) · explicabilidad (motivos + evidencias) · reconocer incertidumbre · personalización individual sin compartir aprendizajes entre usuarios · decisión humana · privacidad (minimizar lo enviado, procesado y conservado) · accesibilidad para mayores · todo mensaje y enlace = **dato no confiable**.

## 5. MVP (12-nov) — prioridades
**Flujo a demostrar:** recepción de un mensaje → filtro → alerta preventiva → investigación → evaluación → notificación final → decisión del usuario. **(Sesión 6, D-34) La demo principal no depende de Gmail:** funciona con análisis manual y, como respaldo, con conectores simulados **etiquetados**. La recepción **real** por Gmail sigue siendo una integración **prioritaria** (fase f, D-28) y se mostrará si está disponible.
### P0 imprescindibles
1 Motor de análisis de texto · 2 extracción y normalización de enlaces · 3 filtro rápido · 4 análisis contextual con IA · 5 motor de riesgo explicable · 6 niveles **BAJO / MEDIO / ALTO / NO CONCLUYENTE** · 7 alertas preventiva y definitiva · 8 interfaz en español · 9 análisis manual · 10 pruebas automatizadas · 11 demo reproducible (legítimos y fraudulentos).
### P1 prioritarias
1 **Gmail real** · 2 recepción automática de cuenta autorizada · 3 app Windows con **bandeja** · 4 notificaciones nativas · 5 entidades financieras configurables · 6 sensibilidad configurable · 7 historial · 8 feedback individual · 9 políticas de borrado · 10 inicio con Windows **opcional, desactivado por defecto**.
+ (⚖ propuesto como P1 porque está en el alcance) **correlación simple** entre mensajes del mismo usuario.
### P2 solo si el MVP está estable
Segundo canal automático · correlación avanzada entre canales · importar capturas · extracción segura de adjuntos · personalización avanzada · inspección aislada de páginas · empaquetado sofisticado. (Adjuntos/imágenes: preparados en la arquitectura, no implementados.)
Si Google bloquea OAuth: documentar, mantener conector simulado **comprobable y etiquetado**, proponer alternativa. **Nunca** presentar un simulado como real.

## 6. Experiencia Windows y accesibilidad
Bandeja: abrir panel, estado de protección, activar/pausar, integraciones, alertas, resultados, análisis manual, preferencias, salir. Inicio con Windows solo si el usuario lo activa.
Diseño para mayores: solo español, texto grande, botones grandes, alto contraste, pocos elementos, teclado, estados claros, confirmación de acciones importantes, **sin tecnicismos** (DNS, SPF, TLS) en la explicación principal (detalle técnico secundario), **riesgo con texto + icono, no solo color**.
Pantalla principal: protección on/off · canales · últimas alertas · botón «Analizar un mensaje» · configuración · historial.
Acciones en una alerta: ver explicación · ver evidencias · «Es una falsa alarma» · «Reportar fraude» · vías oficiales de verificación (solo datos de contacto **verificados** del directorio; nunca inventar teléfonos). Nunca abrir enlaces sospechosos ni ejecutar acciones financieras.

## 7. Alertas en dos fases
- **Preventiva** (si el filtro detecta riesgo relevante según sensibilidad): «Posible intento de fraude. Hemos encontrado elementos sospechosos en un correo que parece proceder de tu banco. Estamos comprobándolo.»
- **Definitiva**: nivel + motivos + recomendaciones; si alguna comprobación falló → «análisis parcial». **Un error de API nunca se convierte en BAJO.** Si hubo alerta preventiva, siempre se cierra con una definitiva (también si resulta BAJO: «Lo hemos comprobado y no hemos encontrado indicios»), para no dejar al usuario con la duda.

## 8. Riesgo: tres conceptos separados
1 **Nivel** (BAJO/MEDIO/ALTO/NO CONCLUYENTE) · 2 **Evidencias** (cada una con su fuente: regla, inteligencia técnica, IA, perfil, correlación) · 3 **Incertidumbre** (comprobaciones no realizadas o fallidas, dudas del análisis). No se muestran porcentajes. Una probabilidad 0–100 % exigiría datos etiquetados representativos, modelo, calibración, evaluación independiente y métricas de fiabilidad (ver `13` §6.4).
Sensibilidad configurable **sin** desactivar controles críticos (p. ej. petición evidente de credenciales). Un remitente marcado como legítimo **nunca** es una excepción absoluta.

## 9. Inteligencia de enlaces y directorio de entidades
Análisis de dominio real, subdominios, URL normalizada, acortadores, caracteres engañosos, parecidos a marcas, reputación, evidencias de phishing, redirecciones (solo si se verifican de forma segura), suplantación bancaria y falsas pasarelas.
**Directorio de entidades** seleccionables por el usuario con **dominios oficiales verificados** (fuente y fecha documentadas), nunca construido a partir de lo que dicen los mensajes. Se distingue: identidad declarada · identidad verificada · dominio oficial · dominio encontrado · resultado de comparación. Un dominio oficial **no** garantiza la legitimidad de todo el contenido.
**MVP: solo análisis pasivo** (no se visita ninguna página): no podemos garantizar en 4 días un aislamiento robusto frente a SSRF, DNS rebinding y descargas (ver `13` §7). La inspección aislada es P2.

## 10. Personalización individual (diferenciador)
Fuentes: bancos seleccionados, preferencias, sensibilidad, correcciones, historial autorizado, remitentes habituales (con autorización).
Progresiva: preferencias y feedback → reglas individuales limitadas. **Sin fine-tuning**; nunca datos privados para un modelo compartido.
Antimanipulación: correcciones ≠ permisos absolutos; reglas reversibles con **procedencia** registrada; controles de alto riesgo siempre prevalecen; borrado total de la personalización; separación estricta entre usuarios.

## 11. Correlación entre mensajes
Detectar fraudes en varias comunicaciones (verificar cuenta → enlace → presión para credenciales). Indicadores: remitente, dominio, conversación, entidad mencionada, referencias compartidas, proximidad temporal, similitud contextual. **No** atribuir automáticamente mensajes distintos al mismo fraude: el MVP solo **añade una evidencia** «relacionado con una alerta previa» con criterios simples y verificables (mismo dominio/hilo/entidad en una ventana temporal). Entre canales: requiere autorización (P2).

## 12. Demostración (3 casos reproducibles)
1. **Correo legítimo** de pruebas → sin alerta injustificada.
2. **Estafa evidente**: supuesto banco pide verificar credenciales con urgencia mediante enlace sospechoso → detecta, alerta, investiga el enlace, identifica suplantación, resultado explicado, actuación segura.
3. **Estafa sofisticada**: correo profesional convincente pide una actuación financiera con incoherencias de identidad o enlaces (p. ej. texto visible del enlace = dominio oficial pero destino distinto; nombre mostrado de banco con dirección de otro dominio; cambio de cuenta de pago) → evidencias sin depender de faltas de ortografía; si faltan datos, **NO CONCLUYENTE**.
Objetivo: al menos uno con **recepción real vía Gmail** si la integración está disponible (prioritaria, pero **no requisito** de la demo principal, D-34). Nada pregrabado presentado como ejecución real; lo simulado, siempre etiquetado.

## 13. Definición de éxito
Un usuario conecta un canal permitido → recibe un mensaje → análisis automático → indicios → alerta preventiva → investigación de contenido y enlaces → evaluación explicada → evidencias → **qué no se pudo comprobar** → decide el usuario. Comprensible para una persona mayor. Sin afirmar detectar todo, sin porcentajes de eficacia inventados, sin simulaciones como reales, sin datos personales no autorizados.

## 14. Fase 2 (aplazada, no implementar)
Asistente de voz para llamadas/videollamadas autorizadas (audio, transcripción, ambos interlocutores si es legal, ingeniería social progresiva, alertas, correlación con mensajes). Ver límites ya investigados en `12` §1 (llamadas). Solo se garantiza la compatibilidad mediante el adaptador de entrada (`13` §3).
