"""Normalización de texto no confiable (fase a/b). Sin red.

- ``clean_text``: elimina caracteres de control e invisibles (anchura cero,
  controles bidireccionales) y normaliza saltos de línea. Devuelve también
  cuántos invisibles había (un intento de ocultar texto es una señal).
- ``fold``: versión para comparar reglas (minúsculas, sin acentos, espacios
  simples). Nunca se muestra al usuario.
- ``minimize``: enmascara datos sensibles antes de guardar o enviar a la IA
  (`13` §10): números de tarjeta (Luhn), IBAN (país + 4 últimos), códigos
  numéricos junto a palabras como «código», «PIN», «clave», y contraseñas
  escritas tras «contraseña:».
"""

from __future__ import annotations

import re
import unicodedata

_INVISIBLE = re.compile("[​-‏‪-‮⁠-⁤⁦-⁩﻿­]")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_SPACES = re.compile(r"[ \t  -   　]+")


def clean_text(text: str) -> tuple[str, int]:
    """Texto limpio y número de caracteres invisibles eliminados."""
    invisibles = len(_INVISIBLE.findall(text))
    t = _INVISIBLE.sub("", text)
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = _CONTROL.sub("", t)
    t = "\n".join(_SPACES.sub(" ", line).strip() for line in t.split("\n"))
    t = re.sub(r"\n{3,}", "\n\n", t).strip()
    return t, invisibles


def fold(text: str) -> str:
    """Minúsculas, sin acentos ni diacríticos, espacios simples (solo para comparar)."""
    t = unicodedata.normalize("NFKD", text)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    return " ".join(t.casefold().split())


# --- Minimización ---------------------------------------------------------------
_CARD = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
_IBAN = re.compile(r"\b([A-Z]{2})(\d{2})((?:[ ]?[A-Z0-9]{4}){3,7}(?:[ ]?[A-Z0-9]{1,4})?)\b", re.IGNORECASE)
_CODE_CONTEXT = re.compile(
    r"((?:c[oó]digo|code|pin|clave|otp|contrase[nñ]a|password|cvv|cvc)\b[^0-9\n]{0,25}?)(\d{4,8})(?!\d)",
    re.IGNORECASE,
)
_PASSWORD_VALUE = re.compile(r"((?:contrase[nñ]a|password|clave)\s*[:=]\s*)(\S+)", re.IGNORECASE)


def _luhn_ok(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        total += d
        alt = not alt
    return total % 10 == 0


def _mask_card(m: re.Match[str]) -> str:
    digits = re.sub(r"\D", "", m.group(0))
    if 13 <= len(digits) <= 19 and _luhn_ok(digits):
        return f"[TARJETA …{digits[-4:]}]"
    return m.group(0)


def _mask_iban(m: re.Match[str]) -> str:
    compact = (m.group(1) + m.group(2) + m.group(3)).replace(" ", "")
    if not any(ch.isdigit() for ch in m.group(3)):
        return m.group(0)  # palabras que solo parecen IBAN (p. ej. «ES12 ABCD EFGH…» sin dígitos)
    return f"[IBAN {m.group(1).upper()} …{compact[-4:]}]"


def minimize(text: str) -> str:
    """Enmascara datos sensibles conservando su significado para el análisis."""
    t = _PASSWORD_VALUE.sub(lambda m: m.group(1) + "[OCULTO]", text)
    t = _IBAN.sub(_mask_iban, t)
    t = _CARD.sub(_mask_card, t)
    t = _CODE_CONTEXT.sub(lambda m: m.group(1) + "[CÓDIGO]", t)
    return t
