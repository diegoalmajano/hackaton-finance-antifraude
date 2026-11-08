"""Consulta del directorio de entidades financieras (F0-09).

Funciones de consulta **sin red**: no hay DNS, ni HTTP, ni se visitan enlaces.
No es el detector de phishing; solo responde a dos preguntas exactas:
1. ¿Qué entidad corresponde a este nombre o alias? (coincidencia exacta normalizada)
2. ¿Es este nombre de host un dominio oficial **verificado** de una entidad?

Reglas de coincidencia de dominios:
- Igualdad exacta con un dominio oficial, o subdominio real
  (``x.dominio-oficial``) solo si ese dominio permite subdominios.
- Nunca coincidencias parciales, por prefijo ni por parecido:
  ``dominio-oficial.otro.test``, ``falso-dominio-oficial`` o
  ``dominiooficial`` NO son oficiales.
- Nombres de host no ASCII (posibles homoglifos), con puerto, usuario,
  comodines o espacios → no se consideran oficiales.
- Las entidades pendientes de verificación no tienen dominios oficiales.
- Las entidades ficticias solo se cargan si se pide expresamente.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from antifraude.contracts.entities import (
    EntityFile,
    FinancialEntity,
    OfficialDomain,
    VerificationStatus,
    _fold,
)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
REAL_ENTITIES_FILE = DATA_DIR / "entities_es.json"
FICTITIOUS_ENTITIES_FILE = DATA_DIR / "entities_ficticias.json"

_HOST_RE = re.compile(r"^[a-z0-9.-]{1,253}$")


class DirectoryError(ValueError):
    """Datos del directorio incoherentes (duplicados, entidades ficticias no permitidas…)."""


def normalize_host(host: str) -> str | None:
    """Nombre de host en minúsculas y sin punto final, o ``None`` si no es un host simple y ASCII."""
    if not isinstance(host, str):
        return None
    h = host.strip()
    if not h or h != host or not h.isascii():
        return None
    h = h.lower()
    if h.endswith("."):
        h = h[:-1]
    if not _HOST_RE.fullmatch(h) or ".." in h or h.startswith(".") or h.startswith("-"):
        return None
    return h


def _matches(host: str, official: OfficialDomain) -> bool:
    if host == official.domain:
        return True
    return official.include_subdomains and host.endswith("." + official.domain)


class EntityDirectory:
    def __init__(self, entities: Iterable[FinancialEntity], *, include_fictitious: bool = False) -> None:
        self._by_id: dict[str, FinancialEntity] = {}
        self._by_name: dict[str, str] = {}
        self._domains: list[tuple[OfficialDomain, str]] = []
        for entity in entities:
            if entity.verification_status is VerificationStatus.FICTITIOUS and not include_fictitious:
                continue
            self._add(entity)

    def _add(self, entity: FinancialEntity) -> None:
        if entity.entity_id in self._by_id:
            raise DirectoryError(f"entity_id duplicado: {entity.entity_id}")
        for name in [entity.official_name, *entity.aliases]:
            key = _fold(name)
            if key in self._by_name:
                raise DirectoryError(f"nombre o alias duplicado entre entidades: {name}")
            self._by_name[key] = entity.entity_id
        for od in entity.official_domains:
            for other, other_id in self._domains:
                if od.domain == other.domain:
                    raise DirectoryError(f"dominio oficial duplicado entre entidades: {od.domain}")
                if _matches(od.domain, other) or _matches(other.domain, od):
                    raise DirectoryError(f"dominios oficiales solapados entre {entity.entity_id} y {other_id}")
            self._domains.append((od, entity.entity_id))
        self._by_id[entity.entity_id] = entity

    # --- carga -------------------------------------------------------------------
    @classmethod
    def from_files(cls, paths: Iterable[Path], *, include_fictitious: bool = False) -> EntityDirectory:
        entities: list[FinancialEntity] = []
        for path in paths:
            data = EntityFile.model_validate_json(Path(path).read_text(encoding="utf-8"))
            entities.extend(data.entities)
        return cls(entities, include_fictitious=include_fictitious)

    @classmethod
    def load_default(cls, *, include_fictitious: bool = False) -> EntityDirectory:
        paths = [REAL_ENTITIES_FILE] + ([FICTITIOUS_ENTITIES_FILE] if include_fictitious else [])
        return cls.from_files(paths, include_fictitious=include_fictitious)

    # --- consultas ---------------------------------------------------------------
    def __len__(self) -> int:
        return len(self._by_id)

    def get(self, entity_id: str) -> FinancialEntity | None:
        return self._by_id.get(entity_id)

    def all(self) -> list[FinancialEntity]:
        return list(self._by_id.values())

    def find_by_name(self, name: str) -> FinancialEntity | None:
        """Coincidencia **exacta** normalizada de nombre oficial o alias (nunca por subcadena)."""
        entity_id = self._by_name.get(_fold(name)) if isinstance(name, str) else None
        return self._by_id.get(entity_id) if entity_id else None

    def official_entity_for_host(self, host: str) -> FinancialEntity | None:
        """Entidad cuyo dominio oficial verificado coincide exactamente con ``host`` (ver reglas)."""
        h = normalize_host(host)
        if h is None:
            return None
        for official, entity_id in self._domains:
            if _matches(h, official):
                return self._by_id[entity_id]
        return None

    def is_official_host(self, host: str, entity_id: str) -> bool:
        entity = self.official_entity_for_host(host)
        return entity is not None and entity.entity_id == entity_id

    def official_domains(self, entity_id: str) -> list[str]:
        entity = self._by_id.get(entity_id)
        return [d.domain for d in entity.official_domains] if entity else []
