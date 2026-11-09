# Diseño del MVP — dirección y criterios previos, 09-11-2026

Tras estabilizar detector, gasto y unión Gmail simulada, se aborda G/H del plan. Gmail real y evaluación humana siguen pendientes sin bloquear el resto. Nombre definitivo sin decidir: se conserva «Asistente antifraude».

Dirección: una pausa tranquila antes de actuar. Interfaz editorial sobria, verde profundo y papel cálido, superficies claras y jerarquía amplia. Un escudo lineal local identifica el producto, sin imágenes externas, fuentes remotas ni servicios adicionales. Titular serif local y cuerpo Segoe UI familiar/legible en Windows; prioridad a lectura de mayores frente a tipografías de moda. Sin animaciones decorativas.

Criterios antes de modificar:
- Una acción primaria por pantalla: Empezar, Conectar o Analizar. Estado técnico, guía de niveles y Gmail opcional en segundo plano; ningún falso resultado decorativo.
- Formulario manual y resultado prioritarios; riesgo con texto/icono/borde, motivo y acción comprensible. Análisis parcial visible; detalles técnicos accesibles por desplegable. No ocultar errores ni restricciones.
- Conservar IDs, etiquetas, ayudas, foco, CSRF, htmx sin eval, sesión y CSP. SVG local pasivo, sin scripts. No audio.
- Base18–20px, controles>=48px, reflujo320 y zoom200%, sin barra horizontal, foco visible y respeto a movimiento reducido. Contraste calculado de pares nuevos y comprobación en navegador; no declarar Narrador ni temas Windows superados.
- Prueba funcional real del análisis tras el cambio; comparar cuatro niveles, errores/archivo/espera/cierre y cabeceras. Reconciliar materiales tras fijar versión.

Skills: frontend-design y guías ui-ux-pro-max. El buscador auxiliar de esta última no está incluido en la instalación local (los punteros scripts/data remiten a recursos ausentes); se aplican sus reglas locales de jerarquía, accesibilidad y formularios sin instalar nada.

## Verificación final

IAB: bienvenida y formulario a 1440×1000; reflujo de los cuatro niveles a 320×800 (clientWidth/scrollWidth 305/305). Importación .eml, prioridad, validación, foco y detalles probados; flujo Gmail SIMULADO con consentimiento, estado estable y desconexión probado. Sin infracciones CSP observadas. Capturas locales de bienvenida, NO CONCLUYENTE y Gmail simulado. Zoom real 200 % del nuevo diseño, contraste elevado y lector/manual completo no verificados; evidencia previa de zoom pertenece al diseño anterior. No conformidad WCAG general.

Contraste calculado por luminancia sRGB en 17 combinaciones de texto de la paleta final: mínimo 6.86:1, todas ≥4,5:1. No comprueba colores forzados de Windows, percepción, todos los estados ni conformidad WCAG general.
