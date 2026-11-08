# 02 — Hackatón: rúbrica, requisitos y entregables

> Adaptado (sesión 5) del documento homónimo de la memoria original. Fuente única y oficial: el PDF del hackatón; su **texto literal** está en `../referencia/rubrica_oficial_texto.md`. Todo lo de este documento es ✅ PDF salvo que se indique.

## 1. Rúbrica completa (suma 100 %)
| # | Criterio | Peso | Qué evalúa literalmente |
|---|---|---:|---|
| 1 | **Innovación y viabilidad** (Topic Abierto) | **30 %** | Problema real del mundo de las finanzas · solución técnica útil y aplicable · **viable financieramente** · factor novedoso y competitivo respecto a soluciones existentes en el mercado |
| 2 | **Uso de capacidades de IA frontera** | **15 %** | IA frontera aporta valor diferencial · se apoya en **tecnologías de lenguaje y audio avanzado** y genera **impacto medible** en usabilidad, interactividad o accesibilidad |
| 3 | **Experiencia de usuario y accesibilidad** | **15 %** | Interfaz visual clara, funcional e intuitiva · tiempos de respuesta razonables |
| 4 | **Implementación técnica y de código** | **30 %** | Solución **acabada, madura y funcional, lista para ejecutar** |
| 5 | **Presentación ante jurado** | **10 %** | Explicación clara de problema, solución y arquitectura · transmitir impacto y valor diferencial · buena gestión del tiempo y respuestas precisas |

Lectura (⚖ asistente): el 60 % se decide entre «¿novedoso y viable?» y «¿funciona y se puede ejecutar?». El 15 % de IA frontera nombra **audio** y exige **impacto medible**. Como la voz está aplazada (D-12), ese criterio se defiende con lenguaje + impacto medible en accesibilidad/comprensión (riesgo aceptado; `14` §7).

## 2. Entregables obligatorios (dentro del plazo, vía formulario oficial de BEST UC3M)
1. **Enlace al repositorio GitHub** (público o compartido con quien indique la organización).
2. **ZIP del proyecto** descargado desde GitHub (*Code → Download ZIP*). **El ZIP es la versión oficial evaluada**, aunque el repo se actualice después.
3. **README.md** en el repo **y** en el ZIP: descripción breve, requisitos, instalación, configuración, ejecución y **prueba**.
4. **PDF de una cara**: problemática resuelta, solución propuesta y **valor diferencial**.
5. **Presentación PowerPoint** que se vaya a usar ante el jurado.

## 3. Reglas
- Se puede **sustituir** la entrega hasta el cierre; se evalúa la **última entrega completa** recibida en plazo. Tras el cierre, nada.
- Presentación: **formato libre**; diapositivas opcionales; **si se hace demo, debe corresponder a la versión entregada**.
- El jurado aplica la rúbrica de la página 1.

## 4. Lo que el PDF NO dice (⏳ confirmar con BEST UC3M)
- **Fecha y hora exactas del cierre de entrega** (el PDF solo dice «cierre del plazo»). El 12-nov procede del equipo (💬). Búsqueda web de la sesión 4: no publicada.
- Duración de la presentación y formato de preguntas; URL del formulario; datos/APIs que facilite la organización.
- **Tensión interna**: «diapositivas opcionales» vs PowerPoint listado como entregable → **entregar el PowerPoint siempre** (P-04).

## 5. Implicaciones directas para el diseño
- Priorizar **un flujo completo, pulido y reproducible** (30 % implementación + 15 % UX).
- El **README debe permitir ejecutar y probar** desde cero; probar el ZIP descargado en una carpeta limpia antes de enviar.
- Medir algo con **impacto medible** (15 %): detección/falsas alarmas en el banco de pruebas, comprensión de las alertas por personas mayores, latencia.
- Viabilidad financiera (30 %): explicar quién paga (bancos, modelo B2B, `11` §3) y el coste de inferencia medido (`14` §8).
- La **demo = versión entregada**: congelar commit antes de ensayar.
