"""Extracción segura de texto visible y enlaces de HTML no confiable (stdlib, sin red).

No ejecuta nada ni descarga recursos: solo recorre etiquetas. Se ignora el
contenido de ``script``, ``style``, ``head`` y ``template``; los ``<a href>``
se devuelven con su texto visible para detectar enlaces cuyo texto no
coincide con su destino.

Robustez frente a HTML hostil o mal formado (revisión de la Etapa B):
- ``<body>`` reinicia el modo «ignorar» (un ``<head>``/``<title>`` sin cerrar
  no puede ocultar el cuerpo).
- Un ``<a>`` sin cerrar se registra igualmente (al abrir otro ``<a>`` o al
  terminar el documento).
- Si el analizador falla, se devuelve lo extraído y se anota un aviso.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser

#: Solo se omite lo que un cliente de correo nunca muestra. ``noscript``, ``head`` y ``title`` SÍ se
#: analizan (revisión de seguridad: un cliente de correo muestra el contenido de ``<noscript>``).
_SKIP = {"script", "style", "template"}
_BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "table", "ul", "ol", "section", "article"}
MAX_ANCHORS = 200
#: Límite de HTML que se analiza (protección frente a denegación de servicio; el resto se declara).
MAX_HTML_CHARS = 300_000
#: Un «<» sin «>» en esta distancia se trata como texto (evita el coste cuadrático de HTMLParser).
_MAX_TAG_SPAN = 2_000
_HIDDEN_STYLE = re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden|font-size\s*:\s*0(?![.\d])|opacity\s*:\s*0(?![.\d])",
                           re.IGNORECASE)


def defuse_html(html: str) -> tuple[str, bool]:
    """Neutraliza construcciones que hacen el análisis cuadrático. Lineal. Devuelve (html, recortado)."""
    truncated = len(html) > MAX_HTML_CHARS
    html = html[:MAX_HTML_CHARS]
    for opener, closer in (("<!--", "-->"), ("<![CDATA[", "]]>")):
        last_close = html.rfind(closer)
        idx = html.find(opener, last_close + len(closer) if last_close >= 0 else 0)
        if idx != -1:  # apertura sin cierre: el resto pasa a ser texto
            html = html[:idx] + html[idx:].replace("<", "&lt;")
    # «<» cuyo «>» más cercano está lejos o no existe → texto.
    next_gt = [-1] * (len(html) + 1)
    nearest = -1
    for i in range(len(html) - 1, -1, -1):
        if html[i] == ">":
            nearest = i
        next_gt[i] = nearest
    out: list[str] = []
    for i, ch in enumerate(html):
        if ch == "<" and (next_gt[i] == -1 or next_gt[i] - i > _MAX_TAG_SPAN):
            out.append("&lt;")
        else:
            out.append(ch)
    return "".join(out), truncated


@dataclass
class Anchor:
    href: str
    text: str


@dataclass
class _State:
    parts: list[str] = field(default_factory=list)
    anchors: list[Anchor] = field(default_factory=list)


class _Extractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.state = _State()
        self._skip_depth = 0
        self._anchor_href: str | None = None
        self._anchor_text: list[str] = []
        self._hidden_stack: list[str] = []  # etiquetas abiertas con estilo oculto
        self.hidden_chars = 0
        self.script_links = 0

    def _flush_anchor(self) -> None:
        if self._anchor_href is not None and len(self.state.anchors) < MAX_ANCHORS:
            text = " ".join("".join(self._anchor_text).split())
            self.state.anchors.append(Anchor(href=self._anchor_href, text=text))
        self._anchor_href = None
        self._anchor_text = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "body":
            self._skip_depth = 0
            return
        if tag in _SKIP:
            self._skip_depth += 1
            return
        if tag in _BLOCK:
            self.state.parts.append("\n")
        attr = dict(attrs)
        if _HIDDEN_STYLE.search(attr.get("style") or "") or "hidden" in attr:
            self._hidden_stack.append(tag)
        if tag == "a":
            self._flush_anchor()  # un <a> anterior sin cerrar
            href = attr.get("href")
            self._anchor_href = href.strip() if href else None
            self._anchor_text = []
            if href and href.strip().lower().replace(" ", "").startswith(("javascript:", "vbscript:", "data:")):
                self.script_links += 1

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in _SKIP:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._hidden_stack and self._hidden_stack[-1] == tag:
            self._hidden_stack.pop()
        if tag == "a":
            self._flush_anchor()
        if tag in _BLOCK:
            self.state.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._hidden_stack:
            self.hidden_chars += len(data.strip())
        self.state.parts.append(data)
        if self._anchor_href is not None:
            self._anchor_text.append(data)


def html_to_text_and_anchors(html: str, warnings: list[str] | None = None) -> tuple[str, list[Anchor]]:
    parser = _Extractor()
    html, truncated = defuse_html(html)
    try:
        parser.feed(html)
        parser.close()
    except Exception:  # HTML roto: se devuelve lo extraído hasta el error, con aviso
        if warnings is not None:
            warnings.append("Análisis parcial: el contenido HTML del mensaje estaba dañado; se analizó solo una parte.")
    parser._flush_anchor()  # enlace final sin cerrar
    if warnings is not None:
        if truncated:
            warnings.append("Análisis parcial: el contenido HTML era muy extenso; solo se analizó una parte.")
        if parser.hidden_chars > 20:
            warnings.append("Texto oculto: el mensaje contiene texto escondido al lector.")
        if parser.script_links:
            warnings.append("Texto oculto: el mensaje contiene enlaces que ejecutarían código.")
    return "".join(parser.state.parts), parser.state.anchors
