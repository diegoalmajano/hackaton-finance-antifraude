# Limitaciones conocidas de la detección (reglas `rules-0.3.2`, sin IA)

> Estas limitaciones salen de tres pruebas adversariales de caja blanca: la de la misión 2 (unos 140 casos) y la de la misión 3 (unos 245). Las cifras de detección del conjunto de desarrollo **no** son una evaluación independiente (ver `eval/METODOLOGIA_INDEPENDIENTE.md`).

## Qué hace hoy la capa determinista
- Detecta:
  - Peticiones de claves, códigos, tarjeta o datos de identidad, incluidas formas verbales con pronombre, subjuntivos y peticiones sin la palabra «código».
  - Pagos, cambios de cuenta con IBAN, señuelos (cargo no reconocido, familiar, cuenta segura, inversión, clave caducada, multas con enlace) y acceso remoto.
- Analiza los enlaces sin abrirlos:
  - Dominios parecidos, homógrafos y punycode.
  - Marca de la entidad en un subdominio, antes de una «@» o en la ruta.
  - Dominios incrustados («empresa.es.otra-web») y acortadores.
- Analiza el remitente: dominio parecido al oficial, respuesta a otro dominio y autenticación del correo.
- Resiste:
  - Negaciones que solo afectan a su propia cláusula.
  - Consejos de seguridad («nunca facilite…»).
  - Letras separadas o con guiones, entidades HTML, texto oculto, caracteres invisibles y de ancho completo, y textos alternativos de imágenes.
- Declara el **análisis parcial** cuando:
  - el mensaje es demasiado largo (revisa el principio y el final) o está dañado;
  - falta la IA y era necesaria;
  - una comprobación obligatoria falla.
  En esos casos nunca da BAJO.

## Lo que las reglas NO pueden resolver sin disparar falsos positivos
| Situación | Resultado sin IA | Por qué | Qué lo resolvería |
|---|---|---|---|
| Ingeniería social sin palabras clave («¿Estás? Necesito un favor rápido», «Llámame en cuanto puedas», «la combinación que usas para entrar») | BAJO | Marcarlo por regla alarmaría con mensajes cotidianos idénticos | IA contextual y correlación de varios mensajes (P2) |
| Pronombres que se refieren a algo dicho antes («facilítesela cuando se la pida») | BAJO (prueba `xfail` estricta) | La regla no sabe a qué se refiere «la» | IA |
| Familiar que pide dinero frente a la estafa del «hijo con número nuevo» | MEDIO como máximo si no hay más señales | El texto puede ser idéntico; ninguna regla sabe si el número es el de siempre | El usuario, llamando al número de siempre |
| Cambio de IBAN legítimo de un proveedor, DNI que pide un colegio, multas reales | MEDIO o NO CONCLUYENTE | No se distingue del fraude por el texto | Verificación por un canal conocido (se recomienda siempre) |
| Organismos públicos y empresas (Correos, Hacienda, eléctricas) | NO CONCLUYENTE o MEDIO si hay enlace y llamada a la acción | Sus dominios no están verificados (solo `.gob.es` se considera oficial por estar reservado a las administraciones) | Verificar sus dominios en fuentes oficiales |
| Bancos reales | Dominio oficial incrustado → ALTO; otros dominios con su nombre → MEDIO (incertidumbre) | El registro del Banco de España solo da una web por entidad (cobertura parcial, `docs/DOMINIOS_BANCARIOS.md`) | Completar dominios web y de correo con fuentes de cada entidad |
| Petición de claves desde el dominio oficial («introduzca su contraseña en la nueva app») | MEDIO | Decisión D-29: una petición de credenciales nunca se considera segura | — (decisión deliberada) |
| Mensajes en otros idiomas | Cobertura mínima (inglés básico) y aviso de idioma | Las reglas están pensadas para español (R-56) | IA |
| Contenido dentro de adjuntos o imágenes | No se analiza | Fuera del alcance del MVP (P2) | Fase posterior |

## Principios que se han mantenido
- **No se ajustan reglas a frases concretas:** cada corrección es de patrón o del motor, y se comprueba contra mensajes legítimos del mismo informe.
- **No se sube la detección a base de alarmas:** la urgencia sola ya no alerta (es una señal leve que solo corrobora señuelos), y las multas y deudas solo cuentan si llevan un enlace o un teléfono.
- **Cuando falta información, se declara la incertidumbre** (NO CONCLUYENTE), no se inventa un nivel.


## Revisión P5–P7 y R-64 para la demo local

Casos reproducibles en `tests/test_b_pendientes_demo.py`, con DNS y conexiones bloqueados por la propia prueba. No se han cambiado etiquetas del conjunto dev ni se ha leído el sellado.

| Pendiente | Comprobación y resultado actual | Tratamiento / impacto |
|---|---|---|
| P5 / R-60 | Banco Ficticio desde su dominio invita a encuesta en encuestas.example: MEDIO, parcial | Sigue abierto: el directorio no representa proveedores autorizados ni permite verificar que la encuesta sea legítima. Puede ser una falsa alarma. No se crea una excepción para remitentes oficiales; una petición de contraseña añadida da ALTO |
| P6 / R-61 | Una revista menciona Banco Ficticio y enlaza a su propio artículo: NO CONCLUYENTE, parcial | Corregida la atribución mecánica: claimed_entity_id procede del nombre del remitente o del dominio oficial registrado, nunca solo de una mención en el cuerpo. Se mantiene la IA requerida ausente y no se concede BAJO. Peticiones sensibles, imitaciones y errores conservan sus mínimos; no es comprensión semántica de toda representación bancaria |
| P7 / R-62 | Aviso informativo con acort.test: NO CONCLUYENTE, parcial y destino no comprobado | Límite deliberado de ADR-0005/0006/0015: no seguir el acortador ni dar BAJO cuando la IA requerida falta. El mismo texto puede preceder un destino legítimo o fraudulento. No se rebaja a BAJO ni se afirma que sea fraude |
| R-64 | Enlace directo a archivo ejecutable, incluida .apk/.exe en ruta percent-encoded o con query: MEDIO por sí solo, parcial sin IA | Corregido para extensiones explícitas de ruta. Señal `url.executable_download`; recomienda no descargar desde el mensaje. Es un archivo potencialmente ejecutable, no prueba de malware. Un distribuidor legítimo también puede recibir MEDIO. Con petición de contraseña se corrobora ALTO incluso en dominio oficial |

R-64 no inspecciona bytes ni Content-Type, no sigue redirecciones y no busca nombres dentro de query/fragmento: una descarga sin extensión, un archivo servido desde un acortador o doble codificación puede no detectarse. Documentos .pdf/.png, .exe.txt y extensiones solo en query/fragmento no disparan esta señal. Las 35 pruebas de este archivo incluyen estas contrapartidas y las regresiones de atribución P6. No se promete resolver toda la ingeniería social con reglas.

P6 no autentica al remitente: el nombre y el campo From pueden falsificarse. La selección del dominio aporta contexto de comparación, no una excepción de confianza. No se infiere una identidad bancaria solo por una afirmación en el cuerpo; las señales de contenido y de imitación siguen analizándose. Casos ambiguos sin otras evidencias pueden quedar NO CONCLUYENTE cuando la IA requerida está ausente.
