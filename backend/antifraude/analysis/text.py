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


#: Letras de otros alfabetos que imitan a las latinas (revisión de seguridad: evasión por homoglifos).
_CONFUSABLES = str.maketrans({
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "х": "x", "у": "y", "і": "i", "ј": "j", "ѕ": "s",
    "ԁ": "d", "һ": "h", "ӏ": "l", "ո": "n", "ս": "u", "к": "k", "м": "m", "т": "t", "в": "b", "н": "h",
    "α": "a", "ο": "o", "ρ": "p", "ε": "e", "ι": "i", "κ": "k", "ν": "v", "τ": "t", "υ": "u", "χ": "x",
    "ı": "i", "ɑ": "a", "ɡ": "g",
})
_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"})
_LEET_WORD = re.compile(r"\b(?=[a-z0-9@$]*[a-z])(?=[a-z0-9@$]*[0-9@$])[a-z0-9@$]{4,}\b")
_SPACED = re.compile(r"\b(?:[a-zñ] ){3,}[a-zñ]\b")
_LATIN = re.compile(r"[a-z]")
_OTHER_SCRIPT = re.compile("[Ͱ-ϿЀ-ӿԀ-ԯ]")


def has_mixed_script(text: str) -> bool:
    """¿Alguna palabra mezcla letras latinas con griegas o cirílicas? (típico de evasión)."""
    for word in re.findall(r"\w+", text.lower()):
        if _LATIN.search(word) and _OTHER_SCRIPT.search(word):
            return True
    return False


def fold(text: str) -> str:
    """Forma canónica para comparar reglas (nunca se muestra al usuario).

    Minúsculas, sin acentos, homoglifos cirílicos/griegos → latinos, «leet» dentro de palabras
    («c0ntraseña» → «contrasena») y letras espaciadas reunidas («c l a v e» → «clave»).
    """
    t = unicodedata.normalize("NFKC", text).casefold().translate(_CONFUSABLES)
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = " ".join(t.split())
    t = _SPACED.sub(lambda m: m.group(0).replace(" ", ""), t)
    t = _LEET_WORD.sub(lambda m: m.group(0).translate(_LEET), t)
    return t


# --- Minimización ---------------------------------------------------------------
_CARD = re.compile(r"(?<!\d)(?:\d[ \t\n.\-/]?){13,19}(?!\d)")
_IBAN = re.compile(r"\b([A-Z]{2})(\d{2})((?:[ .\-]?[A-Z0-9]{2,4}){4,8})\b", re.IGNORECASE)
_CCC = re.compile(r"(?<!\d)\d{4}[ .\-]?\d{4}[ .\-]?\d{2}[ .\-]?\d{10}(?!\d)")  # cuenta española antigua
_KEYWORD = r"(?:c[oó]digo|code|pin|clave|otp|contrase[nñ]a|password|cvv|cvc|verificaci[oó]n|verification|token)"
_CODE_AFTER = re.compile(rf"(\b{_KEYWORD}\b[^\n.]{{0,60}}?(?:\n[ \t]*)?)(\d(?:[ \-]?\d){{2,9}})(?!\d)", re.IGNORECASE)
_CODE_BEFORE = re.compile(rf"(?<!\d)(\d(?:[ \-]?\d){{3,9}})(?!\d)(\s+(?:es|is|=)\s+(?:su|tu|el|your)?\s*{_KEYWORD})",
                          re.IGNORECASE)
_PASSWORD_VALUE = re.compile(r"((?:contrase[nñ]a|password|clave)\s*(?:[:=]|\bes\b|\bis\b)\s*)(\S+)", re.IGNORECASE)
_DNI = re.compile(r"\b(\d{8})[ \-]?([A-HJ-NP-TV-Z])\b")
_PHONE = re.compile(r"(?<![\d+])(?:\+34[ ]?)?[6789]\d{2}[ ]?\d{3}[ ]?\d{3}(?!\d)")


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
    """Enmascara datos sensibles conservando su significado para el análisis.

    Tarjetas (Luhn, con cualquier separador), IBAN y cuentas, códigos de 3–10 dígitos junto a palabras
    como «código», «PIN» o «verificación» (antes o después), contraseñas escritas, DNI y teléfonos.
    """
    t = _PASSWORD_VALUE.sub(lambda m: m.group(1) + "[OCULTO]", text)
    t = _IBAN.sub(_mask_iban, t)
    t = _CCC.sub("[CUENTA]", t)
    t = _CARD.sub(_mask_card, t)
    t = _CODE_AFTER.sub(lambda m: m.group(1) + "[CÓDIGO]", t)
    t = _CODE_BEFORE.sub(lambda m: "[CÓDIGO]" + m.group(2), t)
    t = _DNI.sub("[DNI]", t)
    t = _PHONE.sub("[TELÉFONO]", t)
    return t
