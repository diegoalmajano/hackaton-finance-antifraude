"""Análisis **pasivo** de enlaces (ADR-0005). Sin DNS, sin HTTP, sin seguir acortadores.

Funciones puras sobre cadenas:
- ``split_url``: esquema, host (punycode/ASCII), puerto, usuario, ruta.
- ``registrable_domain``: dominio registrable aproximado **sin la Public
  Suffix List** (no hay dependencia autorizada): lista corta incluida de
  sufijos de dos niveles frecuentes (limitación R-55).
- ``analyze_url``: comparación con el directorio de entidades y señales.
"""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from urllib.parse import urlsplit
from uuid import UUID

from antifraude.analysis.text import fold
from antifraude.contracts.checks import CheckResult, CheckStatus
from antifraude.contracts.common import Severity
from antifraude.contracts.links import DomainComparison, UrlAnalysis
from antifraude.contracts.messages import ExtractedUrl
from antifraude.contracts.screening import Signal, SignalFamily, SignalSource
from antifraude.intel.entities import EntityDirectory, normalize_host

#: Sufijos públicos de dos niveles frecuentes (aproximación sin PSL; R-55).
_TWO_LEVEL_SUFFIXES = frozenset({
    "com.es", "org.es", "nom.es", "gob.es", "edu.es",
    "co.uk", "org.uk", "ac.uk", "gov.uk", "com.ar", "com.mx", "com.br", "com.co", "com.pe",
    "co.jp", "com.au", "co.nz", "com.tr", "com.cn", "co.in", "co.za",
})

#: Acortadores conocidos (el destino nunca se resuelve). Incluye el ficticio de pruebas.
SHORTENERS = frozenset({
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "buff.ly", "cutt.ly", "rebrand.ly",
    "shorturl.at", "rb.gy", "t.ly", "s.id", "tiny.cc", "bl.ink", "acort.test",
})

STANDARD_PORTS = {None, 80, 443}
SIMILARITY_THRESHOLD = 0.8


@dataclass(frozen=True)
class UrlParts:
    scheme: str | None
    host: str | None  # ASCII (punycode) en minúsculas, o None si no se pudo determinar
    raw_host: str | None
    port: int | None
    has_userinfo: bool
    host_was_unicode: bool
    is_ip: bool


def split_url(raw: str) -> UrlParts:
    text = raw.strip()
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://", text):
        text = "http://" + text  # «www.x.es/…» o «x.es/…» sin esquema
        scheme = None
    else:
        scheme = text.split("://", 1)[0].lower()
    try:
        parts = urlsplit(text)
        raw_host = parts.hostname  # urlsplit ya separa usuario y puerto
        port = parts.port
    except ValueError:
        return UrlParts(scheme, None, None, None, "@" in text.split("/")[2] if text.count("/") >= 2 else False,
                        False, False)
    netloc = parts.netloc
    has_userinfo = "@" in netloc
    if not raw_host:
        return UrlParts(scheme, None, None, port, has_userinfo, False, False)
    unicode_host = not raw_host.isascii()
    host: str | None
    try:
        host = raw_host.encode("idna").decode("ascii").lower() if unicode_host else raw_host.lower()
    except UnicodeError:
        host = None
    is_ip = False
    if host:
        try:
            ipaddress.ip_address(host.strip("[]"))
            is_ip = True
        except ValueError:
            is_ip = False
    return UrlParts(scheme, host, raw_host, port, has_userinfo, unicode_host, is_ip)


def registrable_domain(host: str | None) -> str | None:
    if not host:
        return None
    labels = host.strip(".").split(".")
    if len(labels) < 2:
        return None
    if ".".join(labels[-2:]) in _TWO_LEVEL_SUFFIXES and len(labels) >= 3:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def _label(domain: str) -> str:
    """Parte distintiva de un dominio registrable (sin el sufijo)."""
    reg = registrable_domain(domain) or domain
    first = reg.split(".")[0]
    return first


def _signal(code: str, severity: Severity, user: str, tech: str) -> Signal:
    return Signal(code=code, family=SignalFamily.URL, severity=severity, source=SignalSource.THREAT_INTEL,
                  description_user=user, description_tech=tech)


def looks_like_host(text: str) -> str | None:
    """Si un texto visible parece un dominio o URL, devuelve su host normalizado."""
    t = text.strip().strip("<>").rstrip("/.")
    if not t or " " in t or "." not in t:
        return None
    if not re.match(r"^(?:[a-zA-Z][a-zA-Z0-9+.\-]*://)?[\w.\-]+\.[a-zA-Z]{2,}(?:[:/?#].*)?$", t):
        return None
    return split_url(t).host


#: Etiquetas que, dentro de un subdominio, indican un dominio completo incrustado («correos.es.otro.test»).
_TLD_LIKE = frozenset({"com", "es", "net", "org", "gob", "gov", "eu", "info"})


def _skeleton(host: str) -> str:
    """Forma canónica de un host para comparar: punycode decodificado, homoglifos y «leet» normalizados."""
    labels = []
    for label in host.split("."):
        if label.startswith("xn--"):
            try:
                label = label.encode("ascii").decode("idna")
            except (UnicodeError, ValueError):
                pass
        labels.append(label)
    return fold(".".join(labels)).replace(" ", "")


def _match_brand(host: str, directory: EntityDirectory) -> tuple[str, str] | None:
    reg = registrable_domain(host) or host
    reg_label = _label(host)
    sub = host[: -len(reg)].strip(".") if host.endswith(reg) else ""
    sub_tokens = re.split(r"[.\-]", sub) if sub else []
    for entity in directory.all():
        for od in entity.official_domains:
            brand = _label(od.domain)
            # dominio oficial usado como subdominio de otro («bancoficticio.example.otro.test»), con límite de
            # etiqueta: «booking.example» NO contiene a «ing.example».
            embedded = bool(re.search(r"(^|[.\-])" + re.escape(od.domain) + r"\.", host))
            if embedded or (len(brand) >= 4 and brand in sub_tokens):
                return "url.brand_in_subdomain", od.domain
            if len(brand) >= 4 and (brand in reg_label.split("-") or (len(brand) >= 6 and brand in reg_label)
                                    or (len(brand) >= 5 and SequenceMatcher(None, brand, reg_label).ratio()
                                        >= SIMILARITY_THRESHOLD)):
                return "url.lookalike_domain", od.domain
    return None


def find_lookalike(host: str | None, directory: EntityDirectory) -> tuple[str, str] | None:
    """¿El host (de un enlace o de un remitente) imita el dominio de una entidad del directorio?

    Devuelve ``(código, dominio_oficial_imitado)`` o ``None``. Un dominio oficial exacto nunca es parecido.
    Se compara el host tal cual y su «esqueleto» (homoglifos cirílicos/griegos, punycode y dígitos por letras).
    """
    if not host:
        return None
    host = host.lower().strip(".")
    if directory.official_entity_for_host(host) is not None:
        return None
    found = _match_brand(host, directory)
    if found:
        return found
    skeleton = _skeleton(host)
    if skeleton != host:
        official = directory.official_entity_for_host(skeleton)
        if official is not None and official.official_domains:
            return "url.lookalike_domain", official.official_domains[0].domain
        return _match_brand(skeleton, directory)
    return None


def _userinfo(raw: str) -> str | None:
    m = re.match(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://([^/?#]*)@", raw.strip())
    return m.group(1) if m else None


def urlsplit_path(raw: str) -> str:
    m = re.match(r"^(?:[a-zA-Z][a-zA-Z0-9+.\-]*://)?[^/?#]*(/[^?#]*)?", raw.strip())
    return (m.group(1) or "") if m else ""


def _brand_mentioned(text: str, directory: EntityDirectory, *, domains_only: bool = False) -> str | None:
    folded = _skeleton(text.lower())
    for entity in directory.all():
        for od in entity.official_domains:
            brand = _label(od.domain)
            if od.domain in folded or (not domains_only and len(brand) >= 5 and brand in folded):
                return od.domain
    return None


def analyze_url(url: ExtractedUrl, directory: EntityDirectory, claimed_entity_id: str | None = None) -> UrlAnalysis:
    parts = split_url(url.raw)
    findings: list[Signal] = []
    limitations: list[str] = []
    host = parts.host
    reg = registrable_domain(host)

    if parts.has_userinfo:
        findings.append(_signal("url.userinfo", Severity.HIGH,
                                "El enlace esconde su destino real detrás de una «@».",
                                "userinfo en la autoridad de la URL"))
    if parts.is_ip:
        findings.append(_signal("url.ip_literal", Severity.HIGH,
                                "El enlace usa una dirección numérica en lugar de un nombre de web.",
                                "host es una IP literal"))
    if parts.host_was_unicode or (host and "xn--" in host):
        findings.append(_signal("url.punycode", Severity.HIGH,
                                "La dirección contiene letras que pueden imitar a otras (caracteres especiales).",
                                f"host IDN/punycode: {host}"))
    if parts.port not in STANDARD_PORTS:
        findings.append(_signal("url.nonstandard_port", Severity.MEDIUM,
                                "El enlace usa un puerto poco habitual.", f"puerto {parts.port}"))
    if parts.scheme == "http":
        findings.append(_signal("url.insecure_http", Severity.LOW,
                                "El enlace no usa conexión cifrada (https).", "esquema http"))
    is_shortener = bool(reg and (reg in SHORTENERS or (host or "") in SHORTENERS))
    if is_shortener:
        findings.append(_signal("url.shortener", Severity.MEDIUM,
                                "Es un enlace acortado: no se puede saber a dónde lleva sin abrirlo.",
                                f"acortador {host}"))
        limitations.append("El destino del enlace acortado no se ha comprobado (no se abren enlaces).")
    if host is None or "\\" in url.raw.split("?")[0]:
        findings.append(_signal("url.unparseable", Severity.MEDIUM,
                                "El enlace tiene una forma extraña que impide saber a qué web lleva.",
                                "host indeterminable o barra invertida en la dirección"))
        if host is None:
            limitations.append("No se pudo determinar el dominio del enlace.")

    comparison = DomainComparison.UNKNOWN
    lookalike_of: str | None = None
    official = directory.official_entity_for_host(host) if host else None
    if official is not None:
        comparison = DomainComparison.OFFICIAL
    elif host is not None and not parts.is_ip:
        comparison = DomainComparison.UNRELATED
        found = find_lookalike(host, directory)
        if found:
            code, lookalike_of = found
            comparison = DomainComparison.LOOKALIKE
            if code == "url.brand_in_subdomain":
                findings.append(_signal(code, Severity.CRITICAL,
                                        "La dirección imita la web de una entidad colocándola delante de otro dominio.",
                                        f"{lookalike_of} usado como subdominio de {reg}"))
            else:
                findings.append(_signal(code, Severity.CRITICAL,
                                        "La dirección se parece a la de una entidad, pero no es la oficial.",
                                        f"{reg} se parece a {lookalike_of}"))
        sub = host[: -len(reg)].strip(".") if reg and host.endswith(reg) else ""
        if not found and any(lbl in _TLD_LIKE for lbl in sub.split(".")[1:]):  # «es.wikipedia.org» no cuenta
            findings.append(_signal("url.domain_in_subdomain", Severity.HIGH,
                                    "La dirección coloca el nombre de otra web delante de su dominio real "
                                    "(por ejemplo «empresa.es.otra-web»).", f"dominio incrustado en {host}"))
    # Marca oficial escondida antes de la «@» o en la ruta (revisión adversarial ronda 3, A10).
    userinfo = _userinfo(url.raw)
    if userinfo and not lookalike_of:
        brand_hit = _brand_mentioned(userinfo, directory)
        if brand_hit:
            lookalike_of, comparison = brand_hit, DomainComparison.LOOKALIKE
            findings.append(_signal("url.brand_in_userinfo", Severity.CRITICAL,
                                    "El enlace escribe la dirección de una entidad antes de una «@», pero lleva a otra web.",
                                    f"{brand_hit} en la parte de usuario de la URL"))
    path = urlsplit_path(url.raw)
    if path and official is None and not lookalike_of:
        in_path = _brand_mentioned(path, directory, domains_only=True)
        if in_path:
            findings.append(_signal("url.brand_in_path", Severity.HIGH,
                                    "El enlace incluye la dirección de una entidad en su ruta, pero lleva a otra web.",
                                    f"{in_path} en la ruta de {host}"))

    if url.display_text:
        shown = looks_like_host(url.display_text)
        if shown and host and registrable_domain(shown) != reg:
            findings.append(_signal("url.display_mismatch", Severity.HIGH,
                                    "El texto del enlace muestra una dirección, pero lleva a otra distinta.",
                                    f"texto visible {shown} ≠ destino {host}"))

    if claimed_entity_id and comparison is not DomainComparison.OFFICIAL and host and not lookalike_of:
        entity = directory.get(claimed_entity_id)
        if entity is not None and entity.official_domains:
            findings.append(_signal("url.not_official_for_claimed", Severity.HIGH,
                                    f"El mensaje dice venir de {entity.official_name}, pero el enlace no es de su web oficial.",
                                    f"{host} no es dominio oficial de {claimed_entity_id}"))

    checks = [
        CheckResult(name="intel.url_passive", required=True, status=CheckStatus.DONE),
        CheckResult(name="intel.rdap", required=False, status=CheckStatus.NOT_CONFIGURED),
        CheckResult(name="intel.reputation", required=False, status=CheckStatus.NOT_CONFIGURED),
    ]
    return UrlAnalysis(
        url_id=url.url_id,
        normalized_url=url.raw if len(url.raw) <= 8192 else None,
        registrable_domain=reg if reg and re.fullmatch(r"[a-z0-9.\-]+", reg) else None,
        claimed_entity_id=claimed_entity_id,
        comparison=comparison,
        lookalike_of=lookalike_of,
        display_href_mismatch=any(f.code == "url.display_mismatch" for f in findings),
        is_shortener=is_shortener,
        punycode_or_confusable=any(f.code == "url.punycode" for f in findings),
        findings=findings[:50],
        checks=checks,
        limitations=limitations,
    )


def url_id_for(index: int, message_id: UUID) -> UUID:
    """Identificador estable de una URL dentro de un mensaje."""
    from uuid import uuid5

    return uuid5(message_id, f"url-{index}")
