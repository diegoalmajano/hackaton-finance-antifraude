# Ejecución reproducible de la evaluación

Estado: evaluador implementado y verificado con dev y dobles simulados. La evaluación independiente no está realizada. Autoría, custodia y cierre humano: [metodología](METODOLOGIA_INDEPENDIENTE.md) y [guía operativa](../docs/EVALUACION_FINAL_PROCEDIMIENTO.md).

## Qué se mide y qué no

| Comprobación | Fuente | Alcance |
|---|---|---|
| Pruebas unitarias | `tests/` | Invariantes y comportamiento de componentes; no rendimiento de detección |
| Integración local/simulada | `tests/`, incluido HTTP en loopback | Unión entre componentes; Gmail/IA simulados no equivalen a una cuenta o API real |
| Pruebas adversariales | Regresiones `test_b_*` | Fallos seleccionados para romper el detector; no muestra representativa |
| Métricas de desarrollo | `eval/datasets/dev/` | Los 27 casos usados para ajustar el motor, todos `synthetic_ai`; no generalización |
| Evaluación independiente | Conjunto externo autorizado y custodiado | Solo puede calificarse así si la autoría, etiquetas, congelación y ejecución están documentadas |

Los resultados actuales de las suites, integraciones reales saltadas y fallos esperados se registran en [seguimiento](../docs/contexto/15_SEGUIMIENTO.md). No se declaran superadas las pruebas reales por existir su código.

## Ejecución dev autorizada sin gasto

Desde la carpeta `backend`, con el entorno existente y sin instalar paquetes:

```powershell
$env:AI_ENABLED='0'
$env:AI_BUDGET_USD='0'
$env:AI_ALLOW_OPUS='0'
$env:ANTIFRAUDE_PRUEBAS_REALES='0'
$env:ANTIFRAUDE_PRUEBAS_REALES_GMAIL='0'
$env:APP_GMAIL_ENABLED='0'
Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:CLAUDE_MODEL -ErrorAction SilentlyContinue
..\.venv\Scripts\python.exe -m antifraude.evaluation
```

Por defecto se usa `--modo reglas` sobre los archivos de dev y se escribe un JSON en `eval/results/` (ignorado por Git). `--salida <archivo>` permite elegir un destino local fuera de datos/código; use nombres distintos si necesita conservar varias revisiones. No se guardan textos de mensajes ni citas en el informe.

## Configuraciones que siguen requiriendo autorización

No ejecutar actualmente modos con IA ni evaluación sellada: presupuesto vigente cero, modelo/SDK/datos/privacidad pendientes y ningún conjunto final autorizado. No pegar claves ni casos privados en el chat.

Cuando exista permiso específico, la sintaxis del evaluador permite `--modo ia` o `--modo ambos --confirmar-gasto`; este último compara reglas y **un** modelo de IA configurado en una única ejecución. Antes de cualquier envío presenta un límite conservador basado en los máximos de tokens y solicitudes; CostGuard conserva la decisión efectiva de reserva. Una estimación superior al presupuesto se avisa y puede dar análisis parciales por agotamiento; no se promete completar todos los casos con IA.

El preflight de IA desactivada/no configurada o de falta de `--confirmar-gasto` devuelve código 3 antes de leer, calcular la huella o reservar la marca del conjunto final. Confirmar ese argumento no habilita por sí mismo modelo, clave, política ni presupuesto.

La sintaxis `--sellado <archivo externo> --sha256 <huella aprobada>` está documentada para el custodio el día autorizado, no es una instrucción para crear ni leer casos ahora. La CLI no ejecuta una matriz de varios modelos sobre una misma huella: no borrar la marca para improvisar nuevas variantes. La comparación de modelos exige un plan y autorización previos.

## Contenido del informe actual

- Fecha, commit, `arbol_trabajo_sucio`, versión de Python, plataforma, SHA-256 de requirements.lock, reglas/prompt y modelo. Un árbol sucio no acredita el código exacto de ese commit; null significa que no se pudo comprobar Git. La huella del lock no verifica por sí sola las dependencias realmente instaladas.
- Por configuración y por origen/medio: VP/FP/FN/VN, precisión, recall, F1 y tasa de FP; Wilson para precisión/recall/tasa de FP; números y tasas de NO CONCLUYENTE, ambiguos aparte, niveles aceptables, análisis parciales y latencias p50/p95.
- Citas esperadas/cubiertas y cobertura literal. La revisión local solo reglas da 0/62; las evidencias deterministas describen señales sin adjuntar esas citas. No equivale a una auditoría humana de las explicaciones.
- `llamadas_ia` y `fallos_ia`: transportes verificados mediante CostGuard; caché reutilizada y bloqueos locales separados. Un adaptador genérico sin telemetría no permite inferir solicitudes y produce null.
- `coste_real_usd`: suma calculada con usage de solicitudes nuevas, sin duplicar caché; null si alguna solicitud no tiene coste/usage o no hay telemetría. `coste_con_usage_usd` conserva la suma conocida y `solicitudes_sin_coste_usage` muestra el hueco. El libro mantiene reservas pesimistas de errores inciertos. No es una factura ni una medición real cuando el transporte es simulado.

Los informes dev incluyen identificadores y niveles (o diferencias entre configuraciones), nunca textos. Los informes sellados y su salida de consola son solo agregados. El análisis cualitativo de cada FP/FN del conjunto final corresponde a los revisores autorizados, no a los agentes que ajustaron el detector.

## Controles del modo sellado y sus límites (D-40)

1. Rechaza rutas dentro del repositorio, incluidas resoluciones que apuntan a él.
2. Compara la huella del archivo con el argumento `--sha256`. **El custodio** debe verificar que ese argumento coincide con el registro aprobado de SELLADO.md; el código no valida automáticamente dicho registro.
3. Crea una marca exclusiva en `eval/results/` antes de analizar y rechaza una marca ya existente. Si el análisis se interrumpe después, la reserva permanece y no se repite automáticamente.
4. La marca es un control local: otro directorio de resultados, su borrado o una copia distinta no constituyen una custodia global ni autorizan reejecuciones. Mantener el registro y no alterar la marca es responsabilidad del custodio.
5. Antes de esa ejecución se deben fijar ubicación externa, autores/revisores, etiquetas, huella, versión limpia congelada y configuraciones aprobadas. No modificar reglas tras observar el conjunto final y presentar el resultado como si continuara siendo independiente.
6. La ejecución no demuestra por sí sola independencia, autoría, revisión humana ni congelación. Siguen pendientes T-14 y las medidas de denegación de lectura/custodia T-18. No se ejecutan Claude Code/ECC ni se modifica configuración personal para resolverlas.

No se ha creado ni consultado un conjunto final en esta revisión. Los tests del mecanismo utilizan dobles temporales claramente identificados; no son datos de evaluación independiente.
