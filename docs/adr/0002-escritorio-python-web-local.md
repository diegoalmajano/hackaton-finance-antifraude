# ADR-0002: Aplicación web local primero; pywebview y bandeja después

**Fecha**: 2026-11-08
**Estado**: accepted (D-26, D-27)
**Decisores**: usuario · Claude Code (propuesta)

## Contexto
D-15 fija Windows con bandeja como primera plataforma, pero la pila de escritorio Python (pywebview/pythonnet, pystray, toasts) tiene incógnitas de compatibilidad y de hilos. La rúbrica premia una solución acabada y ejecutable (30 %).

## Decisión
La aplicación es una **web local** servida por FastAPI en `127.0.0.1`, utilizable desde el navegador. **pywebview (ventana nativa), pystray (bandeja) y las notificaciones nativas se añaden solo después de comprobar que el núcleo funciona** (prioridad g, D-28), como envoltorio fino sin lógica propia.

## Alternativas consideradas
### pywebview desde el día 0 (propuesta original, con navegador como plan B)
- **Por qué no**: hace depender el núcleo de la parte más incierta.
### Electron + Python hijo
- **Contras**: dos runtimes, empaquetado y endurecimiento. **Por qué no**: inviable en plazo; **descartado para el hackatón**.
### Tauri 2
- **Por qué no**: exige Rust + MSVC (no instalados). Descartado.

## Consecuencias
### Positivas
- El núcleo es demostrable desde el primer día; el respaldo «navegador» es la base, no un parche.
### Negativas
- Hasta la fase g no hay bandeja ni toasts nativos (las alertas se ven en la UI web).
### Riesgos
- Que no dé tiempo a la capa de escritorio → la demo se hace en navegador local, declarándolo.

## Pendiente de verificar (⏳)
- Convivencia de hilos pywebview (hilo principal) / pystray / Uvicorn en Windows · pythonnet con Python 3.12 (V-12) · licencia de pystray (V-13) · win11toast con 3.12.
