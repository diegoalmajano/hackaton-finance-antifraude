# ADR-0004: Gmail por polling de `history.list`

**Fecha**: 2026-11-08
**Estado**: accepted (D-26)
**Decisores**: usuario · Claude Code (propuesta)

## Contexto
Gmail es la primera integración real (D-16), pero la demo principal **no debe depender de Gmail** (D-34). El *push* exige Pub/Sub y un backend en la nube.

## Decisión
Polling de `users.history.list` cada 20–30 s con `startHistoryId` persistido (inicial con `users.getProfile`); `messages.get` solo para mensajes nuevos; incluir SPAM; si `historyId` caduca (404) → resincronizar con `messages.list` reciente. OAuth de app de escritorio con redirección loopback, scope `gmail.readonly`, refresh token en keyring. Solo lectura. Es la **prioridad f** (D-28): el análisis manual y el conector simulado **etiquetado** son el respaldo.

## Alternativas consideradas
### Push con Pub/Sub + `watch`
- **Por qué no**: requiere infraestructura en la nube y renovación de `watch`.
### `messages.list` periódico con conjunto de vistos
- **Por qué no**: más coste de cuota y lógica de deduplicación peor.

## Consecuencias
### Positivas
- Sin servidor público; cuota holgada (`13` §8).
### Negativas
- Latencia de hasta ~30 s en la recepción.
### Riesgos
- OAuth bloqueado o lento → empezar la configuración de GCP cuanto antes (B-04); respaldo manual/simulado.

## Pendiente de verificar (⏳)
- Caducidad de 7 días del refresh token en modo Testing (V-11) · cabecera `Authentication-Results` en `payload.headers` (V-10) · si enviar fragmentos a Anthropic cuenta como «transmisión» para Google (V-15).
