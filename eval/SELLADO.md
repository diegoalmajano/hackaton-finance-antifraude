# Conjunto de evaluación final sellado — procedimiento (D-40)

> **Estado (2026-11-08, F0-08): NO creado.** Su ubicación fuera del repositorio está pendiente de acordar (T-14). No crear casos sellados hasta entonces.

## Reglas
1. Los casos sellados viven **fuera de este repositorio** (por ejemplo, en una carpeta o unidad indicada por el usuario) y **nunca** se versionan. `.gitignore` bloquea además `eval/datasets/test_sealed/`, `eval/sealed/` y `*.sealed.jsonl` por si acaso.
2. **Los agentes (Claude Code, ECC y otros) no deben leer ni consultar** el conjunto sellado durante el desarrollo. No se les da su ruta hasta el día de la evaluación.
   - Recomendación pendiente de decisión: añadir una regla de denegación de lectura para esa ruta en `.claude/settings.local.json`.
3. Se escribe **antes** de ajustar las reglas y los prompts con el conjunto `dev`, con el mismo formato (`EvalCase`, `split = "sealed_test"`, `case_id = test-NNNN`).
4. Al cerrarlo se calcula su **huella SHA-256**, y en este repositorio se registran solo metadatos no sensibles. Esta información se añadirá a este archivo al cerrar el conjunto:
   - fecha de cierre;
   - número de casos por tipo y por origen (`synthetic_human`, `synthetic_ai`, `adapted_licensed`);
   - SHA-256 del archivo.
5. El día de la evaluación (con autorización del usuario y presupuesto aprobado):
   - Verificar que el SHA-256 coincide.
   - Ejecutar el sistema **una sola vez**.
   - Guardar los resultados en `eval/results/` (ignorado).
   - **No modificar casos después**.
6. Limitación conocida (R-26): con un único autor, «sellado» significa escrito antes de ajustar y no consultado hasta el final. No es una evaluación independiente.
