"""Ejecución del banco de evaluación y métricas (módulo K, `eval/README.md` §6).

Convierte cada ``EvalCase`` (mensaje ficticio + etiqueta) en un mensaje del
pipeline, ejecuta el análisis y compara con lo esperado. **Solo** para el
conjunto de desarrollo durante el desarrollo; el conjunto sellado se ejecuta
una vez, con autorización (D-40).
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from uuid import UUID

from antifraude.analysis.ingest import build_message, make_sender
from antifraude.app.pipeline import AnalysisOutcome, AnalysisPipeline
from antifraude.contracts.common import RiskLevel
from antifraude.contracts.evaluation import EvalCase
from antifraude.contracts.messages import Channel

EVAL_USER = UUID("00000000-0000-4000-8000-0000000e7a1d")
_ALERT = {RiskLevel.MEDIUM, RiskLevel.HIGH}


def load_cases(paths: Iterable[Path]) -> list[EvalCase]:
    cases: list[EvalCase] = []
    for p in paths:
        cases += [EvalCase.model_validate_json(line) for line in Path(p).read_text(encoding="utf-8").splitlines()
                  if line.strip()]
    return cases


def run_case(case: EvalCase, pipeline: AnalysisPipeline) -> AnalysisOutcome:
    m = case.message
    ingested = build_message(
        user_id=EVAL_USER,
        channel=Channel.MANUAL,
        body_text=m.body_text,
        body_html=m.body_html,
        subject=m.subject,
        sender=make_sender(m.sender.display_name, m.sender.address, m.sender.auth),
        reply_to=make_sender(None, m.reply_to) if m.reply_to else None,
        received_at=m.received_at,
    )
    return pipeline.run(ingested)


@dataclass
class CaseResult:
    case_id: str
    expected: RiskLevel
    acceptable: list[RiskLevel]
    obtained: RiskLevel
    must_alert: bool
    alerted: bool
    latency_ms: int
    origin: str

    @property
    def level_ok(self) -> bool:
        return self.obtained in self.acceptable


@dataclass
class Metrics:
    n: int
    tp: int
    fp: int
    fn: int
    tn: int
    inconclusive: int
    level_ok: int
    latencies_ms: list[int] = field(default_factory=list)

    @property
    def precision(self) -> float | None:
        return self.tp / (self.tp + self.fp) if (self.tp + self.fp) else None

    @property
    def recall(self) -> float | None:
        return self.tp / (self.tp + self.fn) if (self.tp + self.fn) else None

    @property
    def f1(self) -> float | None:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p is not None and r is not None and (p + r) else None

    @property
    def false_positive_rate(self) -> float | None:
        return self.fp / (self.fp + self.tn) if (self.fp + self.tn) else None

    def percentile(self, q: float) -> int | None:
        if not self.latencies_ms:
            return None
        s = sorted(self.latencies_ms)
        return s[min(len(s) - 1, max(0, math.ceil(q * len(s)) - 1))]


def wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float] | None:
    """Intervalo de confianza de Wilson al 95 % para una proporción."""
    if n == 0:
        return None
    p = successes / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, centre - half), min(1.0, centre + half)


def evaluate(cases: Iterable[EvalCase], pipeline: AnalysisPipeline) -> tuple[list[CaseResult], Metrics]:
    results: list[CaseResult] = []
    for c in cases:
        out = run_case(c, pipeline)
        level = out.assessment.risk_level
        results.append(CaseResult(c.case_id, c.expected.risk_level, list(c.expected.acceptable_levels), level,
                                  c.expected.must_alert, level in _ALERT, out.latency_ms, c.origin.value))
    m = Metrics(n=len(results), tp=0, fp=0, fn=0, tn=0, inconclusive=0, level_ok=0,
                latencies_ms=[r.latency_ms for r in results])
    for r in results:
        if r.must_alert and r.alerted:
            m.tp += 1
        elif not r.must_alert and r.alerted:
            m.fp += 1
        elif r.must_alert and not r.alerted:
            m.fn += 1
        else:
            m.tn += 1
        m.inconclusive += r.obtained is RiskLevel.INCONCLUSIVE
        m.level_ok += r.level_ok
    return results, m
