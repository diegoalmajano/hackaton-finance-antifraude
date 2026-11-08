"""Seguridad de la API local (ADR-0013, D-30, D-39). F0-05.

- Emparejamiento manual con código de un solo uso (``pairing``).
- Sesiones en servidor con cookie HttpOnly/SameSite=Strict (``sessions``).
- Validación de Host/Origin/Sec-Fetch-Site y cabeceras de seguridad (``middleware``).
- Dependencias de autenticación y CSRF para los endpoints (``deps``).
Nada de esto registra códigos, identificadores de sesión ni tokens.
"""
