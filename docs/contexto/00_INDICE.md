# 00 — Índice de la documentación de contexto

> Reescrito (sesión 5, 2026-11-08) para el repositorio independiente. Leer primero `../../CLAUDE.md`; este índice dice **qué documento abrir según la necesidad**. Toda la documentación necesaria está dentro del repositorio.

| Archivo | Para qué sirve | Abrir cuando… |
|---|---|---|
| `01_PROYECTO.md` | Objetivo, datos del evento y su fiabilidad, pilares, independencia | Necesitas el contexto general |
| `02_HACKATON_RUBRICA.md` | **Rúbrica oficial (100 %)**, entregables, reglas, huecos del PDF | Priorizar o preparar la entrega |
| `../referencia/rubrica_oficial_texto.md` | Texto **literal** del PDF oficial | Dudas de interpretación de la rúbrica |
| `07_DECISIONES.md` | Decisiones confirmadas vs propuestas (D-xx / P-xx) | **Antes de cualquier decisión importante** |
| `08_PROGRESO.md` | Historial, estado por área, próximos pasos | Al empezar y cerrar cada sesión |
| `09_PENDIENTES.md` | Bloqueos, decisiones técnicas abiertas, verificaciones, contradicciones, riesgos | Antes de afirmar algo dudoso |
| `10_FUENTES.md` | Origen de cada documento, fuente oficial, qué no se copió | Citas o dudas de origen |
| **`11_PRODUCTO_ANTIFRAUDE.md`** | **Producto vigente**: alcance, público, principios, MVP P0/P1/P2, UX, alertas, riesgo, enlaces, personalización, demo, éxito | Siempre que se diseñe, programe o presente |
| `12_VIABILIDAD_PLATAFORMAS.md` | Límites reales por canal, inteligencia de URLs y licencias, costes de modelos, competencia, datos INCIBE, fuentes | Antes de prometer o implementar un canal |
| **`../adr/README.md`** | **ADR-0001–0015 aprobados** (sesión 6, D-26): fuente de verdad de la arquitectura | Antes de programar cualquier módulo |
| **`13_ARQUITECTURA_TECNICA.md`** | Arquitectura **aprobada con modificaciones** (ver resumen al inicio): entorno, contratos, pipeline, motor de riesgo, enlaces, Gmail, seguridad. Si contradice un ADR, prevalece el ADR | Detalle técnico de un módulo |
| **`14_PLAN_EJECUCION.md`** | **§11: plan para un desarrollador y Fase 0** (propuesta P-16); Git, pruebas, aceptación, riesgos, costes, entregables | Planificar y cerrar fases |

Numeración: se conservan los números de la memoria original para trazabilidad; 03–06 no existen aquí (histórico no copiado, ver `10` §3).

## Búsquedas rápidas
- Pesos de la rúbrica → `02` §1 · Entregables → `02` §2.
- Reglas de seguridad → `11` §4, §8, §9 y `13` §10 · Niveles de riesgo → `11` §8 y `13` §6.
- MVP → `11` §5 · Demo → `11` §12 · Criterios de aceptación → `14` §6.
- ¿Qué está pendiente de decidir? → `09` §1–2 (incluye modelo Opus/Sonnet, T-11).

## Convención
✅ confirmado (doc. oficial) · 🟡 fuentes secundarias · 📢 declarado por proveedor · 💬 solo usuario/chat · ❓ hipótesis · ⏳ pendiente · ⚖ valoración del asistente.
