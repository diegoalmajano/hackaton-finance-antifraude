# Verificación automática de accesibilidad — 09-11-2026

> Hecha por un compañero del equipo con Claude, en Linux con Chromium sin interfaz (Playwright) y axe-core 4.10.2 (reglas WCAG 2.0/2.1/2.2 A y AA + buenas prácticas), contra `127.0.0.1` en modo demostración. Sin IA, sin red externa, sin gasto. **Lo automático no sustituye** a una persona con lector de pantalla: ver «No verificado».

## Resultados (después de las correcciones)
| Comprobación | Resultado | Estado |
|---|---|---|
| axe-core: bienvenida, emparejar, panel vacío y panel con resultado ALTO | **0 infracciones** en las cuatro pantallas | **Probado** |
| Recorrido con Tab (bienvenida, emparejar, panel) | Orden lógico; **foco visible en todos** los elementos; sin trampas de foco | **Probado** |
| Emparejar solo con teclado (escribir el código + Enter) | Llega al panel | **Probado** |
| Foco tras analizar con teclado (Enter en «2. Estafa evidente») | El foco va al título del resultado («Riesgo ALTO») | **Probado** |
| Zoom 200 % (ventana de 640 px CSS a 2×) en bienvenida y panel con resultado | Sin desplazamiento horizontal ni botones o títulos cortados | **Probado** (emulado) |
| Contraste forzado (`forced-colors: active`, como el contraste alto de Windows) | El nivel se ve con **texto + icono**; bordes y enlaces visibles | **Probado** (emulado) |
| `prefers-reduced-motion: reduce` | Ninguna animación ni transición activa | **Probado** (emulado) |
| Pruebas JS de eventos y foco (`tests/ui/test_accesibilidad.cjs`) | 11/11 | **Probado** |

## Problemas encontrados y corregidos
1. **`<aside>` dentro de otro punto de referencia** en la portada (axe `landmark-complementary-is-top-level`, moderado). Ahora es un `div` con `role="group"` y la misma etiqueta. → 0 infracciones.
2. **Escudo invisible en contraste forzado**: el icono es blanco y el fondo pasaba a `CanvasText` (blanco en temas oscuros). Ahora conserva su fondo propio con `forced-color-adjust: none` y un contorno del sistema.
3. **Dos frases casi iguales en «Por qué»**: «La dirección de correo imita…» (remitente) y «La dirección se parece…» (enlace). La segunda dice ahora «La dirección web del enlace se parece…», para que una persona mayor sepa de qué dirección se habla.
4. **Historial con el nivel repetido**: «ALTO — ALTO: probable estafa» pasa a «ALTO — probable estafa».

Pruebas de regresión: `tests/test_h_accesibilidad.py`.

## No verificado (requiere personas)
- **Narrador de Windows (o NVDA) audible** con el diseño final.
- **Contraste alto real de Windows** (aquí solo se emula `forced-colors`).
- **Zoom real del navegador al 200 %** en Windows (aquí, emulado por tamaño de ventana).
- Comprensión por personas mayores reales.

Estimación: 30 minutos de una persona del equipo con Windows (Narrador con Ctrl+Win+Enter, contraste alto con Alt+Mayús izquierda+Impr Pant, zoom con Ctrl y +).
