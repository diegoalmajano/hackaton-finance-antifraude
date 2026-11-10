# Valor diferencial: comparación documental y hipótesis a validar

Revisión de fuentes primarias oficiales: **10-11-2026**. Es una comparación de enfoques, no un ensayo de eficacia ni un catálogo exhaustivo. Funciones, licencias y configuraciones de las alternativas pueden variar. No se han enviado casos ni mensajes a estos servicios para preparar este documento.

## Qué ya ofrecen otras soluciones

| Enfoque y ejemplo | Capacidad descrita por el proveedor | Relación con el prototipo |
|---|---|---|
| Filtro del correo: Gmail | Identificación automática de phishing, advertencias y consejos de comprobación. La propia ayuda recomienda cautela aunque no aparezca un aviso. [Ayuda oficial](https://support.google.com/mail/answer/8253?hl=es). | Ya existe protección en el buzón y orientación al usuario. No sería defendible afirmar que los filtros nunca explican riesgos o que nuestro MVP detecta lo que Gmail no puede detectar. |
| Navegación protegida: Google Safe Browsing | Avisos ante sitios o descargas peligrosas; también se integra con productos como Gmail. La protección mejorada añade comprobaciones y puede implicar compartir información adicional de seguridad. [Descripción oficial](https://safebrowsing.google.com/). | Nuestro análisis pasivo describe señales del mensaje y del enlace sin abrirlo; no ofrece la reputación ni el análisis de destinos/archivos de ese servicio, y no debe sustituirlo. |
| Protección de enlaces de empresa: Microsoft Defender Safe Links | Escaneo de URL, reescritura de enlaces y comprobación al hacer clic, según producto y política empresarial. [Documentación oficial](https://learn.microsoft.com/en-us/defender-office-365/safe-links-about). | Muestra una alternativa empresarial con controles de enlaces documentados. No hemos comparado cobertura, falsos positivos, latencia ni costes equivalentes. |
| Asistente generativo de propósito amplio: Microsoft Copilot Chat | Conversación, redacción, búsqueda y síntesis con contexto/fuentes; Microsoft reconoce que puede equivocarse y pide verificar resultados antes de utilizarlos. [FAQ oficial](https://support.microsoft.com/en-us/microsoft-365-copilot/frequently-asked-questions-about-microsoft-365-copilot-chat), [guía oficial de validación](https://support.microsoft.com/en-gb/microsoft-365-copilot/validate-copilot-output). | Puede ayudar a interpretar un mensaje y un prompt puede pedir niveles y consejos. Nuestra propuesta se apoya en un flujo de producto y un motor determinista explícito, no en afirmar que un asistente genérico sea incapaz de dar esas respuestas. |

Las referencias corresponden a productos y variantes concretas. La tabla no permite generalizar sus políticas de datos ni demuestra superioridad de privacidad en cualquier escenario.

## Aportación concreta que sí puede demostrarse

El prototipo ofrece un recorrido local específico en español: introducir texto o .eml, obtener BAJO/MEDIO/ALTO/NO CONCLUYENTE, entender el motivo y recibir una acción segura. Separa evidencias de incertidumbres, declara análisis parcial y conserva la decisión humana. El motor aplica criterios deterministas sobre texto, remitente y enlaces; la IA es opcional y no fija por sí sola el nivel. Véanse [arquitectura](ARQUITECTURA.md), [ADR-0006](adr/0006-motor-riesgo-determinista.md) y [limitaciones](LIMITACIONES_DETECCION.md).

La demostración manual funciona con datos sintéticos y sin llamadas de IA. Se han implementado minimización, análisis pasivo de enlaces y controles de sesión/consentimiento. Gmail tiene puente al panel y compatibilidad probada con dobles; **la recepción de una cuenta real y Claude real no están verificadas** en la evidencia de este cierre. No es protección permanente del escritorio ni un sistema que bloquee pagos.

**Inferencia de posicionamiento, todavía a validar:** un recorrido preparado que muestre nivel, motivo y acción podría exigir menos decisiones que redactar y evaluar una conversación abierta. Esa ventaja de comprensión no se deduce del código: debe observarse con personas mediante [la hoja de revisión](REVISION_HUMANA_MVP.md). Tampoco se ha demostrado que mejore la detección o la experiencia de los filtros ya instalados.

## Hipótesis B2B y evidencia que falta

| Hipótesis de negocio | Comprobación necesaria antes de afirmarla |
|---|---|
| Un banco podría distribuir una ayuda de comprensión y prevención del fraude para sus clientes | Entrevistas y piloto consentido con responsables y usuarios; necesidad real, canal y condiciones de despliegue |
| Una explicación y una acción claras podrían reducir decisiones peligrosas | Estudio de comprensión con errores/tiempos y comparación previamente definida; resultados de uso, no solo intención declarada |
| La solución podría aportar valor adicional junto a filtros existentes | Evaluación independiente de cobertura y falsas alarmas en tareas comparables, sin reutilizar dev para validar |
| Podría existir ahorro o disposición a pagar | Datos de costes, soporte, integración y resultados de piloto; validar precio/compra con quien decide |

En esta revisión no se aportan contratos, ventas, ahorro, reducción real de fraude ni disposición a pagar demostrados. B2B es una propuesta de validación, no un cliente conseguido. El prototipo no se presenta como preparado para uso bancario comercial.

## Discurso permitido para el jurado

«Hemos construido una ayuda local para interpretar mensajes financieros: combina señales de texto, remitente y enlaces, declara lo que no ha podido comprobar y propone un siguiente paso seguro. Queremos probar si ese recorrido facilita la comprensión; hoy mostramos una demo reproducible y reconocemos que la evaluación humana independiente y las integraciones reales siguen pendientes.»

Evitar «mejor que Gmail/Copilot», «detecta todas las estafas», «evita pérdidas», «99 % de eficacia», «privacidad garantizada» o «protección automática permanente»: ninguna de esas afirmaciones está acreditada por esta comparación. El valor que se propone es complementar las protecciones existentes con un recorrido comprensible y controles explícitos, sujeto a validación.
