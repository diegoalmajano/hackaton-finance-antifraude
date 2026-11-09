"""Filtro rápido por reglas (nivel 1, fase b). Determinista y sin red.

Las reglas trabajan sobre el texto **plegado** (minúsculas, sin acentos) y
sobre el remitente. Cada coincidencia produce una ``Signal`` con un código
estable, una descripción para el usuario en español llano y otra técnica.
La ausencia de señales no garantiza nada: el motor de riesgo decide.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from time import perf_counter

from antifraude.analysis.text import fold
from antifraude.contracts.checks import CheckStatus
from antifraude.contracts.common import Severity
from antifraude.contracts.entities import DomainCoverage, FinancialEntity
from antifraude.contracts.messages import AuthVerdict, IncomingMessage
from antifraude.contracts.screening import ScreeningResult, Signal, SignalFamily, SignalSource
from antifraude.intel.entities import EntityDirectory
from antifraude.intel.urls import UNVERIFIED_BRAND, find_lookalike, registrable_domain

RULE_VERSION = "rules-0.3.4"

#: Negación SOLO de la propia petición («nunca le pediremos…»): tras el verbo de pedir solo pueden
#: quedar pronombres o artículos (revisión adversarial A1: «Nunca le pediremos sus datos, por eso
#: introduzca su clave» ya NO se anula).
_NEGATION = re.compile(
    r"\b(nunca|jamas|no)\b[^.!?\n:;]{0,30}\b(pedi\w*|pide\w*|pida\w*|pediran|solicit\w*|pregunt\w*|requer\w*|"
    r"exig\w*|reclam\w*)\b(\s+(le|te|les|nos|os|su|sus|tu|tus|el|la|los|las|que|a usted|de usted))*\s*$")
#: Negación directa del verbo de la petición («nunca facilite», «no debe facilitar», «evite introducir»).
_DIRECT_NEGATION = re.compile(r"\b(no|nunca|jamas|evite|evita)(\s+(me|le|te|se lo|se la|nos|les|lo|la))?"
                              r"(\s+(debe|deberia|tiene que|tienes que|hay que|debemos))?(\s+nunca)?\s*$")
#: Discurso referido: «si alguien le pide que confirme…», «los estafadores le dirán «introduzca…»».
_REPORTED = re.compile(r"\b(alguien|desconocid\w*|estafador\w*|delincuent\w*|ciberdelincuent\w*|terceros?|"
                       r"nadie|otra persona|un supuesto|una supuesta)\b[^.!?\n]{0,50}\b(le|te|les)\s+"
                       r"(pide|piden|pidan|pidiera|pedira|pediran|dira|diran|dice|dicen)(\s+que)?\s*[«\"']?\s*$")
#: Negación coordinada: «no pague ni transfiera», dentro de su propia cláusula.
_COORDINATED_NEGATION = re.compile(r"\b(no|nunca|jamas|evite|evita)\b[^.!?\n:;]{0,60}\bni( tampoco)?\s*$")
#: Cortes de cláusula además de la puntuación fuerte.
_CLAUSE_CUT = re.compile(r"[.!?\n:;]|\b(por eso|asi que|pero|sin embargo|aun asi|sino|solo|para su tranquilidad|ahora)\b")
_NO_NEED = re.compile(r"\b(no es necesario|no hace falta|no tiene que|no tienes que|no necesita|no debe|"
                      r"sin necesidad de)\b[^.!?\n:;,]{0,40}$")
#: «nada»/«ningún pago» solo anula si es el OBJETO del verbo de pago («no pague nada»), no «sin ningún recargo».
_NEGATED_SPAN = re.compile(r"^\S+\s+(nada|ningun\w*\s+(pago|importe|cantidad|dinero|cargo))\b")

_REQUEST_VERB = (
    r"\b(introduzca|introduce|introducir|introduciendo|indique|indica|facilite|facilita|facilitar|confirme|confirma|"
    r"confirmar|verifique|verifica|verificar|envie|envia|enviar|mande|manda|mandar|responda|responde|dime|digame|"
    r"actualice|actualiza|actualizar|escriba|escribe|proporcione|proporciona|comparta|comparte|valide|valida|validar|"
    r"rellene|rellena|complete|completa|identifiquese|reactive|reactiva|reactivar|acceda e|accede e|inicie sesion|"
    r"inicia sesion|ingrese|necesit\w*|acced\w* con|entre con|comuniq\w*|digale|facilitenos|indiquenos|envienos|"
    r"tecle\w*|aporte|aporta|remita|remite|remitiera|remitirnos|"
    # formas con pronombre pegado (revisión adversarial A2/A3)
    r"enviarnos|envianos|facilitarnos|facilitanos|indicarnos|indicanos|confirmarnos|confirmenos|pasame|pasamelo|"
    r"pasarnos|pasanos|pasenos|pasas|diganos|dinos|mandame|mandanos|reenviame|reenvienos|renueve|renueva|renuevela|"
    r"compart(?:a|e)(?:me|nos)|envi(?:a|e)me|"
    # subjuntivo de tú («te pide que nos envíes…») y otras formas (revisión adversarial ronda 3, A5/A7)
    r"envies|mandes|pases|indiques|facilites|confirmes|introduzcas|actualices|compartas|verifiques|digas|"
    r"pon|ponga|pongan|leamelo|leamelos|leamela|respondanos|respondenos|contestenos|devuelvanos)"
)
_CREDENTIAL_OBJECT = (
    r"(contrasena|clave(s)?( de acceso| de firma| personal| secreta| sms| de operaciones| de un solo uso)?\b|pin\b|"
    r"credenciales|usuario y contrasena|coordenadas|numero secreto|"
    r"datos (de acceso|habituales de acceso|bancarios|personales|de (la|su|tu) tarjeta)|"
    r"numero de (la |su |tu )?(tarjeta|cuenta)|(ultimos )?(\d+ )?digitos de (la|su|tu) tarjeta|cvv|cvc|"
    r"codigo de seguridad|firma (electronica|digital)|identidad con sus datos|"
    r"foto (de|del) (la |el |su |tu )?(dni|tarjeta)|datos con (los )?que (entra|accede|inicia))"
)
#: Verbos de petición que NO son «teclear en su propio servicio» (adversarial P2).
_SHARE_VERB = re.sub(r"(introduzca|introduce|introducir|introduciendo|escriba|escribe|tecle\\w\*)\|", "",
                     _REQUEST_VERB)
_CARD_OBJECT = r"(datos de (la|su|tu) tarjeta|numero de (la |su |tu )?tarjeta|fecha de caducidad|cvv|cvc)"
_OTP_OBJECT = (
    r"(codigo (que|de verificacion|de confirmacion|recibido|que le|que te|sms|de un solo uso|otp)|\botp\b|"
    r"codigo [^.\n]{0,40}(recibira|recibiras|le (hemos|acabamos de) enviad|te (hemos|acabamos de) enviad|le llegara|te llegara|(le|te) ha llegado|(le|te) va a llegar)|codigo de \d+ (cifras|digitos)|"
    # código sin la palabra «código» (A7): «el número que le aparecerá en el móvil»
    r"(numero|numeros|cifras|digitos)( de \d+ cifras)? que (le|te) (llega\w*|aparec\w*|acaba\w* de llegar|"
    r"ha\w* llegado|va\w* a llegar))"
)


@dataclass(frozen=True)
class _Rule:
    code: str
    family: SignalFamily
    severity: Severity
    pattern: re.Pattern[str]
    user: str
    tech: str
    negatable: bool = False
    no_need: bool = False  # además, «no es necesario que…» anula la regla (p. ej. pagos)


def _rx(p: str) -> re.Pattern[str]:
    return re.compile(p)


_CONTENT_RULES: tuple[_Rule, ...] = (
    _Rule("content.credential_request", SignalFamily.CONTENT, Severity.HIGH,
          _rx(_REQUEST_VERB + r"\b[^.\n]{0,120}?" + _CREDENTIAL_OBJECT),
          "Le piden claves, contraseñas o datos de acceso. Su banco nunca se los pedirá por mensaje.",
          "petición de credenciales", negatable=True),
    # Peticiones de credenciales en inglés (cobertura mínima; las reglas están pensadas para español, R-56).
    _Rule("content.credential_request_en", SignalFamily.CONTENT, Severity.HIGH,
          _rx(r"\b(enter|confirm|verify|update|provide|submit|send|reply with|log ?in with)\b[^.\n]{0,60}?"
              r"\b(password|passcode|pin|login details|card number|cvv|security code|verification code|one[- ]time code)"),
          "Le piden claves, códigos o datos de tarjeta (mensaje en inglés). Su banco nunca se los pedirá por mensaje.",
          "petición de credenciales (inglés)", negatable=True),
    # OTP: «introduce el código» para teclearlo en el propio servicio es legítimo (adversarial P2); solo cuenta
    # si se pide enviarlo, compartirlo o introducirlo en un enlace/formulario/respuesta.
    _Rule("content.otp_request", SignalFamily.CONTENT, Severity.HIGH,
          _rx(_SHARE_VERB + r"\b[^.\n]{0,70}?" + _OTP_OBJECT + r"|\b(introduzca|introduce|introducir|escriba|escribe|"
              r"tecle\w*)\b[^.\n]{0,70}?" + _OTP_OBJECT + r"[^.\n]{0,60}(enlace|aqui|formulario|respond|https?|www)"),
          "Le piden un código de verificación (de un solo uso). No lo comparta nunca.",
          "petición de OTP", negatable=True),
    _Rule("content.otp_share", SignalFamily.CONTENT, Severity.HIGH,
          _rx(r"codigo[^.!?\n]{0,60}\b(comuniq\w*|digaselo|diga\w*|dicte\w*|facilit\w*|reenvi\w*|envie\w*|mande\w*|"
              r"responda con|indiquenos|leaselo|pasamelo|pasemelo|pasanoslo|dimelo|digamelo|mandamelo|reenviamelo)\b"),
          "Le piden que comunique a otra persona un código que ha recibido. No lo comparta nunca.",
          "petición de compartir un código", negatable=True),
    # Tarjeta: exige un verbo de petición o una pregunta (adversarial P3: mencionarla no es pedirla).
    _Rule("content.card_request", SignalFamily.CONTENT, Severity.HIGH,
          _rx(_REQUEST_VERB + r"\b[^.\n]{0,60}?" + _CARD_OBJECT + r"|(cual es|digame|diganos)[^.\n]{0,30}" + _CARD_OBJECT),
          "Le piden datos de su tarjeta.", "petición de datos de tarjeta", negatable=True),
    _Rule("content.identity_data_request", SignalFamily.CONTENT, Severity.MEDIUM,
          _rx(_REQUEST_VERB + r"\b[^.\n]{0,60}?(\bdni\b|\[dni\]|fecha de nacimiento|numero de la seguridad social|"
              r"documento de identidad)"),
          "Le piden datos personales de identidad (DNI, fecha de nacimiento…).", "petición de datos de identidad",
          negatable=True),
    _Rule("content.urgency", SignalFamily.CONTENT, Severity.LOW,
          _rx(r"(urgente|inmediatamente|de inmediato|en (las proximas |los proximos |un plazo de )?\d+ ?(horas|minutos|h\b)|"
              r"antes de \d+ ?(horas|minutos|h\b)|ultimo aviso|antes de (hoy|manana|medianoche)|cuanto antes|"
              r"lo antes posible|de lo contrario|plazo de \d+|es imprescindible|hoy mismo|plazas limitadas)"),
          "Le meten prisa para que actúe sin pensar.", "lenguaje de urgencia"),
    _Rule("content.unrecognized_charge_lure", SignalFamily.CONTENT, Severity.HIGH,
          _rx(r"(si no (ha|has) sido (usted|tu)|si no (reconoce|reconoces|ha realizado|has realizado)|no ha sido usted|"
              r"si no (lo|la) (has|ha) (hecho|solicitado|autorizado|realizado))"
              r"[^\n]{0,80}(cancel|anul|bloque|rechaz|deten|pulse|acceda|llam|responda)"),
          "Le asustan con un cargo o una operación que no ha hecho para que actúe rápido.",
          "señuelo de cargo no reconocido"),
    _Rule("content.account_threat", SignalFamily.CONTENT, Severity.MEDIUM,
          _rx(r"((cuenta|tarjeta|acceso|banca|servicio)s?( de [a-z]+)? (sera|seran|ha sido|han sido|quedara|quedaran|esta|"
              r"estan) (temporalmente )?(bloquead|suspendid|cancelad|desactivad|restringid|limitad)|"
              r"(bloqueo|suspension|cancelacion|embargo) de (su|tu) (cuenta|tarjeta|acceso|vehiculo|nomina))"),
          "Le amenazan con bloquear su cuenta o tarjeta.", "amenaza de bloqueo"),
    _Rule("content.call_lure", SignalFamily.CONTENT, Severity.HIGH,
          _rx(r"\b(llam\w*|contacte\w*|contacta\w*)\b[^.\n]{0,40}\[telefono\][^.\n]{0,60}"
              r"(evitar|desbloque|cancel|anul|urgente|inmediat|tecnico|virus)|"
              r"(evitar|desbloque|cancel|anul|urgente|virus|infectad)[^.\n]{0,80}\b(llam\w*|contact\w*)\b[^.\n]{0,40}\[telefono\]"),
          "Le piden que llame con urgencia a un número que aparece en el mensaje. Use siempre el teléfono de siempre.",
          "presión para llamar a un número del mensaje"),
    _Rule("content.payment_request", SignalFamily.CONTENT, Severity.MEDIUM,
          _rx(r"(\b(realice|realiza|haga|haz|hacer|hacerme|hagas|efectue|efectua|envie|envia|enviar|enviarme|enviame|"
              r"mande|manda|mandarme|pasarme|pasar|pases|prestarme|pague|paga|pagar|pagando|abone|abona|abonar|ingrese|"
              r"ingresa|transferir|transfier(?:a|e)(?:me|nos)?|pon|ponme|envies|mandes)\b[^.\n]{0,40}"
              r"(transferencia|bizum|pago|importe|tasa|\d+[.,]?\d*\s?(€|eur|euros))|\bpague[^.\n]{0,30}tasa|"
              r"pago pendiente|deposito (inicial |minimo )?de \d+|"
              r"\b(necesito|necesitamos|necesitaria|necesitariamos) [^.\n]{0,20}\d+[.,]?\d*\s?(€|eur|euros)|"
              r"(compr|adquier)\w*[^.\n]{0,40}(tarjetas? regalo|paysafecard|tarjetas? prepago)|"
              r"\b(hazme|ingresame|ingresarme|prestame|prestes|presta|devuelveme|abonelo|abonela|abonarlo)\b[^.\n]{0,40}"
              r"(\d+[.,]?\d*\s?(€|eur|euros)|bizum|transferencia|importe)|"
              r"actualic\w* (su|tu) (metodo|datos|forma) de pago|(fianza|senal|gastos (notariales|de gestion|de envio)) de \d+|"
              r"para (recibir|cobrar)[^.\n]{0,40}acept\w* (la )?solicitud)"),
          "Le piden que pague o envíe dinero.", "petición de pago", negatable=True, no_need=True),
    _Rule("content.debt_lure", SignalFamily.CONTENT, Severity.MEDIUM,
          _rx(r"(si no paga|multa [^.\n]{0,30}(pendiente|sin pagar)|tasa de (aduana|envio|gestion)|deuda pendiente|"
              r"sancion pendiente|retenid\w* por (falta de )?(pago|franqueo|tasas?))"),
          "Le reclaman una multa, deuda o tasa y le dan un enlace o teléfono para pagarla. Compruébelo por la web "
          "oficial del organismo, escribiéndola usted mismo.", "reclamación de pago con enlace o teléfono"),
    _Rule("content.login_lure", SignalFamily.CONTENT, Severity.LOW,
          _rx(r"\b(inicie|inicia|acceda|accede|verifique|verifica|valide|valida|confirme|confirma|identifiquese|"
              r"evitelo|evitalo|reactive|reactiva)\b[^.\n]{0,40}(sesion|su cuenta|tu cuenta|su identidad|tu identidad|"
              r"sus datos|tus datos|enlace)"),
          "Le piden que entre en su cuenta o confirme su identidad desde el mensaje.", "invitación a iniciar sesión"),
    _Rule("content.secrecy", SignalFamily.CONTENT, Severity.MEDIUM,
          _rx(r"(no se lo digas|no le digas nada|es confidencial|no lo comentes|mantenlo en secreto|no se lo cuentes|"
              r"no se lo diga|no lo comente)"),
          "Le piden que lo mantenga en secreto: los estafadores quieren evitar que alguien le avise.", "petición de secreto"),
    _Rule("content.credential_expiry", SignalFamily.CONTENT, Severity.HIGH,
          _rx(r"((clave|contrasena|credenciales|firma( electronica)?) (ha|han) caducad|"
              r"(clave|contrasena|firma)[^.\n]{0,20}caduca hoy|renuev\w* (su|tu|sus|tus) (clave|contrasena|credenciales|firma))"),
          "Le dicen que su clave ha caducado para que la «renueve» donde ellos digan.", "clave caducada"),
    _Rule("content.safe_account_lure", SignalFamily.CONTENT, Severity.HIGH,
          _rx(r"(cuenta segura|transferir todo su dinero|(policia|guardia civil)[^.\n]{0,80}(transfer|cuenta))"),
          "Le piden mover su dinero a una «cuenta segura». Ningún banco ni policía lo pide.", "cuenta segura"),
    _Rule("context.public_body", SignalFamily.CONTEXT, Severity.LOW,
          _rx(r"\b(hacienda|aeat|agencia tributaria|dgt|trafico|seguridad social|correos|policia|guardia civil)\b"),
          "Dice venir de un organismo público.", "organismo público mencionado"),
    _Rule("content.payment_details_change", SignalFamily.CONTENT, Severity.HIGH,
          _rx(r"(nuev[oa] (numero de )?(cuenta|iban)|cambio de (cuenta|iban|datos bancarios)|"
              r"(hemos cambiado|ha cambiado|cambiado) (de )?(nuestra |la )?(cuenta|iban|entidad bancaria)|"
              # IBAN enmascarado («…» se pliega a «...») SOLO con contexto de cambio o novedad (revisión Etapa B)
              r"(nuev\w*|cambi\w*|actualizad\w*|a partir de ahora|desde ahora)[^.!?\n]{0,60}\[iban [a-z]{2} \.\.\.|"
              r"\[iban [a-z]{2} \.\.\.[^\]]*\][^.!?\n]{0,40}(nuev\w*|cambi\w*|a partir de ahora))"),
          "Le indican una cuenta bancaria nueva o diferente para pagar.", "cambio de datos de pago"),
    # Bizum inverso / solicitud de dinero disfrazada de cobro: para RECIBIR dinero nunca hay que aceptar una
    # solicitud; aceptarla es pagar. Puede cruzar una frase («…para recibir el reembolso. Acéptela…»), pero no
    # un salto de línea. Tipología pública (avisos de INCIBE/OSI y del Banco de España); ver ``_ACCEPT_NEGATED``.
    _Rule("content.reverse_payment_request", SignalFamily.CONTENT, Severity.HIGH,
          _rx(r"solicitud(es)? de (bizum|pago|dinero|cobro)[^\n]{0,120}?\b(para (recibir|cobrar|que (se )?le ingres|"
              r"que (te|le) llegue)|reembols\w*|devoluc\w*|ingres\w*)[^\n]{0,120}?\b(acept|autoric|aprueb|aprob)\w*|"
              r"\b(para (recibir|cobrar)|reembols\w*|devoluc\w*)[^\n]{0,120}?\b(acept|autoric|aprueb|aprob)\w*"
              r"[^\n]{0,40}\bsolicitud|"
              r"\b(acept|autoric|aprueb|aprob)\w*[^\n]{0,40}\bsolicitud(es)? de (bizum|pago|dinero|cobro)[^\n]{0,80}"
              r"(para (recibir|cobrar|que (se )?(te|le) (llegue|ingres))|reembols|devoluc|ingres)"),
          "Le piden que acepte una solicitud de Bizum o de pago para «recibir» dinero. Aceptar una solicitud es "
          "PAGAR: para cobrar nunca tiene que aceptar nada.", "solicitud de pago disfrazada de cobro (Bizum inverso)",
          negatable=True),
    _Rule("content.investment_promise", SignalFamily.CONTENT, Severity.HIGH,
          _rx(r"(rentabilidad(es)? (garantizad|asegurad)|(duplic|tripl|multiplic)\w* (su|tu) (dinero|inversion)|"
              r"sin (ningun )?riesgo|ganancias? (garantizad|diari|semanal)|beneficios? garantizad|"
              r"invierta (ahora|hoy)|oportunidad unica de inversion|invi?e?rt\w* \d+|gan\w* hasta \d+|"
              r"\d+[.,]?\d* ?(€|euros) al (mes|dia)|inversion inicial|recibir \d+[.,]?\d* (millones|mil))"),
          "Le prometen ganancias garantizadas o sin riesgo.", "promesa de inversión"),
    _Rule("content.prize_or_refund", SignalFamily.CONTENT, Severity.MEDIUM,
          _rx(r"(ha (sido )?(ganado|premiad|seleccionad)|has (ganado|sido seleccionad)|reembolso|devolucion pendiente|"
              r"tiene (un|una) (premio|devolucion|reembolso)|devolucion de [^.\n]{0,20}(€|euros)|derecho a (una )?devolucion)"),
          "Le ofrecen un premio o una devolución de dinero.", "premio o reembolso"),
    _Rule("content.family_new_number", SignalFamily.CONTENT, Severity.HIGH,
          _rx(r"((mama|papa|abuela|abuelo|hijo|hija)\b[^.\n]{0,60}(numero nuevo|nuevo numero|movil nuevo|se me ha (roto|caido|perdido))|"
              r"(numero nuevo|nuevo numero|este es mi nuevo)[^.\n]{0,60}(mama|papa|hijo|hija))"),
          "Alguien dice ser un familiar con un número nuevo.", "suplantación de familiar"),
    _Rule("content.remote_access", SignalFamily.CONTENT, Severity.HIGH,
          _rx(r"(anydesk|teamviewer|acceso remoto|control remoto|instal\w* (esta|la) (aplicacion|app)|"
              r"descargue (esta|la) (aplicacion|app)|(virus|infectad\w*)[^.\n]{0,80}(tecnico|llam\w*)|"
              r"\b(instal|descarg)\w* (la |el |esta |este |nuestra |nuestro |una |un )?(herramienta|programa|software)"
              r"( de (asistencia|soporte|control))?)"),
          "Le piden instalar un programa o dar acceso remoto a su dispositivo.", "acceso remoto"),
    _Rule("content.injection_attempt", SignalFamily.CONTENT, Severity.HIGH,
          _rx(r"(ignor[ae]n? (todas )?(tus|las|sus) instrucciones|ignore (all |the )?(previous|prior|above) instructions|"
              r"clasifi(?:ca|que) (este|el) mensaje como|mar(?:ca|que) (este|el) mensaje como (seguro|legitimo)|system prompt|"
              r"eres un (asistente|modelo)|you are (an?|the) (assistant|ai)|instrucciones (para|al) (la )?ia)"),
          "El mensaje contiene órdenes ocultas dirigidas a programas de inteligencia artificial.",
          "intento de inyección de instrucciones"),
)

_EXEC_EXT = re.compile(r"\.(exe|scr|js|jse|vbs|vbe|bat|cmd|msi|ps1|hta|jar|com|pif|iso|img|lnk)$", re.IGNORECASE)


def _signal(code: str, family: SignalFamily, severity: Severity, user: str, tech: str,
            source: SignalSource = SignalSource.RULE) -> Signal:
    return Signal(code=code, family=family, severity=severity, source=source,
                  description_user=user, description_tech=tech)


def _is_negated(folded: str, start: int, end: int, no_need: bool) -> bool:
    """¿La coincidencia está negada en su propia cláusula?

    - «nunca le pediremos (que) …» (negación del verbo de pedir, seguido solo de pronombres/artículos);
    - «nunca facilite / no debe facilitar / evite introducir …» (negación directa del verbo de la petición);
    - «si alguien le pide que…» / «le dirán «introduzca…»» (discurso referido: es un consejo, no una petición).
    Los conectores «por eso», «así que», «pero», «solo»… cortan la cláusula (revisión adversarial A1).
    """
    window = folded[max(0, start - 100):start]
    parts = _CLAUSE_CUT.split(window)
    clause = parts[-1] if parts else window
    if any(p.search(clause) for p in (_NEGATION, _DIRECT_NEGATION, _COORDINATED_NEGATION, _REPORTED)):
        return True
    span = folded[start:end]
    if no_need and (_NO_NEED.search(clause + " ") or _NEGATED_SPAN.search(span)):
        return True
    return False


#: Remisión a canales oficiales: no es un señuelo (adversarial P4).
_OFFICIAL_CHANNEL = re.compile(r"(reverso de (su|tu) tarjeta|telefono (habitual|de siempre)|el de siempre|app oficial|"
                               r"desde la app|en la app|su oficina|cajero)")
_EXPIRY_CONTEXT = re.compile(r"(caduc|valid|expir)\w*[^.\n]{0,15}$")


#: Instrucción de pagar o ingresar dirigida al lector (o en pasiva: «deberá abonarse»).
_PAY_INSTRUCTION = re.compile(
    r"\b(abon(e|en|ar|arse|elo|ela)|ingres(e|en|a|ar|arlo)|transfier\w*|transferir|pagu(e|en)|pagar|"
    r"deposit(e|en|ar)|domicili(e|en|ar)|(realic|efectu|hag)\w* (el|los) (pagos?|abonos?|ingresos?))\b|"
    r"(el|los) pagos? (se realizara|debe|debera|deberan)|(debe|deberan?|deben) abonarse")
_NOTHING_TO_DO = re.compile(r"no (tiene|tienes|necesita|necesitas) que hacer nada|no es necesario que haga nada")
_REFUND_DONE = re.compile(r"\b(ha sido|se ha|hemos|has|ha) (tramitad|procesad|abonad|reembolsad|recibid|realizad)o\b")
_NOVELTY = re.compile(r"\b(nuev\w*|cambi\w*|anterior|cancelad\w*|anulad\w*|a partir de|desde este|en lugar de|"
                      r"ya no|otra cuenta|cuenta de mi)\b")
_CALL_TO_ACTION = re.compile(r"\b(acced\w*|consult\w*|puls\w*|haga clic|pinch\w*|siga|complete|regularic\w*|"
                             r"abon\w*|pagu\w*|pagando|descargu\w*|actualic\w*|verifiqu\w*|entre|visite|recib\w*)\b")
_USUAL = re.compile(r"\b(de siempre|habitual)\b")
#: Consejo, no petición: «si recibe una solicitud de Bizum para cobrar, NO la acepte» (la negación va DENTRO
#: de la coincidencia, después de «solicitud», y ``_is_negated`` solo mira antes).
_ACCEPT_NEGATED = re.compile(r"\b(no|nunca|jamas)\s+((la|lo|las|los|le|se|debe|deben|tiene|tienes|hay|necesita|"
                             r"necesitas|que|es necesario|hace falta)\s+){0,3}(acept|autoric|aprueb|aprob)\w*|"
                             r"\bsin (tener que |necesidad de )?(acept|autoriz|aprob)\w*")


def _matches(pattern: re.Pattern[str], text: str, limit: int = 40) -> list[re.Match[str]]:
    """Coincidencias que pueden SOLAPARSE: tras una coincidencia se busca de nuevo desde su inicio + 1.

    Así, en «No confirme nada por teléfono; confirme su clave en…», si la primera coincidencia está negada,
    la segunda petición se evalúa por separado (revisión adversarial ronda 3, A1). Acotado a ``limit``.
    """
    out: list[re.Match[str]] = []
    pos = 0
    while len(out) < limit:
        m = pattern.search(text, pos)
        if m is None:
            break
        out.append(m)
        pos = m.start() + 1
    return out


def _has_payment_instruction(folded: str) -> bool:
    """Un IBAN no convierte un consejo negado en una orden de pago."""
    return any(not _is_negated(folded, m.start(), m.end(), no_need=True)
               for m in _matches(_PAY_INSTRUCTION, folded))


def _iban_payment(folded: str, signals: list[Signal]) -> None:
    """IBAN + instrucción de pago (A6). Con novedad o anulación de la cuenta anterior → cambio de cuenta (ALTO);
    sin ella → petición de pago a una cuenta (MEDIO). «La de siempre / habitual» lo desactiva."""
    if "[iban " not in folded or not _has_payment_instruction(folded) or _USUAL.search(folded):
        return
    codes = {s.code for s in signals}
    if _NOVELTY.search(folded) and not _NOTHING_TO_DO.search(folded):
        if "content.payment_details_change" not in codes:
            signals.append(_signal("content.payment_details_change", SignalFamily.CONTENT, Severity.HIGH,
                                   "Le indican una cuenta bancaria nueva o diferente para pagar.",
                                   "IBAN con instrucción de pago y cambio de cuenta"))
    elif "content.payment_request" not in codes:
        signals.append(_signal("content.payment_request", SignalFamily.CONTENT, Severity.MEDIUM,
                               "Le piden que pague o ingrese dinero en una cuenta bancaria.",
                               "IBAN con instrucción de pago"))


_ES_WORDS = frozenset("de la que el en y los su por para con una es se del las le no un al lo como mas pero sus "
                      "este esta usted su sea muy ya".split())


def _looks_non_spanish(folded: str) -> bool:
    words = re.findall(r"[a-z]+", folded)
    if len(words) < 8:
        return False
    return sum(w in _ES_WORDS for w in words) / len(words) < 0.06


def mentioned_entities(text: str, directory: EntityDirectory) -> list[FinancialEntity]:
    """Entidades del directorio cuyo nombre o alias aparece como palabra completa en ``text``."""
    folded = fold(text)
    found: list[FinancialEntity] = []
    for entity in directory.all():
        for name in [entity.official_name, *entity.aliases]:
            n = fold(name)
            if re.search(r"(?<![\w])" + re.escape(n) + r"(?![\w])", folded):
                found.append(entity)
                break
    return found


def screen(message: IncomingMessage, directory: EntityDirectory) -> tuple[ScreeningResult, list[FinancialEntity]]:
    """Aplica las reglas y devuelve el resultado del filtro y las entidades mencionadas."""
    t0 = perf_counter()
    visible = (message.subject or "") + "\n" + message.text
    folded = fold(visible)
    signals: list[Signal] = []

    has_link_or_phone = bool(message.urls) or "[telefono]" in folded
    for rule in _CONTENT_RULES:
        for m in _matches(rule.pattern, folded):
            if rule.negatable and _is_negated(folded, m.start(), m.end(), rule.no_need):
                continue
            if rule.code == "content.debt_lure" and not has_link_or_phone:
                continue
            if rule.code == "content.payment_request" and re.search(r"en efectivo", folded[m.start():m.end() + 30]):
                continue
            if rule.code == "content.payment_details_change" and (not _has_payment_instruction(folded)
                                                                 or _NOTHING_TO_DO.search(folded)):
                continue  # «su nueva cuenta ya está operativa» informa; solo es riesgo si le piden pagar allí (B1)
            if rule.code == "content.reverse_payment_request" and _ACCEPT_NEGATED.search(
                    folded[max(0, m.start() - 40):m.end() + 5]):
                continue
            if rule.code == "content.prize_or_refund" and _REFUND_DONE.search(folded):
                continue
            if rule.code == "content.account_threat" and _OFFICIAL_CHANNEL.search(folded[m.end():m.end() + 120]):
                continue
            if rule.code == "content.urgency" and _EXPIRY_CONTEXT.search(folded[max(0, m.start() - 25):m.start()]):
                continue  # «el código caduca en 10 minutos» no es presión (adversarial P2)
            if rule.code in ("content.unrecognized_charge_lure", "content.call_lure") and _OFFICIAL_CHANNEL.search(
                    folded[m.start():m.end() + 80]):
                continue
            signals.append(_signal(rule.code, rule.family, rule.severity, rule.user, rule.tech))
            break

    _iban_payment(folded, signals)
    # Organismo público + enlace + llamada a la acción: sin dominios verificados de organismos (salvo «.gob.es»,
    # reservado a las administraciones públicas) no se puede afirmar que el enlace sea oficial (A4).
    if any(s.code == "context.public_body" for s in signals) and message.urls and _CALL_TO_ACTION.search(folded):
        hosts = [u.host for u in message.urls if u.host]
        if not hosts or not all(h.endswith(".gob.es") for h in hosts):
            signals.append(_signal("content.public_body_link", SignalFamily.CONTENT, Severity.MEDIUM,
                                   "Dice venir de un organismo público y le pide actuar desde un enlace que no podemos "
                                   "confirmar que sea oficial. Entre escribiendo usted mismo la web del organismo.",
                                   "organismo público + enlace no verificado + llamada a la acción"))

    if any("invisibles" in w for w in message.parse_warnings):
        signals.append(_signal("content.invisible_chars", SignalFamily.CONTENT, Severity.MEDIUM,
                               "El mensaje contenía caracteres ocultos.", "caracteres invisibles eliminados"))
    if any(w.startswith("Texto oculto") for w in message.parse_warnings):
        signals.append(_signal("content.obfuscation", SignalFamily.CONTENT, Severity.MEDIUM,
                               "El mensaje intenta esconder parte de su contenido (texto oculto o letras disfrazadas).",
                               "ofuscación: texto oculto en HTML, alfabetos mezclados o enlaces con código"))

    if _looks_non_spanish(folded):
        signals.append(_signal("context.non_spanish", SignalFamily.CONTEXT, Severity.LOW,
                               "El mensaje no parece estar en español: algunas comprobaciones del texto podrían no detectarlo todo.",
                               "idioma probablemente no español"))

    # --- Remitente --------------------------------------------------------------
    sender = message.sender
    display_and_text = (sender.display_name or "") + "\n" + visible
    entities = mentioned_entities(display_and_text, directory)
    claimed = mentioned_entities(sender.display_name or "", directory)
    sender_official = directory.official_entity_for_host(sender.domain) if sender.domain else None

    for entity in claimed:
        if entity.official_domains and (sender_official is None or sender_official.entity_id != entity.entity_id):
            partial = entity.domain_coverage is DomainCoverage.PARTIAL
            signals.append(_signal("sender.brand_mismatch", SignalFamily.SENDER,
                                   Severity.MEDIUM if partial else Severity.HIGH,
                                   f"El remitente se presenta como {entity.official_name}, pero no escribe desde "
                                   + ("una dirección suya que hayamos podido verificar." if partial
                                      else "su dirección oficial."),
                                   f"display_name menciona {entity.entity_id}; dominio {sender.domain}"))
    # El cuerpo habla en nombre de una entidad, pero el correo no viene de su dominio oficial (revisión Etapa B).
    if sender.domain and not claimed:
        body_entities = mentioned_entities(visible, directory)
        for entity in body_entities:
            if entity.official_domains and (sender_official is None or sender_official.entity_id != entity.entity_id):
                # Severidad BAJA: mencionar un banco no es suplantarlo; solo corrobora peticiones sensibles.
                signals.append(_signal("sender.body_brand_mismatch", SignalFamily.SENDER, Severity.LOW,
                                       f"El mensaje menciona a {entity.official_name}, pero no procede de su dirección oficial.",
                                       f"cuerpo menciona {entity.entity_id}; dominio {sender.domain}"))
                break
    for role, dom in (("remitente", sender.domain), ("respuesta", message.reply_to.domain if message.reply_to else None)):
        found = find_lookalike(dom, directory) if dom else None
        if found and found[0] == UNVERIFIED_BRAND:
            signals.append(_signal("sender.brand_name_unverified", SignalFamily.SENDER, Severity.MEDIUM,
                                   "La dirección de correo usa el nombre de una entidad, pero no figura entre sus "
                                   "direcciones verificadas: puede ser suya o una imitación.",
                                   f"dominio de {role} {dom} contiene la marca de {found[1]} (lista parcial)"))
            break
        if found:
            signals.append(_signal("sender.lookalike_domain", SignalFamily.SENDER, Severity.CRITICAL,
                                   "La dirección de correo imita la de una entidad, pero no es la oficial.",
                                   f"dominio de {role} {dom} imita {found[1]}"))
            break
    if message.reply_to and message.reply_to.domain and sender.domain:
        if registrable_domain(message.reply_to.domain) != registrable_domain(sender.domain):
            signals.append(_signal("sender.reply_to_mismatch", SignalFamily.SENDER, Severity.MEDIUM,
                                   "Si responde, su respuesta irá a una dirección distinta de la del remitente.",
                                   f"reply-to {message.reply_to.domain} ≠ from {sender.domain}"))
    auth = sender.auth
    if auth.header_present:
        if auth.dmarc in (AuthVerdict.FAIL,):
            signals.append(_signal("sender.dmarc_fail", SignalFamily.SENDER, Severity.HIGH,
                                   "El correo no supera las comprobaciones que confirman quién lo envía.",
                                   "DMARC fail"))
        elif auth.spf in (AuthVerdict.FAIL, AuthVerdict.SOFTFAIL):
            signals.append(_signal("sender.spf_fail", SignalFamily.SENDER, Severity.MEDIUM,
                                   "El servidor que envió el correo no está autorizado por el dominio del remitente.",
                                   f"SPF {auth.spf}"))

    for att in message.attachments:
        if _EXEC_EXT.search(att.filename):
            signals.append(_signal("content.dangerous_attachment", SignalFamily.CONTENT, Severity.HIGH,
                                   "Trae un archivo adjunto que podría instalar un programa malicioso. No lo abra.",
                                   f"adjunto ejecutable {att.filename[:60]}"))
            break

    if entities:
        signals.append(_signal("context.entity_mentioned", SignalFamily.CONTEXT, Severity.LOW,
                               f"Menciona a {entities[0].official_name}.",
                               "entidades mencionadas: " + ", ".join(e.entity_id for e in entities)))

    # Entidad «reclamada»: primero la del nombre del remitente; si no, las mencionadas en el texto.
    entities = claimed + [e for e in entities if e not in claimed]
    signals = _dedupe(signals)
    max_sev = max((s.severity for s in signals), key=lambda s: s.rank, default=None)
    risky = [s for s in signals if s.severity.rank >= Severity.MEDIUM.rank]
    # Mención de una entidad + algún enlace que NO es de un dominio oficial verificado → análisis profundo.
    unofficial_links = [u for u in message.urls if not (u.host and directory.official_entity_for_host(u.host))]
    needs_deep = bool(risky) or (bool(entities) and bool(unofficial_links))
    preliminary = any(s.severity.rank >= Severity.HIGH.rank for s in signals)
    result = ScreeningResult(
        message_id=message.id,
        status=CheckStatus.DONE,
        signals=signals,
        max_severity=max_sev,
        needs_deep_analysis=needs_deep or preliminary,
        preliminary_alert_required=preliminary,
        rule_version=RULE_VERSION,
        latency_ms=int((perf_counter() - t0) * 1000),
    )
    return result, entities


def _dedupe(signals: list[Signal]) -> list[Signal]:
    seen: set[str] = set()
    out: list[Signal] = []
    for s in signals:
        if s.code in seen:
            continue
        seen.add(s.code)
        out.append(s)
    return out
