# Guion de la demostración (≈ 5 minutos)

> Reglas: esta es una **preparación local sin publicar**, basada en `71c5917` más cambios pendientes. Antes de publicar, verificar que código y materiales correspondan a la misma versión. Nada pregrabado como real. Todo lo simulado se dice en voz alta y aparece etiquetado en pantalla. No necesita Internet.

## Preparación (antes de subir al escenario)
1. Ordenador de la demo con Python 3.12 y el proyecto instalado según el README (validación de la copia actual e instalación: ver seguimiento, H6).
2. PowerShell:
   ```powershell
   cd <carpeta del proyecto>\backend
   $env:APP_DEMO_MODE = "1"
   ..\.venv\Scripts\python.exe -m antifraude
   ```
3. Navegador en `http://127.0.0.1:8790/`, zoom al 125–150 % para que se lea desde la sala.
4. Tener copiado en el portapapeles un mensaje de phishing de ejemplo **ficticio** (por ejemplo el de la sección «Texto libre» más abajo).
5. Plan B: si el portátil falla, el mismo flujo en otro ordenador con el ZIP. No hay plan B «grabado».
6. Resultados esperados (comprobados con `rules-0.3.2`, sin IA): ejemplo 1 → BAJO, ejemplo 2 → ALTO, ejemplo 3 → ALTO, texto libre → ALTO. Si cambian las reglas, volver a comprobarlos antes de ensayar.

## Desarrollo
| Min. | Qué se hace | Qué se dice (idea) |
|---|---|---|
| 0:00 | Bienvenida → «Empezar» → introducir el código que aparece en la consola | «Funciona solo en este ordenador. Para conectarse hay que teclear un código de un solo uso que solo ve el usuario: ninguna web externa puede entrar.» |
| 0:40 | Panel: estado de protección (honesto) | «Este es el estado real: el análisis manual está activo; la IA y Gmail se muestran como no configurados porque en esta demo no los usamos.» |
| 1:00 | Ejemplo 1 (aviso legítimo) | «Un banco que informa sin pedir nada: BAJO. Es tan importante no dar falsas alarmas como detectar estafas.» |
| 1:40 | Ejemplo 2 (estafa evidente) | «Aviso preventivo y resultado ALTO. Explica por qué en lenguaje llano: urgencia, petición de claves y un enlace que imita al banco. No abrimos el enlace: lo analizamos sin visitarlo.» |
| 2:40 | Ejemplo 3 (estafa sofisticada) | «Sin faltas ni urgencia. Lo detectamos por incoherencias técnicas: el texto del enlace dice la web del banco pero lleva a otra, la respuesta va a otro dominio y el correo no supera la autenticación.» |
| 3:40 | Texto libre pegado en directo | Mostrar que funciona con un texto nuevo, no solo con ejemplos. |
| 4:20 | «Lo que no hemos podido comprobar» y «Análisis parcial» | «Nunca decimos que algo es seguro si no lo hemos comprobado todo. Por eso no damos porcentajes inventados.» |
| 4:40 | Cierre | Valor para el banco (B2B) y siguientes pasos (Gmail real, IA con presupuesto, bancos reales verificados). |

### Texto libre (ficticio) para pegar
```
Banco Ficticio: hemos detectado un acceso no autorizado. Para evitar el bloqueo de su tarjeta en las próximas 2 horas, confirme el código que le acabamos de enviar respondiendo a este SMS.
```

## Frases a evitar
- «Detecta todas las estafas», «99 % de acierto» o cualquier porcentaje no medido.
- Presentar las métricas del conjunto de desarrollo como evaluación. Si se mencionan: «en nuestros 27 casos de desarrollo, sintéticos y con los que hemos ajustado el motor…».
- Afirmar integración con Gmail, con bancos reales o con GPTadvisor.


## Comprobación ampliada de la demo actual

Use el bloque «Demo local sin IA» del README, que desactiva IA/presupuesto/Opus e integraciones reales y retira clave/modelo del proceso. No basta con activar APP_DEMO_MODE si la consola heredaba configuración de IA.

Después de los tres botones, importe con teclado los archivos de `docs/entrega/ejemplos/`:

| Archivo sintético | Resultado observado por HTTP local, rules-0.3.2 | Qué explicar |
|---|---|---|
| 01-sintetico.eml | BAJO | Aviso informativo sin peticiones sensibles |
| 02-sintetico.eml | ALTO, parcial | Petición de claves y enlace que imita al banco |
| 03-sintetico.eml | ALTO, parcial | Enlace engañoso, respuesta externa y autenticación simulada fallida |
| 04-ambiguo-sintetico.eml | NO CONCLUYENTE, parcial | Un enlace acortado no se abre; no conocemos su destino |

Los cuatro archivos tienen etiquetas sintéticas y dominios reservados. Sus cabeceras de autenticación son **simuladas**. La prueba HTTP local verifica que el archivo tiene prioridad aunque el texto pegado sea diferente; el selector y los anuncios en navegador/lector siguen en la matriz de accesibilidad.

Probar también: envío vacío, archivo de extensión no admitida, corregir y analizar; revisar historial sin cuerpo del mensaje; cerrar sesión y comprobar que /panel exige volver a conectar. El aviso preventivo y el resultado se muestran juntos al completar el análisis local: no se presenta como una notificación asíncrona ya implementada.

Límites relevantes para el jurado: P5 puede alertar en encuestas legítimas; P6 ya no atribuye al remitente una simple mención bancaria; P7 puede quedar NO CONCLUYENTE sin IA. Una descarga directa de ejecutable ahora pide precaución (R-64), sin afirmar que el archivo sea malware. El usuario confirmó zoom real 200 % en el escenario revisado; las comprobaciones de lector, contraste elevado y recorrido manual completo quedan no verificadas y diferidas por el usuario a la fase final indicada en `docs/ACCESIBILIDAD_CODEX.md`.
