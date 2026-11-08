# ADR-0013: Seguridad de la API local

**Fecha**: 2026-11-08
**Estado**: accepted (D-26, D-30)
**Decisores**: usuario · Claude Code (propuesta)

## Contexto
Un servidor en `127.0.0.1` es accesible desde cualquier página abierta en el navegador del usuario (CSRF, DNS rebinding) y desde otros procesos locales. La app maneja contenido sensible (mensajes, evaluaciones, conexión a Gmail).

## Decisión
1. Escuchar **solo en `127.0.0.1`** (nunca `0.0.0.0`).
2. **Validación de `Host`**: solo `127.0.0.1:<puerto>` y `localhost:<puerto>` (defensa contra DNS rebinding).
3. **Autenticación de sesión**: secreto aleatorio por arranque; sesión en **cookie `HttpOnly`, `SameSite=Strict`**, con caducidad. **Ningún token sensible en URLs** (ni en logs ni en el historial).
4. **Validación de `Origin`** (y `Referer` como respaldo) en toda petición que cambie estado y en SSE.
5. **CSRF**: token sincronizado enviado en una cabecera por htmx (además de `SameSite=Strict` y `Origin`).
6. **SSE protegido**: exige sesión válida y `Host`/`Origin` correctos; no transmite contenido completo de mensajes.
7. Cabeceras: CSP estricta (`default-src 'self'`, sin scripts en línea), `X-Content-Type-Options: nosniff`, `frame-ancestors 'none'`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store` en respuestas con datos.
8. Sin CORS abierto.

**Cómo obtiene la sesión el navegador — PENDIENTE de elegir (T-13)** respetando «sin tokens sensibles en URLs»: (a) código de emparejamiento corto que se muestra en la consola/lanzador y se introduce en la primera pantalla; (b) código de un solo uso y caducidad corta en la URL de arranque, canjeado de inmediato por la cookie y retirado con redirección. La (b) pone un valor en la URL aunque no sea reutilizable → requiere decisión expresa del usuario. Con pywebview (fase g) la sesión puede inyectarse sin pasar por la URL.

**Resolución de T-13 (2026-11-08, D-39): opción (a).** Emparejamiento manual inicial con un **código aleatorio de un solo uso** generado con un generador criptográfico (`secrets`), de entropía suficiente frente a fuerza bruta local, **con caducidad corta y limitación de intentos** (bloqueo tras N fallos); al canjearlo se emite la cookie de sesión (`HttpOnly`, `SameSite=Strict`, `Path=/`; sin `Secure` porque el contexto es `http://127.0.0.1`, con caducidad). **Nunca se ponen tokens de sesión en URLs.** Los parámetros exactos (longitud, caducidad, número de intentos) se fijan y prueban en F0-05. La opción (b) queda descartada.

**Implementación F0-05 (2026-11-08, D-45):** `backend/antifraude/app/security/` — `policy.py` (parámetros), `pairing.py` (código de 8 caracteres de un alfabeto de 31 símbolos sin ambiguos, `secrets`, 5 min, un uso; esperas 1-2-4-8 s; bloqueo al 5.º fallo hasta reiniciar; máx. 10 códigos por ejecución y 30 s entre emisiones; los códigos nuevos no reinician los fallos; el código solo se muestra en la consola, sin `logging`), `sessions.py` (id de 256 bits, en memoria solo su SHA-256; inactividad 30 min, absoluta 8 h; máx. 3 sesiones; token CSRF por sesión), `middleware.py` (Host exacto; `Origin` obligatorio en métodos que cambian estado y validado si llega en GET; `Sec-Fetch-Site` solo `same-origin`/`none` —otra app en otro puerto de 127.0.0.1 es *same-site* y se rechaza—; `Content-Length` obligatorio y ≤ 6 MiB en métodos que cambian estado; cabeceras de seguridad y CSP estricta en todas las respuestas; sin CORS), `deps.py` (sesión y CSRF como dependencias). Errores en español sin detalles técnicos ni eco de la entrada. Sin `Secure` en la cookie: el contexto es `http://127.0.0.1` sin TLS.

**Aclaración (F0-06):** el código de emparejamiento se introduce en la interfaz y se envía **solo en el cuerpo de `POST /pairing`** (formulario). Nunca aparece en una URL, en una página, en una respuesta HTTP ni en los registros; únicamente se muestra en la consola local del asistente. La interfaz (Jinja + htmx) reutiliza estas mismas sesiones, cookies y CSRF; el token CSRF se obtiene con `GET /session` y se mantiene solo en memoria del navegador.

## Alternativas consideradas
### Sin autenticación (solo loopback)
- **Por qué no**: cualquier web podría enviar peticiones a la API local.
### Token en la URL (propuesta inicial `?token=`)
- **Por qué no**: queda en historial, logs y `Referer`; descartado por el usuario.

## Consecuencias
### Positivas
- Protección frente a CSRF, DNS rebinding y uso desde otras webs.
### Negativas
- Algo más de complejidad en el arranque y en las pruebas.
### Riesgos
- Bloquear al propio usuario por errores de configuración → tests de cada control y mensajes claros en español.
