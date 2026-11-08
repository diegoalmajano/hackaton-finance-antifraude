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
from antifraude.contracts.entities import FinancialEntity
from antifraude.contracts.messages import AuthVerdict, IncomingMessage
from antifraude.contracts.screening import ScreeningResult, Signal, SignalFamily, SignalSource
from antifraude.intel.entities import EntityDirectory
from antifraude.intel.urls import registrable_domain

RULE_VERSION = "rules-0.1.0"

#: Negación SOLO de la propia petición («nunca le pediremos…», «no le solicitaremos…»). Revisión Etapa B:
#: una negación genérica («No le demore: introduzca su clave») ya no anula la regla.
_NEGATION = re.compile(
    r"\b(nunca|jamas|no)\b[^.!?\n:;]{0,30}\b(pedi\w*|pide\w*|pida\w*|pediran|solicit\w*|pregunt\w*|requer\w*|"
    r"exig\w*|reclam\w*)\b[^.!?\n:;]{0,40}$")
_NO_NEED = re.compile(r"\b(no es necesario|no hace falta|no tiene que|no tienes que|no necesita|no debe|"
                      r"sin necesidad de)\b[^.!?\n:;]{0,40}$")
_NEGATED_SPAN = re.compile(r"\b(ningun|ninguna|nada)\b")

_REQUEST_VERB = (
    r"\b(introduzca|introduce|introducir|indique|indica|facilite|facilita|facilitar|confirme|confirma|confirmar|"
    r"verifique|verifica|verificar|envie|envia|enviar|mande|manda|mandar|responda|responde|dime|digame|"
    r"actualice|actualiza|actualizar|escriba|escribe|proporcione|proporciona|comparta|comparte|valide|valida|validar|"
    r"rellene|rellena|complete|completa|identifiquese|reactive|reactivar|acceda e|accede e|inicie sesion|ingrese|"
    r"necesit\w*|acced\w* con|entre con|comuniq\w*|digame|digale|facilitenos|indiquenos|envienos|"
    r"tecle\w*|aporte|aporta|remita|remite)"
)
_CREDENTIAL_OBJECT = (
    r"(contrasena|clave(s)?( de acceso| de firma| personal| secreta)?\b|pin\b|credenciales|usuario y contrasena|"
    r"datos (de acceso|habituales de acceso|bancarios|de (la|su|tu) tarjeta)|numero de (la |su |tu )?tarjeta|cvv|cvc|"
    r"codigo de seguridad|firma (electronica|digital)|identidad con sus datos)"
)
_OTP_OBJECT = (
    r"(codigo (que|de verificacion|de confirmacion|recibido|que le|que te|sms|de un solo uso|otp)|\botp\b|"
    r"codigo [^.\n]{0,40}(recibira|recibiras|le (hemos|acabamos de) enviad|te (hemos|acabamos de) enviad|le llegara|te llegara))"
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
    _Rule("content.otp_request", SignalFamily.CONTENT, Severity.HIGH,
          _rx(_REQUEST_VERB + r"\b[^.\n]{0,70}?" + _OTP_OBJECT),
          "Le piden un código de verificación (de un solo uso). No lo comparta nunca.",
          "petición de OTP", negatable=True),
    _Rule("content.otp_share", SignalFamily.CONTENT, Severity.HIGH,
          _rx(r"codigo[^.!?\n]{0,60}\b(comuniq\w*|digaselo|diga\w*|dicte\w*|facilit\w*|reenvi\w*|envie\w*|mande\w*|"
              r"responda con|indiquenos|leaselo)\b"),
          "Le piden que comunique a otra persona un código que ha recibido. No lo comparta nunca.",
          "petición de compartir un código", negatable=True),
    _Rule("content.card_request", SignalFamily.CONTENT, Severity.HIGH,
          _rx(r"(datos de (la|su|tu) tarjeta|numero de (la |su |tu )?tarjeta|fecha de caducidad|cvv|cvc)"),
          "Le piden datos de su tarjeta.", "referencia a datos de tarjeta", negatable=True),
    _Rule("content.urgency", SignalFamily.CONTENT, Severity.MEDIUM,
          _rx(r"(urgente|inmediatamente|de inmediato|en (las proximas |los proximos |un plazo de )?\d+ (horas|minutos)|"
              r"antes de \d+ (horas|minutos)|ultimo aviso|antes de (hoy|manana|medianoche)|cuanto antes|"
              r"lo antes posible|de lo contrario|plazo de \d+|es imprescindible)"),
          "Le meten prisa para que actúe sin pensar.", "lenguaje de urgencia"),
    _Rule("content.unrecognized_charge_lure", SignalFamily.CONTENT, Severity.HIGH,
          _rx(r"(si no (ha|has) sido (usted|tu)|si no (reconoce|reconoces|ha realizado|has realizado)|no ha sido usted)"
              r"[^\n]{0,80}(cancel|anul|bloque|rechaz|deten|pulse|acceda|llame|responda)"),
          "Le asustan con un cargo o una operación que no ha hecho para que actúe rápido.",
          "señuelo de cargo no reconocido"),
    _Rule("content.account_threat", SignalFamily.CONTENT, Severity.MEDIUM,
          _rx(r"(cuenta|tarjeta|acceso|banca|servicio)s? (sera|seran|ha sido|han sido|quedara|quedaran|esta|estan) "
              r"(temporalmente )?(bloquead|suspendid|cancelad|desactivad|restringid|limitad)"),
          "Le amenazan con bloquear su cuenta o tarjeta.", "amenaza de bloqueo"),
    _Rule("content.payment_request", SignalFamily.CONTENT, Severity.MEDIUM,
          _rx(r"(\b(realice|realiza|haga|haz|hacer|hacerme|efectue|efectua|envie|envia|enviar|enviarme|mande|manda|"
              r"mandarme|pasarme|prestarme|pague|paga|pagar|abone|abona|ingrese|ingresa)\b[^.\n]{0,40}"
              r"(transferencia|bizum|pago|importe|tasa|\d+[.,]?\d*\s?(€|eur|euros))|\bpague[^.\n]{0,30}tasa|"
              r"tasa de (aduana|envio|gestion)|pago pendiente|deposito (inicial |minimo )?de \d+)"),
          "Le piden que pague o envíe dinero.", "petición de pago", negatable=True, no_need=True),
    _Rule("content.payment_details_change", SignalFamily.CONTENT, Severity.HIGH,
          _rx(r"(nuev[oa] (numero de )?(cuenta|iban)|cambio de (cuenta|iban|datos bancarios)|"
              r"(hemos cambiado|ha cambiado|cambiado) (de )?(nuestra |la )?(cuenta|iban|entidad bancaria)|"
              # IBAN enmascarado («…» se pliega a «...») SOLO con contexto de cambio o novedad (revisión Etapa B)
              r"(nuev\w*|cambi\w*|actualizad\w*|a partir de ahora|desde ahora)[^.!?\n]{0,60}\[iban [a-z]{2} \.\.\.|"
              r"\[iban [a-z]{2} \.\.\.[^\]]*\][^.!?\n]{0,40}(nuev\w*|cambi\w*|a partir de ahora))"),
          "Le indican una cuenta bancaria nueva o diferente para pagar.", "cambio de datos de pago"),
    _Rule("content.investment_promise", SignalFamily.CONTENT, Severity.HIGH,
          _rx(r"(rentabilidad(es)? (garantizad|asegurad|del \d+)|(duplic|tripl|multiplic)\w* (su|tu) (dinero|inversion)|"
              r"sin (ningun )?riesgo|ganancias? (garantizad|diari|semanal)|beneficios? garantizad|"
              r"invierta (ahora|hoy)|oportunidad unica de inversion)"),
          "Le prometen ganancias garantizadas o sin riesgo.", "promesa de inversión"),
    _Rule("content.prize_or_refund", SignalFamily.CONTENT, Severity.MEDIUM,
          _rx(r"(ha (sido )?(ganado|premiad|seleccionad)|has (ganado|sido seleccionad)|reembolso|devolucion pendiente|"
              r"tiene (un|una) (premio|devolucion|reembolso))"),
          "Le ofrecen un premio o una devolución de dinero.", "premio o reembolso"),
    _Rule("content.family_new_number", SignalFamily.CONTENT, Severity.MEDIUM,
          _rx(r"((mama|papa|abuela|abuelo|hijo|hija)\b[^.\n]{0,60}(numero nuevo|nuevo numero|movil nuevo|se me ha (roto|caido|perdido))|"
              r"(numero nuevo|nuevo numero|este es mi nuevo)[^.\n]{0,60}(mama|papa|hijo|hija))"),
          "Alguien dice ser un familiar con un número nuevo.", "suplantación de familiar"),
    _Rule("content.remote_access", SignalFamily.CONTENT, Severity.HIGH,
          _rx(r"(anydesk|teamviewer|acceso remoto|control remoto|instale (esta|la) (aplicacion|app)|descargue (esta|la) (aplicacion|app))"),
          "Le piden instalar un programa o dar acceso remoto a su dispositivo.", "acceso remoto"),
    _Rule("content.injection_attempt", SignalFamily.CONTENT, Severity.HIGH,
          _rx(r"(ignora (todas )?(tus|las|sus) instrucciones|ignore (all |the )?(previous|prior|above) instructions|"
              r"clasifica (este|el) mensaje como|marca (este|el) mensaje como (seguro|legitimo)|system prompt|"
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
    """¿La coincidencia está negada en su propia oración («nunca le pediremos…»)?"""
    window = folded[max(0, start - 80):start]
    clause = re.split(r"[.!?\n:;]", window)[-1]
    span = folded[start:end]
    if _NEGATION.search(clause + " ") or _NEGATION.search(clause + span):
        return True
    if no_need and (_NO_NEED.search(clause + " ") or _NEGATED_SPAN.search(span)):
        return True
    return False


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

    for rule in _CONTENT_RULES:
        for m in rule.pattern.finditer(folded):
            if rule.negatable and _is_negated(folded, m.start(), m.end(), rule.no_need):
                continue
            signals.append(_signal(rule.code, rule.family, rule.severity, rule.user, rule.tech))
            break

    if any("invisibles" in w for w in message.parse_warnings):
        signals.append(_signal("content.invisible_chars", SignalFamily.CONTENT, Severity.MEDIUM,
                               "El mensaje contenía caracteres ocultos.", "caracteres invisibles eliminados"))
    if any(w.startswith("Texto oculto") for w in message.parse_warnings):
        signals.append(_signal("content.obfuscation", SignalFamily.CONTENT, Severity.MEDIUM,
                               "El mensaje intenta esconder parte de su contenido (texto oculto o letras disfrazadas).",
                               "ofuscación: texto oculto en HTML, alfabetos mezclados o enlaces con código"))

    # --- Remitente --------------------------------------------------------------
    sender = message.sender
    display_and_text = (sender.display_name or "") + "\n" + visible
    entities = mentioned_entities(display_and_text, directory)
    claimed = mentioned_entities(sender.display_name or "", directory)
    sender_official = directory.official_entity_for_host(sender.domain) if sender.domain else None

    for entity in claimed:
        if entity.official_domains and (sender_official is None or sender_official.entity_id != entity.entity_id):
            signals.append(_signal("sender.brand_mismatch", SignalFamily.SENDER, Severity.HIGH,
                                   f"El remitente se presenta como {entity.official_name}, pero no escribe desde su dirección oficial.",
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
