# Materiales de entrega

| Archivo | Qué es | Cómo se genera |
|---|---|---|
| `Presentacion_Asistente_Antifraude.pptx` | Presentación (12 diapositivas) | `powershell -ExecutionPolicy Bypass -File docs\entrega\generar_presentacion.ps1` (requiere Microsoft PowerPoint instalado; lee `presentacion.json`) |
| `Resumen_Asistente_Antifraude.pdf` | Resumen de una cara | Imprimir `resumen_una_cara.html` a PDF (A4, sin encabezados). Se generó con Edge sin interfaz: `msedge --headless=new --no-first-run --disable-background-networking --user-data-dir=<carpeta temporal> --no-pdf-header-footer --print-to-pdf=<salida> <ruta del HTML>`. También vale «Imprimir → Guardar como PDF» desde cualquier navegador |
| `GUION_DEMO.md` | Guion de la demostración en directo | — |
| `PRESENTACION.md` | Guion de las diapositivas y relación con la rúbrica | — |
| `RESUMEN_UNA_CARA.md` | Texto fuente del resumen | — |

Reglas: las cifras deben coincidir con la última ejecución de las pruebas. No se incluyen estadísticas externas sin verificar. Las métricas del conjunto de desarrollo no se presentan como evaluación independiente. Claude y Gmail reales no se presentan como funcionando hasta verificarlos.

El ZIP oficial evaluado es el que se descarga de GitHub tras el push (pendiente de autorización). Para un ZIP local equivalente: `git archive --format=zip -o antifraude.zip HEAD`.
