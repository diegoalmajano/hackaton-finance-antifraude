# Limitaciones conocidas de la detección (reglas `rules-0.3.0`, sin IA)

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
| Bancos reales | Ver `backend/data/entities_es.json` | Solo se detectan imitaciones de bancos con dominios **verificados** | Tarea C (dominios verificados con fuente y fecha) |
| Petición de claves desde el dominio oficial («introduzca su contraseña en la nueva app») | MEDIO | Decisión D-29: una petición de credenciales nunca se considera segura | — (decisión deliberada) |
| Mensajes en otros idiomas | Cobertura mínima (inglés básico) y aviso de idioma | Las reglas están pensadas para español (R-56) | IA |
| Contenido dentro de adjuntos o imágenes | No se analiza | Fuera del alcance del MVP (P2) | Fase posterior |

## Principios que se han mantenido
- **No se ajustan reglas a frases concretas:** cada corrección es de patrón o del motor, y se comprueba contra mensajes legítimos del mismo informe.
- **No se sube la detección a base de alarmas:** la urgencia sola ya no alerta (es una señal leve que solo corrobora señuelos), y las multas y deudas solo cuentan si llevan un enlace o un teléfono.
- **Cuando falta información, se declara la incertidumbre** (NO CONCLUYENTE), no se inventa un nivel.
