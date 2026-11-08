"""Pruebas de F0-09: directorio de entidades financieras (sin red, sin detector)."""

from __future__ import annotations

import ast
import copy
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from antifraude.contracts.entities import (
    EntityFile,
    FinancialEntity,
    VerificationStatus,
    is_reserved_domain,
)
from antifraude.contracts.evaluation import EvalCase
from antifraude.intel.entities import (
    FICTITIOUS_ENTITIES_FILE,
    REAL_ENTITIES_FILE,
    DirectoryError,
    EntityDirectory,
    normalize_host,
)

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend" / "antifraude"


def ficticia(**cambios: Any) -> dict[str, Any]:
    base = json.loads(FICTITIOUS_ENTITIES_FILE.read_text(encoding="utf-8"))["entities"][0]
    base = copy.deepcopy(base)
    base.update(cambios)
    return base


def verificada(**cambios: Any) -> dict[str, Any]:
    """Entidad 'verificada' de prueba con dominio NO reservado (solo en memoria, nunca en datos)."""
    base: dict[str, Any] = {
        "entity_id": "entidad_prueba", "official_name": "Entidad de Prueba, S.A.", "aliases": ["Entidad Prueba"],
        "verification_status": "verified",
        "official_domains": [{"domain": "entidad-prueba.es", "include_subdomains": False, "usage": ["web"]}],
        "verification": {"source_description": "Fuente de prueba", "source_url": "https://fuente.invalid/x",
                         "checked_on": "2026-11-01", "checked_by": "test"},
    }
    base.update(cambios)
    return base


@pytest.fixture
def directorio() -> EntityDirectory:
    return EntityDirectory.load_default(include_fictitious=True)


# --- Datos del repositorio ---------------------------------------------------------
def test_archivos_de_datos_validos() -> None:
    for f in (REAL_ENTITIES_FILE, FICTITIOUS_ENTITIES_FILE):
        EntityFile.model_validate_json(f.read_text(encoding="utf-8"))


def test_entidades_reales_verificadas_con_fuente_oficial_y_cobertura_parcial() -> None:
    # Misión 3 (tarea C): dominios del Registro de Entidades del Banco de España (campo PÁGINA WEB).
    reales = EntityFile.model_validate_json(REAL_ENTITIES_FILE.read_text(encoding="utf-8")).entities
    assert {e.entity_id for e in reales} == {"santander", "bbva", "caixabank", "sabadell", "bankinter"}
    esperados = {"santander": "santander.com", "bbva": "bbva.com", "caixabank": "caixabank.es",
                 "sabadell": "grupobancosabadell.com", "bankinter": "ebankinter.com"}
    for e in reales:
        assert e.verification_status is VerificationStatus.VERIFIED
        assert [d.domain for d in e.official_domains] == [esperados[e.entity_id]]
        assert e.domain_coverage.value == "partial"  # el registro solo da una web: nunca se presume completa
        assert e.verification is not None and e.verification.source_url is not None
        assert e.verification.source_url.startswith("https://www.bde.es/")


def test_ningun_dominio_real_sin_verificar_en_los_datos() -> None:
    for f in (REAL_ENTITIES_FILE, FICTITIOUS_ENTITIES_FILE):
        for e in EntityFile.model_validate_json(f.read_text(encoding="utf-8")).entities:
            for d in e.official_domains:
                assert is_reserved_domain(d.domain) or e.verification_status is VerificationStatus.VERIFIED


def test_ficticias_no_se_cargan_por_defecto() -> None:
    d = EntityDirectory.load_default()
    assert d.get("ficticio_banco") is None and d.official_entity_for_host("bancoficticio.example") is None
    assert len(d) == 5


# --- Esquema: entradas malformadas ----------------------------------------------------
@pytest.mark.parametrize("dominio", [
    "BancoFicticio.example", "https://bancoficticio.example", "bancoficticio.example/login",
    "bancoficticio.example:443", "*.bancoficticio.example", "bancoficticio", "-banco.example",
    "banco-.example", "banco..example", " bancoficticio.example", "bancofіcticio.example",  # 'і' cirílica
    "usuario@bancoficticio.example", "bancoficticio.123",
])
def test_dominio_malformado_rechazado(dominio: str) -> None:
    datos = ficticia(official_domains=[{"domain": dominio, "include_subdomains": False, "usage": ["web"]}])
    with pytest.raises(ValidationError):
        FinancialEntity.model_validate(datos)


@pytest.mark.parametrize("datos", [
    verificada(verification=None),                                                     # verificada sin fuente
    verificada(official_domains=[]),                                                   # verificada sin dominios
    verificada(verification={"source_description": "x", "source_url": "http://inseguro.invalid",
                             "checked_on": "2026-11-01", "checked_by": "t"}),           # fuente sin https
    verificada(verification={"source_description": "x", "source_url": None,
                             "checked_on": "2026-11-01", "checked_by": "t"}),           # sin URL de fuente
    verificada(verification={"source_description": "x", "source_url": "https://f.invalid",
                             "checked_on": (date.today() + timedelta(days=2)).isoformat(),
                             "checked_by": "t"}),                                       # fecha futura
    verificada(official_domains=[{"domain": "banco.example", "usage": ["web"]}]),       # real con dominio reservado
    verificada(entity_id="ficticio_x"),                                                 # id reservado a ficticias
    ficticia(official_domains=[{"domain": "banco-real.es", "usage": ["web"]}]),         # ficticia con dominio real
    ficticia(entity_id="banco_x"),                                                      # ficticia sin prefijo
    ficticia(verification=None),                                                        # ficticia sin origen
    {**verificada(), "verification_status": "pending_verification"},                    # pendiente con dominios
    ficticia(aliases=["Banco Ficticio", "banco  ficticio"]),                            # alias repetido
    ficticia(official_domains=[{"domain": "bancoficticio.example", "usage": ["web"]}] * 2),  # dominio repetido
    ficticia(entity_id="Banco Ficticio"),                                               # id malformado
    ficticia(pagina_login="https://bancoficticio.example"),                             # campo desconocido
    ficticia(official_domains=[{"domain": "bancoficticio.example", "usage": []}]),      # sin uso
])
def test_entidad_incoherente_rechazada(datos: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        FinancialEntity.model_validate(datos)


def test_entidad_verificada_valida_en_memoria() -> None:
    e = FinancialEntity.model_validate(verificada())
    assert e.verification_status is VerificationStatus.VERIFIED


# --- Duplicados entre entidades -------------------------------------------------------
@pytest.mark.parametrize("segunda", [
    verificada(entity_id="ficticio_banco", official_name="Otra, S.A.", aliases=[],          # id duplicado
               verification_status="pending_verification", official_domains=[], verification=None),
    verificada(entity_id="otra", official_name="Otra, S.A.", aliases=["Banco Ficticio"],   # alias duplicado
               verification_status="pending_verification", official_domains=[], verification=None),
    ficticia(entity_id="ficticio_otro", official_name="Otro Ficticio", aliases=[]),        # dominio duplicado
    ficticia(entity_id="ficticio_otro", official_name="Otro Ficticio", aliases=[],         # dominio solapado
             official_domains=[{"domain": "pagos.bancoficticio.example", "usage": ["web"]}]),
])
def test_duplicados_entre_entidades(segunda: dict[str, Any]) -> None:
    entidades = [FinancialEntity.model_validate(ficticia()), FinancialEntity.model_validate(segunda)]
    with pytest.raises(DirectoryError):
        EntityDirectory(entidades, include_fictitious=True)


# --- Reglas de coincidencia exacta de dominios ------------------------------------------
@pytest.mark.parametrize("host,oficial", [
    ("bancoficticio.example", True),
    ("www.bancoficticio.example", True),                  # subdominio real (include_subdomains)
    ("BANCOFICTICIO.EXAMPLE.", True),                     # mayúsculas y punto final
    ("bancoficticio.example.validacion-dispositivos.test", False),  # subdominio engañoso de otro dominio
    ("bancoficticio-verificacion.example", False),        # dominio parecido
    ("evilbancoficticio.example", False),                 # coincidencia parcial por sufijo
    ("bancoficticio.exampl", False),                      # truncado
    ("bancoficticio.example.", True),
    ("bancofіcticio.example", False),                     # homoglifo (i cirílica)
    ("bancoficticio.example:443", False),                 # con puerto
    ("usuario@bancoficticio.example", False),             # con usuario
    ("*.bancoficticio.example", False),                   # comodín
    (" bancoficticio.example", False),                    # espacios
    ("", False),
    ("example", False),
])
def test_coincidencia_exacta_de_dominios(directorio: EntityDirectory, host: str, oficial: bool) -> None:
    entidad = directorio.official_entity_for_host(host)
    assert (entidad is not None and entidad.entity_id == "ficticio_banco") is oficial
    assert directorio.is_official_host(host, "ficticio_banco") is oficial


def test_subdominios_solo_si_se_permiten() -> None:
    e = FinancialEntity.model_validate(verificada())  # include_subdomains=False
    d = EntityDirectory([e])
    assert d.is_official_host("entidad-prueba.es", "entidad_prueba")
    assert not d.is_official_host("www.entidad-prueba.es", "entidad_prueba")


def test_dominios_registrados_y_sus_subdominios_son_oficiales(directorio: EntityDirectory) -> None:
    assert directorio.is_official_host("www.bbva.com", "bbva")
    assert directorio.is_official_host("caixabank.es", "caixabank")
    assert not directorio.is_official_host("bbva.com.otro.test", "bbva")
    assert directorio.official_entity_for_host("bbva.es") is None  # no verificado (cobertura parcial)


def test_normalize_host() -> None:
    assert normalize_host("WWW.Banco.Example.") == "www.banco.example"
    for malo in ["", " x.es", "x.es ", "x..es", ".x.es", "-x.es", "x.es:80", "a/b.es", "ñ.es", "a b.es"]:
        assert normalize_host(malo) is None, malo


# --- Búsqueda por nombre (exacta, sin subcadenas) ------------------------------------------
@pytest.mark.parametrize("nombre,esperado", [
    ("Banco Ficticio", "ficticio_banco"), ("banco  ficticio", "ficticio_banco"), ("BANCO FICTICIO, S.A.", "ficticio_banco"),
    ("bbva", "bbva"), ("Bankinter", "bankinter"), ("Banco de Sabadell, S.A.", "sabadell"),
    ("Banco Ficticio Seguridad", None), ("BBVA Net", None), ("Ficticio", None), ("", None),
])
def test_busqueda_por_nombre_exacta(directorio: EntityDirectory, nombre: str, esperado: str | None) -> None:
    e = directorio.find_by_name(nombre)
    assert (e.entity_id if e else None) == esperado


# --- Coherencia con los casos de demo (sin detector) ------------------------------------------
def test_dominios_de_los_casos_demo(directorio: EntityDirectory) -> None:
    casos = {c.case_id: c for c in (EvalCase.model_validate_json(line) for line in
             (ROOT / "eval/datasets/dev/demo.jsonl").read_text(encoding="utf-8").splitlines() if line.strip())}
    dominio = lambda addr: addr.split("@", 1)[1]  # noqa: E731
    assert directorio.is_official_host(dominio(casos["dev-0001"].message.sender.address), "ficticio_banco")
    assert not directorio.is_official_host(dominio(casos["dev-0002"].message.sender.address), "ficticio_banco")
    assert not directorio.is_official_host("bancoficticio-verificacion.example", "ficticio_banco")
    c3 = casos["dev-0003"]
    assert c3.message.reply_to and not directorio.is_official_host(dominio(c3.message.reply_to), "ficticio_banco")
    assert not directorio.is_official_host("bancoficticio.example.validacion-dispositivos.test", "ficticio_banco")


# --- Sin red: ningún código del backend resuelve DNS ni hace peticiones HTTP salientes ----------
_PROHIBIDO_IMPORT = {"requests", "httpx", "urllib.request", "http.client", "aiohttp", "dns", "dns.resolver"}
_PROHIBIDO_LLAMADA = {"getaddrinfo", "gethostbyname", "gethostbyname_ex", "create_connection", "urlopen"}


def test_backend_sin_dns_ni_http_saliente() -> None:
    for py in BACKEND.rglob("*.py"):
        arbol = ast.parse(py.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Import):
                assert not {a.name for a in nodo.names} & _PROHIBIDO_IMPORT, py
            elif isinstance(nodo, ast.ImportFrom) and nodo.module:
                assert nodo.module not in _PROHIBIDO_IMPORT, py
            elif isinstance(nodo, ast.Attribute):
                assert nodo.attr not in _PROHIBIDO_LLAMADA, f"{py}: {nodo.attr}"
