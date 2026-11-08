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

from dataclasses import dataclass, field
from html.parser import HTMLParser

_SKIP = {"script", "style", "head", "template", "noscript", "title"}
_BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "table", "ul", "ol", "section", "article"}
MAX_ANCHORS = 200


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
        if tag == "a":
            self._flush_anchor()  # un <a> anterior sin cerrar
            href = dict(attrs).get("href")
            self._anchor_href = href.strip() if href else None
            self._anchor_text = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in _SKIP:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if tag == "a":
            self._flush_anchor()
        if tag in _BLOCK:
            self.state.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        self.state.parts.append(data)
        if self._anchor_href is not None:
            self._anchor_text.append(data)


def html_to_text_and_anchors(html: str, warnings: list[str] | None = None) -> tuple[str, list[Anchor]]:
    parser = _Extractor()
    try:
        parser.feed(html)
        parser.close()
    except Exception:  # HTML roto: se devuelve lo extraído hasta el error, con aviso
        if warnings is not None:
            warnings.append("El contenido HTML del mensaje estaba dañado; se analizó solo una parte.")
    parser._flush_anchor()  # enlace final sin cerrar
    return "".join(parser.state.parts), parser.state.anchors
