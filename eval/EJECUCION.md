# Ejecución reproducible de la evaluación

> Desarrolla la sección 5 de `METODOLOGIA_INDEPENDIENTE.md`. Desde la carpeta `backend`.

## Cuatro cosas distintas (no mezclarlas)
| Qué | Dónde | Qué permite afirmar |
|---|---|---|
| **Pruebas unitarias y de integración simulada** | `tests/` (unas 660) | Que el código hace lo que dice el diseño. **No** miden la detección |
| **Pruebas adversariales** | `tests/test_b_regresiones_adversariales.py`, `tests/test_b_adversariales_ronda3.py` | Que los fallos encontrados por los probadores siguen corregidos. Son casos elegidos para romper el sistema, **no** una muestra representativa |
| **Métricas de desarrollo** | `python -m antifraude.evaluation` sobre `eval/datasets/dev/` (27 casos sintéticos) | Nada sobre la generalización: el motor se ajustó con estos casos |
| **Evaluación independiente** | `--sellado` sobre un conjunto **fuera del repositorio** que nadie del desarrollo ha visto | Lo único que puede presentarse como rendimiento, con su tamaño e intervalos |

## Comandos
```powershell
..\.venv\Scripts\python.exe -m antifraude.evaluation                       # dev, solo reglas (por defecto)
..\.venv\Scripts\python.exe -m antifraude.evaluation --modo ambos          # reglas frente a reglas + Claude (requiere IA autorizada)
..\.venv\Scripts\python.exe -m antifraude.evaluation --modo ambos --confirmar-gasto
..\.venv\Scripts\python.exe -m antifraude.evaluation --sellado <ruta fuera del repo> --sha256 <huella> [--modo ambos --confirmar-gasto]
```
- Cada ejecución escribe un **informe JSON** en `eval/results/`, que Git ignora. El informe incluye:
  - la fecha, el commit, `rule_version`, `prompt_version` y el modelo;
  - por configuración: VP, FP, FN, VN, precisión, recall, F1, tasa de FP con **intervalos de Wilson**, NO CONCLUYENTE, latencias p50 y p95, llamadas a la IA y **coste real** (suma del `usage` de cada respuesta).
- Desarrollo con `--modo ambos`: lista de casos cuyo nivel cambia entre reglas y reglas + IA. Solo identificadores y niveles, nunca textos.
- Sin IA autorizada, los modos con IA salen con código 3 **sin enviar nada**. Con IA, muestran antes el peor caso de coste y exigen `--confirmar-gasto`. El presupuesto de `CostGuard` sigue mandando.

## Garantías del modo sellado (D-40)
1. El archivo debe estar **fuera del repositorio**; si no, se rechaza.
2. La huella SHA-256 debe coincidir con la registrada en `eval/SELLADO.md`; si no, se rechaza.
3. En pantalla **solo se muestran agregados**: ni identificadores ni textos de casos. El informe JSON tampoco incluye casos.
4. **Una sola ejecución por huella:** queda una marca en `eval/results/` y la segunda se rechaza.
5. Antes de ejecutar: congelar el commit del detector y no tocar las reglas después.
6. Pendiente de decisión del usuario: la ubicación (T-14) y, opcionalmente, una regla de denegación de lectura para los agentes en `.claude/settings.local.json` (T-18).
   - Este mecanismo **no** lee el conjunto en ningún otro momento.
   - Ningún agente lo ha creado ni leído.
