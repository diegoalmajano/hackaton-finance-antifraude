# Asistente antifraude — resumen de una cara (texto fuente)

> Versión maquetada: `Resumen_Asistente_Antifraude.pdf`, generada desde `resumen_una_cara.html` (método actual y alternativas en `docs/entrega/README.md`). No incluir estadísticas externas sin verificar (V-07).

## El problema
Las estafas por correo y SMS que suplantan a bancos buscan que la víctima entregue sus claves, sus códigos de un solo uso o su dinero. Las personas mayores y con poca experiencia digital son especialmente vulnerables: los mensajes son cada vez más convincentes y meten prisa para que se actúe sin pensar.

## La solución
Un asistente que revisa los mensajes que el usuario elige, **sin abrir nunca los enlaces**, y le explica en español llano:
- **qué nivel de riesgo** tiene el mensaje: BAJO, MEDIO, ALTO o NO CONCLUYENTE, con icono y texto, y **sin porcentajes inventados**;
- **por qué**: evidencias concretas; la IA opcional exige citas verificadas;
- **qué no se ha podido comprobar**;
- **qué hacer**: no compartir códigos, verificar por el teléfono habitual del banco…

La decisión es siempre del usuario.

## Cómo funciona
1. **Reglas deterministas** sobre el texto (petición de claves u OTP, urgencia, cambio de cuenta, premios, inversión milagrosa, suplantación de familiar, órdenes ocultas para la IA…).
2. **Análisis pasivo de enlaces y remitente**: dominios que imitan al banco, texto visible distinto del destino real, acortadores, direcciones numéricas, caracteres engañosos, respuestas a otro dominio, autenticación del correo.
3. **IA (Claude) opcional**: aporta contexto, con citas que se verifican literalmente. Nunca decide sola: un motor determinista fija el nivel y **un error nunca da «BAJO»**.
4. **Alertas en dos fases**: aviso preventivo junto al resultado definitivo explicado.

## Por qué es diferente
- **Explica y reconoce sus límites.** El nivel, las evidencias y las incertidumbres están separados, y nunca afirma seguridad sin comprobarlo todo.
- **Diseñado para personas mayores:** texto grande, alto contraste, teclado, sin tecnicismos y nunca solo color.
- **Privacidad:** funciona en el ordenador del usuario, minimiza los datos antes de usar IA y no guarda el texto de los mensajes.
- **Seguro por diseño:** sin visitar enlaces, resistente a mensajes que intentan manipular a la IA, y con acceso local protegido.

## Modelo y viabilidad
Cliente: **bancos españoles**, como capa de protección para sus clientes (marca blanca en el futuro). El banco no recibe los mensajes personales.
- Coste: el filtro por reglas no cuesta nada por mensaje. La IA solo se usa en los mensajes sospechosos.
- El coste por análisis con IA está **estimado, no medido**: requiere una prueba con presupuesto.

## Estado (prototipo académico)
- **Funciona hoy:** análisis manual completo (texto y `.eml`), interfaz en español con accesibilidad parcialmente verificada y modo demostración con datos ficticios.
- **Probado con simulaciones:** IA y Gmail.
- **Pendiente:** conexión real con Gmail y con la IA, dominios web y de correo completos de los bancos (cobertura actual parcial) y verificación manual completa de accesibilidad.
