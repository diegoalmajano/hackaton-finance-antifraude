# Materiales de entrega

> Estado vigente de cierre, 10-11-2026: rules-0.3.9, 1030 Python / 11 JS / 8 SDK Gmail simulados. Candidata local codex/candidata-council, base 615b4a9, sin commit ni publicación. Evidencia y pendientes: [DECISION_VERSION_FINAL.md](../DECISION_VERSION_FINAL.md). Las secciones fechadas anteriores son históricas.

| Archivo | Qué es | Cómo se genera |
|---|---|---|
| `Presentacion_Asistente_Antifraude.pptx` | Presentación (12 diapositivas) | Fuente: `presentacion.json`. Candidata actualizada con Artifact Tool del runtime de Codex, renderizada y validada. Alternativa existente: `docs\entrega\generar_presentacion.ps1`, que requiere PowerPoint instalado; no se ejecutó para esta revisión |
| `Resumen_Asistente_Antifraude.pdf` | Resumen de una cara | Fuente: `resumen_una_cara.html`. Candidata regenerada con ReportLab del runtime de Codex, renderizada con Poppler e inspeccionada. Alternativa: imprimir el HTML a PDF A4 sin encabezados desde un navegador; esa alternativa no se ejecutó ahora |
| `GUION_DEMO.md` | Guion de la demostración en directo | — |
| `PRESENTACION.md` | Guion de las diapositivas y relación con la rúbrica | — |
| `RESUMEN_UNA_CARA.md` | Texto fuente del resumen | — |

Reglas: las cifras deben coincidir con la última ejecución de las pruebas. No se incluyen estadísticas externas sin verificar. Las métricas del conjunto de desarrollo no se presentan como evaluación independiente. Claude y Gmail reales no se presentan como funcionando hasta verificarlos.

La publicación inicial ya se completó. El 09-11-2026 el usuario autorizó consolidar esta revisión en un commit y subir solo feat/fase-0 al mismo repositorio privado. Antes de confirmar los cambios, git archive HEAD solo empaqueta el commit anterior; las comprobaciones de esta revisión utilizaron una copia temporal con las fuentes actuales.


## Revisión local preparada para consolidación
- PPTX de 12 diapositivas: corregido sobre la presentación existente con Artifact Tool del runtime ya disponible. Se conservaron tamaños, diseño y tipografías, se inspeccionaron las 12 diapositivas renderizadas y pasaron validación de paquete/geometría y reimportación. No se ha abierto en PowerPoint en esta revisión. `presentacion.json` conserva el contenido actualizado para regeneración con el script existente.
- PDF: actualizado desde el HTML con ReportLab del runtime incluido, sin instalar paquetes en el proyecto. Una página A4, texto extraído comprobado y render PNG inspeccionado. La maquetación tiene pequeñas diferencias respecto a la impresión HTML original. El HTML sigue siendo la fuente de contenido.
- Ambos materiales reflejan 746 pruebas Python y 11 JS, IA/Gmail reales sin activar y accesibilidad parcial. No afirman conformidad WCAG general.
- Los `.eml` de `ejemplos/` son exclusivamente sintéticos. Su resultado HTTP se verifica en `tests/test_demo_http_local.py`; las cabeceras de autenticación de esos ejemplos son simuladas.
- `git archive HEAD` **no** incluye las correcciones locales sin commit: no usarlo como entrega actual. La copia temporal de verificación incluye únicamente fuentes publicables seleccionadas explícitamente, con los cambios actuales y sin entorno virtual ni archivos ignorados. Su evidencia y los límites de instalación se registran en el seguimiento. No se genera ni se versiona un ZIP temporal. La autorización actual solo cubre el commit y push de esta revisión; registro de comprobaciones en el seguimiento.

## Continuación final del MVP — 09-11-2026
Las autorizaciones de publicación del bloque anterior quedaron ejecutadas en dd3e4fb. Esta misión autoriza commits locales revisados, **no push ni publicación**. Los materiales se reconciliaron con 877 Python/11 JS, reglas0.3.3, diseño final con accesibilidad parcial y Gmail en el panel probado con simulaciones. Ocho comprobaciones SDK Gmail separadas; ninguna conexión real.

El ZIP local candidato se genera fuera del repositorio a partir de una lista revisada de fuentes actuales, sin .git/.venv/ignorados/datos privados. No es el ZIP oficial descargado de una futura publicación de GitHub. Resultados y límites en docs/VERIFICACION_FINAL_MVP.md. PPTX actualizado conservando el diseño existente, validado y renderizado; no se afirma abierto en PowerPoint. PDF A4 de una página regenerado desde HTML con ReportLab incluido y revisado visualmente.
