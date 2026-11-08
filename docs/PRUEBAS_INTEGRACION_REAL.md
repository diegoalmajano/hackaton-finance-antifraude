# Pruebas de integración real (preparadas, NO ejecutadas)

> Estado (2026-11-08): **preparadas y saltadas por defecto**. No se han ejecutado: faltan las autorizaciones (SDK, clave y presupuesto de Anthropic; OAuth y librerías de Google). Ninguna afirmación del proyecto depende de ellas hasta que se ejecuten.

## 1. Claude (`tests/integracion_real/test_claude_real.py`)
- **Qué comprueba**, con 3 mensajes **sintéticos** (legítimo, phishing e intento de inyección):
  - que la API responde con el esquema JSON estricto y que las citas de la IA aparecen literalmente en el mensaje;
  - que el rechazo o el fallo se declaran;
  - que el `usage` y el coste real quedan en el libro de gasto;
  - que la inyección no rebaja el nivel.
- **Coste máximo:** 3 solicitudes con Sonnet 5.5. Peor caso ≈ 3 × 0,055 USD ≈ **0,17 USD** con los límites por defecto. El coste real será menor; **está sin medir**.
- **Requisitos y orden:**
  1. Autorizar la instalación del SDK oficial (versión exacta → `requirements.txt` y `docs/DEPENDENCIAS.md`) y repetir la auditoría OSV.
  2. En Anthropic Console, fijar un **límite de gasto** bajo y crear una clave exclusiva del proyecto.
  3. En PowerShell, solo en esa consola:
     ```powershell
     $env:ANTIFRAUDE_PRUEBAS_REALES = "1"
     $env:AI_ENABLED = "1"; $env:CLAUDE_MODEL = "claude-sonnet-5-5"; $env:AI_BUDGET_USD = "0.50"
     $env:ANTHROPIC_API_KEY = Read-Host "Clave de Anthropic" -MaskInput
     .\.venv\Scripts\python.exe -m pytest tests\integracion_real\test_claude_real.py -rs
     ```
  4. Revisar el libro de gasto (`%LOCALAPPDATA%\antifraude\gasto_ia.json`) y anotar el coste real en `docs/contexto/15_SEGUIMIENTO.md`.
  5. `Remove-Item Env:ANTHROPIC_API_KEY` al terminar.
- **Qué queda por verificar con esta prueba:** V-28 (que el SDK acepta `extra_body` con `output_config` y `thinking`), la compilación del esquema `anyOf`, los rechazos reales, la latencia y el coste por mensaje.

## 2. Comparativa reglas frente a Claude (banco dev)
```powershell
cd backend
..\.venv\Scripts\python.exe -m antifraude.evaluation --modo ambos              # muestra el peor caso y NO envía nada
..\.venv\Scripts\python.exe -m antifraude.evaluation --modo ambos --confirmar-gasto
```
- Son 27 casos: el peor caso que calcula el propio comando es ≈ 1,27 USD, pero el presupuesto autorizado lo limita. Con 0,50 USD se detiene al agotarlo y lo declara.
- **Recomendación:** primero la prueba de la sección 1. Después, decidir si se amplía el presupuesto para la comparativa completa.
- Las cifras serán **de desarrollo**, no una evaluación (ver `eval/EJECUCION.md`).

## 3. Gmail (`tests/integracion_real/test_gmail_real.py`)
- **Qué comprueba:**
  - el OAuth de escritorio, solo con `gmail.readonly`;
  - que el token se guarda en el Administrador de credenciales de Windows;
  - que el `client_secret` está fuera del repositorio;
  - que la primera consulta no lee el buzón antiguo.
- **Requisitos:** cuenta de pruebas, proyecto de Google Cloud en modo Testing (B-04), librerías autorizadas y:
  ```powershell
  $env:ANTIFRAUDE_PRUEBAS_REALES_GMAIL = "1"
  $env:GMAIL_CLIENT_SECRET = "C:\Users\<usuario>\secretos\client_secret.json"
  .\.venv\Scripts\python.exe -m pytest tests\integracion_real\test_gmail_real.py -rs
  ```
- Después, la prueba de extremo a extremo manual: enviar un correo sintético desde la cuenta emisora y comprobar que se analiza.
