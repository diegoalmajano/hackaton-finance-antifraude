# Configuración del asistente (Windows PowerShell)

> F0-07 (2026-11-08). Referencia de variables: `.env.example` (raíz del repositorio).
> El asistente **no carga archivos `.env`**: no hay ninguna dependencia autorizada para ello (V-24). Las variables se definen en la consola antes de arrancar.

## 1. Variables disponibles
| Variable | Para qué sirve | Valor por defecto | ¿Secreto? |
|---|---|---|---|
| `APP_PORT` | Puerto local (siempre en `127.0.0.1`). Entero 1024–65535 | `8790` | No |
| `APP_LOG_LEVEL` | Detalle de los registros: `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` | No |
| `ANTHROPIC_API_KEY` | Clave de la API de Anthropic (fase d; **aún no se usa**) | vacía → IA «no configurada» | **Sí** |
| `CLAUDE_MODEL` | Modelo de Claude (fase d; **aún no se usa**). Elección pendiente (D-24, D-32) | vacío | No |

La dirección de escucha **no** es configurable: siempre `127.0.0.1` (ADR-0013).

## 2. Definir variables solo para la consola actual (recomendado)
Duran hasta cerrar la ventana de PowerShell. Es la forma recomendada, sobre todo para claves.
```powershell
cd C:\Users\dialm\Desktop\hackaton-finance-antifraude\backend
$env:APP_PORT = "8791"          # opcional
$env:APP_LOG_LEVEL = "INFO"     # opcional
..\.venv\Scripts\python.exe -m antifraude
```
Ver las variables definidas (sin mostrar la clave):
```powershell
Get-ChildItem Env:APP_*
if ($env:ANTHROPIC_API_KEY) { "ANTHROPIC_API_KEY definida" } else { "ANTHROPIC_API_KEY sin definir" }
```
Quitar una variable de la consola actual:
```powershell
Remove-Item Env:APP_PORT
```

## 3. Clave de API (cuando llegue la fase d)
- Escríbala **solo en la consola** para que no quede en el historial de PowerShell, pidiéndola de forma oculta:
  ```powershell
  $env:ANTHROPIC_API_KEY = Read-Host "Clave de Anthropic" -MaskInput   # PowerShell 7
  ```
  En Windows PowerShell 5.1 (sin `-MaskInput`):
  ```powershell
  $s = Read-Host "Clave de Anthropic" -AsSecureString
  $env:ANTHROPIC_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
  ```
- **No** la guarde en archivos del repositorio, en `.env.example`, en capturas ni en documentos.
- **No** se recomienda guardarla como variable permanente de usuario: quedaría en el registro de Windows en texto claro.
- Al terminar: `Remove-Item Env:ANTHROPIC_API_KEY`.

## 4. Variables permanentes (opcional, solo para valores NO secretos)
```powershell
[Environment]::SetEnvironmentVariable("APP_PORT", "8791", "User")   # nuevas consolas
[Environment]::SetEnvironmentVariable("APP_PORT", $null, "User")    # eliminarla
```

## 5. Errores de configuración
Si una variable no es válida, el asistente **no arranca** y explica en español qué variable revisar, **sin mostrar el valor** recibido. Ejemplo:
```
ERROR: la configuración del asistente no es válida.
  - APP_PORT debe ser un número entero entre 1024 y 65535 (por defecto, 8790).
Consulte docs/CONFIGURACION.md.
```
Si el puerto está ocupado por otro programa, también lo indica y no cierra procesos ajenos ni cambia de puerto (D-42).

## 6. Registros y privacidad (F0-07)
- Sin registro de accesos (rutas, IP, cabeceras).
- El código **nunca** registra códigos de emparejamiento, cookies, tokens CSRF, claves ni contenido de mensajes.
- Defensa adicional: todos los manejadores de registros aplican un filtro que oculta valores con forma de secreto (cookie de sesión, cabeceras sensibles, claves `sk-ant-…`, tokens de 43 caracteres, códigos de emparejamiento) y **elimina las trazas de excepción**.
- Un error interno no controlado responde «Se ha producido un error interno» y solo registra el **tipo** de error, el archivo y la línea de origen y la ruta; nunca el mensaje de la excepción.
- Excepción deliberada: el código de emparejamiento se **muestra** en la consola (no es un registro) porque el usuario necesita leerlo. No redirija esa salida a un archivo (R-32).
- El código de emparejamiento se introduce en la interfaz y viaja **solo en el cuerpo de `POST /pairing`**; nunca en una URL ni en una respuesta.
