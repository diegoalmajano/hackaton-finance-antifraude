"""Análisis manual desde la interfaz (Etapa D). Protegido por sesión, CSRF y Origin.

- ``POST /analizar``: texto pegado o archivo ``.eml``.
- ``POST /analizar/ejemplo/{n}``: solo en modo demostración; casos sintéticos
  de ``eval/datasets/dev/demo.jsonl``, siempre etiquetados como EJEMPLO SINTÉTICO.
Se devuelve un fragmento HTML (htmx). El texto del mensaje no se guarda: el
historial de la sesión solo conserva el nivel, el título y la hora.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any
from uuid import UUID, uuid5

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, Response

from antifraude.analysis.ingest import IngestError, IngestResult, from_eml, from_manual_text
from antifraude.app.errors import UserFacingError
from antifraude.app.pages import templates
from antifraude.app.pipeline import AnalysisOutcome, AnalysisPipeline
from antifraude.app.security.deps import CsrfSessionDep
from antifraude.app.security.sessions import Session
from antifraude.contracts.assessment import EvidenceKind, EvidenceSource
from antifraude.contracts.common import MAX_RAW_BYTES, RiskLevel
from antifraude.evaluation import load_cases, run_case

router = APIRouter()

DEMO_FILE = Path(__file__).resolve().parents[3] / "eval" / "datasets" / "dev" / "demo.jsonl"
MAX_TEXT_FORM_CHARS = 100_000
HISTORY_MAX = 20
_NAMESPACE = UUID("7c1d3f0e-5a2b-4c8d-9e6f-0a1b2c3d4e5f")

LEVEL_VIEW: dict[RiskLevel, dict[str, str]] = {
    RiskLevel.HIGH: {"nombre": "ALTO", "icono": "⛔", "clase": "alto"},
    RiskLevel.MEDIUM: {"nombre": "MEDIO", "icono": "⚠️", "clase": "medio"},
    RiskLevel.INCONCLUSIVE: {"nombre": "NO CONCLUYENTE", "icono": "❔", "clase": "no-concluyente"},
    RiskLevel.LOW: {"nombre": "BAJO", "icono": "✅", "clase": "bajo"},
}
SOURCE_VIEW = {
    EvidenceSource.RULE: "Revisión automática del texto",
    EvidenceSource.THREAT_INTEL: "Análisis del enlace o del remitente (sin abrir nada)",
    EvidenceSource.AI: "Análisis con inteligencia artificial (cita comprobada)",
    EvidenceSource.USER_PROFILE: "Sus preferencias",
    EvidenceSource.CORRELATION: "Relación con otros mensajes",
}
CHECK_VIEW = {
    "screening.rules": "Revisión del texto",
    "intel.url_passive": "Análisis de enlaces sin abrirlos",
    "intel.rdap": "Antigüedad de la web (no configurada)",
    "intel.reputation": "Listas de webs peligrosas (no configuradas)",
    "ai.analysis": "Análisis con inteligencia artificial",
}


def _pipeline(request: Request) -> AnalysisPipeline:
    pipeline: AnalysisPipeline = request.app.state.pipeline
    return pipeline


def _view(outcome: AnalysisOutcome, *, ejemplo: str | None, ai_configured: bool) -> dict[str, Any]:
    a = outcome.assessment
    riesgo = [e for e in a.evidence if e.kind is EvidenceKind.RISK and e.severity.rank >= 2]
    leves = [e for e in a.evidence if e.kind is EvidenceKind.RISK and e.severity.rank < 2]
    legit = [e for e in a.evidence if e.kind is EvidenceKind.LEGITIMACY]
    no_comprobado = list(dict.fromkeys(a.uncertainties + [CHECK_VIEW.get(n, n) for n in a.unverified_checks]))
    ai_status = outcome.ai.status.value if outcome.ai else "not_required"
    return {
        "nivel": LEVEL_VIEW[a.risk_level],
        "explicacion": a.explanation_user,
        "evidencias": [{"texto": e.description_user, "fuente": SOURCE_VIEW[e.source], "cita": e.quote,
                        "grave": e.severity.rank >= 3} for e in riesgo],
        "detalles": [e.description_user for e in leves],
        "legitimidad": [e.description_user for e in legit],
        "no_comprobado": no_comprobado,
        "recomendaciones": [r.text_user for r in a.recommendations],
        "parcial": a.is_partial,
        "preventiva": outcome.preventive_alert is not None,
        "ejemplo": ejemplo,
        "ia": {"configurada": ai_configured, "estado": ai_status},
        "comprobaciones": [{"nombre": CHECK_VIEW.get(c.name, c.name), "estado": c.status.value,
                            "obligatoria": c.required} for c in a.checks],
        "avisos_ingesta": list(outcome.message.parse_warnings),
        "latencia_ms": outcome.latency_ms,
    }


def _remember(session: Session, outcome: AnalysisOutcome, origen: str) -> None:
    level = LEVEL_VIEW[outcome.assessment.risk_level]
    session.history.insert(0, {
        "nivel": level["nombre"], "icono": level["icono"], "clase": level["clase"],
        "titulo": outcome.final_alert.title_user, "origen": origen,
        "hora": datetime.now(timezone.utc).astimezone().strftime("%H:%M"),
        "parcial": "sí" if outcome.assessment.is_partial else "no",
    })
    del session.history[HISTORY_MAX:]


def _render(request: Request, outcome: AnalysisOutcome, session: Session, *, ejemplo: str | None) -> Response:
    _remember(session, outcome, "Ejemplo sintético" if ejemplo else "Análisis manual")
    ctx = {"r": _view(outcome, ejemplo=ejemplo, ai_configured=request.app.state.ai_configured),
           "historial": session.history}
    return templates.TemplateResponse(request, "partials/resultado.html", ctx)


@router.post("/analizar", response_class=HTMLResponse)
async def analizar(
    request: Request,
    session: CsrfSessionDep,
    texto: Annotated[str, Form(max_length=MAX_TEXT_FORM_CHARS)] = "",
    archivo: Annotated[UploadFile | None, File()] = None,
) -> Response:
    user_id = uuid5(_NAMESPACE, session.csrf_token)  # identificador estable por sesión, sin datos personales
    try:
        ingested: IngestResult
        if archivo is not None and archivo.filename:
            if not archivo.filename.lower().endswith(".eml"):
                raise UserFacingError(400, "Solo se pueden importar archivos de correo con extensión .eml.")
            raw = await archivo.read(MAX_RAW_BYTES + 1)
            ingested = from_eml(raw, user_id)
        elif texto.strip():
            ingested = from_manual_text(texto, user_id)
        else:
            raise UserFacingError(400, "Pegue el texto del mensaje o elija un archivo .eml para analizarlo.")
    except IngestError as exc:
        raise UserFacingError(400, str(exc)) from None
    outcome = _pipeline(request).run(ingested)
    return _render(request, outcome, session, ejemplo=None)


@router.post("/analizar/ejemplo/{numero}", response_class=HTMLResponse)
def analizar_ejemplo(request: Request, numero: int, session: CsrfSessionDep) -> Response:
    if not request.app.state.settings.demo_mode:
        raise UserFacingError(404, "Los ejemplos solo están disponibles en el modo demostración.")
    casos = {c.demo_order: c for c in load_cases([DEMO_FILE]) if c.demo_order}
    caso = casos.get(numero)
    if caso is None:
        raise UserFacingError(404, "Ese ejemplo no existe.")
    outcome = run_case(caso, _pipeline(request))
    return _render(request, outcome, session, ejemplo=f"{caso.title_es} ({caso.case_id})")


@router.get("/historial", response_class=HTMLResponse)
def historial(request: Request, session: CsrfSessionDep) -> Response:
    return templates.TemplateResponse(request, "partials/historial.html", {"historial": session.history})
