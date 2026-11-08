# Dominios de entidades financieras reales (tarea C, misión 3)

## Fuente y método
- **Fuente oficial:** Registro de Entidades del Banco de España, listado descargable «Entidades de crédito» (`https://www.bde.es/f/webbe/SGE/regis/ficheros/es/Registro_EntCredito.xlsx`), enlazado desde la página oficial «Información de otros registros» del Banco de España.
- **Fecha del fichero:** 05/11/2026. **Consulta:** 2026-11-08.
- **Método:**
  1. Descarga en una carpeta temporal aislada.
  2. Lectura con la biblioteca estándar de Python (el `.xlsx` es un ZIP con XML), sin dependencias nuevas.
  3. Filtrado por código BE y por entidades **activas**, sin fecha de baja.
  4. Se tomó el campo «PÁGINA WEB».
  5. No se abrió ninguna web de los bancos ni ningún enlace sospechoso.

| Entidad | Código BE | NIF | Web en el registro | Dominio incorporado |
|---|---|---|---|---|
| Banco Santander, S.A. | 0049 | A39000013 | `HTTP://www.santander.com` | `santander.com` (y subdominios) |
| Banco Bilbao Vizcaya Argentaria, S.A. | 0182 | A48265169 | `HTTP://WWW.BBVA.COM` | `bbva.com` (y subdominios) |
| CaixaBank, S.A. | 2100 | A08663619 | `HTTP://WWW.CAIXABANK.ES` | `caixabank.es` (y subdominios) |
| Banco de Sabadell, S.A. | 0081 | A08000143 | `HTTP://WWW.GRUPOBANCOSABADELL.COM` | `grupobancosabadell.com` (y subdominios) |
| Bankinter, S.A. | 0128 | A28157360 | `HTTP://WWW.EBANKINTER.COM` | `ebankinter.com` (y subdominios) |

## Por qué la cobertura es **parcial**
- El registro da **una sola web por entidad**, normalmente la corporativa. Los bancos usan otros dominios para la banca de clientes y para el correo, que este registro **no** recoge, y que no se han verificado.
- Si se tratara esa lista como completa, un correo **auténtico** del banco desde otro dominio suyo se marcaría como suplantación crítica, un falso positivo grave.
- Por eso las cinco entidades llevan `domain_coverage: "partial"`, y el comportamiento es este:

| Caso | Con cobertura parcial |
|---|---|
| Enlace o remitente en un dominio registrado (o subdominio) | Oficial |
| Dominio oficial incrustado en otro (`bbva.com.otro.test`) | **Crítico → ALTO** (nunca es legítimo) |
| Otro dominio con el nombre del banco (`bbva.es`, `bbva-seguridad.test`) | **MEDIO, como incertidumbre**: «puede ser suyo o una imitación» (`url.brand_name_unverified`). Con una petición de claves o pago, sube a ALTO |
| Remitente que se presenta como el banco desde otro dominio | MEDIO («no escribe desde una dirección que hayamos podido verificar») |
| Enlace no verificado en un mensaje que menciona al banco | Información (LOW): no es prueba de suplantación |

## Pendiente (requiere revisión humana)
- Completar los dominios **web y de correo** de cada banco desde fuentes oficiales de la propia entidad (páginas de seguridad o aviso legal), con fecha y fuente. Solo entonces podrá marcarse `domain_coverage: "complete"`.
- Revisar estos cinco registros (`checked_by` lo indica).
- Los alias «Santander» y «Sabadell» son ambiguos, porque también son ciudades (R-50). Una mención de la ciudad con un enlace queda en NO CONCLUYENTE sin IA, nunca en alerta.
- Organismos y empresas (Correos, Hacienda, eléctricas): sin dominios verificados. Solo `.gob.es` se trata como oficial, porque está reservado a las administraciones públicas.
