# 10 — Fuentes y trazabilidad

> Reescrito (sesión 5) para el repositorio independiente. Explica de dónde sale cada documento y qué **no** se ha copiado.

## 1. Origen de esta documentación
La memoria original se creó en las sesiones 1–4 (2026-11-08) en una carpeta de trabajo externa a este repositorio. En la sesión 5 se copió aquí lo vigente para que el repositorio sea **autosuficiente** (D-23). Los originales externos **no se han modificado**.

| Documento del repo | Origen | Tratamiento |
|---|---|---|
| `00_INDICE.md`, `10_FUENTES.md` | Memoria original 00 y 10 | Reescritos |
| `01_PROYECTO.md`, `02_HACKATON_RUBRICA.md`, `07`, `08`, `09` | Memoria original | Adaptados: solo contenido vigente, referencias corregidas |
| `11_PRODUCTO_ANTIFRAUDE.md`, `12_VIABILIDAD_PLATAFORMAS.md`, `13_ARQUITECTURA_TECNICA.md`, `14_PLAN_EJECUCION.md` | Memoria original | Copiados con cambios mínimos marcados «(sesión 5)» |
| `../referencia/rubrica_oficial_texto.md` | Texto extraído del PDF oficial | Transcripción literal |

## 2. Fuente oficial
Único documento oficial del hackatón: **«Completo hack finance.pdf»** (2 páginas; 265 664 bytes; SHA-256, 16 primeros hex `2182c34ebb762066`). Su texto completo está en `../referencia/rubrica_oficial_texto.md`. El PDF no se copia (las imágenes son solo logos).

## 3. No copiado (histórico o irrelevante para el antifraude)
- Memoria original `03_GPTADVISOR`, `04_COMPETIDORES`, `05_IDEAS_PRODUCTO`, `06_ARQUITECTURA` y `11_ANALISIS_ESTRATEGICO`: idea fiscal descartada (D-09) e investigación del ecosistema de GPTadvisor.
- Informe y anexos de investigación sobre GPTadvisor, chat exportado (DOCX), prototipo fiscal (ZIP duplicado) y caché de extracción: histórico de la idea fiscal. El prototipo **no se reutiliza** (`13` §1).
- Si en el futuro hiciera falta argumentar frente a GPTadvisor, recuperar ese material de la carpeta original y resumirlo aquí.

## 4. Fuentes externas
Las URL de documentación oficial (Gmail, Graph, Telegram, Windows, Safe Browsing/Web Risk, Tauri, librerías, Anthropic, AI Act, INCIBE) están en `12` §5bis y §6. Fiabilidad marcada en cada dato (✅/🟡/⏳). **Antes de implementar un conector, abrir la documentación oficial enlazada**; las cifras de INCIBE deben verificarse en la fuente original antes de presentarlas.
