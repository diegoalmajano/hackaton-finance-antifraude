"""Métricas y preflight de evaluación, solo datos dev y transportes SIMULADOS."""
from pathlib import Path
from types import SimpleNamespace
import json
import pytest
import antifraude.evaluation as ev
from antifraude.ai.budget import AiPolicy
from antifraude.ai.claude import AiTimeout, ClaudeAnalyzer
from antifraude.app.pipeline import AnalysisPipeline
from antifraude.contracts.common import RiskLevel
from antifraude.contracts.evaluation import CaseOrigin, Medium
from antifraude.intel.entities import EntityDirectory

ROOT = Path(__file__).resolve().parents[1]


def fraud():
    return ev.load_cases([ROOT / "eval/datasets/dev/demo.jsonl"])[1]


def pipe(ai=None):
    return AnalysisPipeline(EntityDirectory.load_default(include_fictitious=True), ai)


@pytest.mark.parametrize("tp,fp,fn,expected", [(0,2,3,0.0),(0,0,1,0.0),(0,1,0,0.0),(0,0,0,None),(1,1,1,0.5)])
def test_f1_cero_no_se_confunde_con_no_definido(tp, fp, fn, expected):
    m = ev.Metrics(n=tp+fp+fn, tp=tp, fp=fp, fn=fn, tn=0, inconclusive=0, level_ok=0)
    assert m.f1 == expected


@pytest.mark.parametrize("mode", ["ia", "ambos"])
def test_preflight_ia_bloqueada_no_lee_ni_marca_sellado(mode, tmp_path, monkeypatch):
    for key in ("ANTHROPIC_API_KEY", "CLAUDE_MODEL"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("AI_ENABLED", "0")
    monkeypatch.setenv("AI_BUDGET_USD", "0")
    monkeypatch.setattr(ev, "RESULTS_DIR", tmp_path / "results")
    def forbidden(*args, **kwargs):
        pytest.fail("El preflight debe impedir leer/hash/ejecutar cualquier conjunto")
    monkeypatch.setattr(ev, "load_cases", forbidden)
    monkeypatch.setattr(ev, "_sha256", forbidden)
    monkeypatch.setattr(Path, "is_file", lambda self: True)
    # Solo nombre de ruta inexistente: nunca se crea ni se consulta un conjunto sellado.
    assert ev.main(["--modo",mode,"--sellado",str(tmp_path/"inexistente.jsonl"),"--sha256","0"*64]) == 3
    assert not (tmp_path / "results").exists()


def test_una_llamada_cache_y_bloqueo_no_triplican_consumo(tmp_path):
    sent = []
    def transport(params):
        sent.append(params)
        return {"model":"claude-sonnet-5-5", "stop_reason":"end_turn",
                "content":[{"type":"text","text":json.dumps({"tactics":[]})}],
                "usage":{"input_tokens":1000,"output_tokens":200}}
    ai = ClaudeAnalyzer(policy=AiPolicy(enabled=True,model="claude-sonnet-5-5",budget_usd="0.50",
        max_requests=1,ledger_path=tmp_path/"simulado.json"),api_key=None,transport=transport)
    a=fraud()
    b=a.model_copy(update={"case_id":"dev-9802"})
    changed=a.message.model_copy(update={"body_text":a.message.body_text+"\nAviso sintético diferente."})
    c=a.model_copy(update={"case_id":"dev-9803","message":changed})
    run=ev.evaluate_config("simulado",[a,b,c],pipe(ai))
    assert len(sent) == 1 and run.ai_calls == 1
    assert run.ai_failures == 0
    assert run.cost_usd == pytest.approx(0.004)
    data=ev.metrics_dict(run)
    assert data["analisis_ia_bloqueados"] == 1
    assert data["respuestas_ia_reutilizadas"] == 1


def test_timeout_sin_usage_no_se_presenta_como_coste_total_cero(tmp_path):
    def transport(params):
        raise AiTimeout("fallo SIMULADO")
    ai = ClaudeAnalyzer(policy=AiPolicy(enabled=True,model="claude-sonnet-5-5",budget_usd="0.50",
        ledger_path=tmp_path/"simulado.json"),api_key=None,transport=transport)
    run=ev.evaluate_config("simulado",[fraud()],pipe(ai))
    data=ev.metrics_dict(run)
    assert data["llamadas_ia"] == 1 and data["fallos_ia"] == 1
    assert data["coste_real_usd"] is None
    assert data["coste_con_usage_usd"] == 0
    assert data["solicitudes_sin_coste_usage"] == 1


def test_agregados_por_origen_medio_citas_y_parcial_sin_filtrar_textos(monkeypatch):
    a=fraud()
    b=a.model_copy(update={"case_id":"dev-9802","origin":CaseOrigin.SYNTHETIC_HUMAN,
        "message":a.message.model_copy(update={"medium":Medium.SMS})})
    quote=a.expected.expected_quotes[0]
    out=SimpleNamespace(assessment=SimpleNamespace(risk_level=RiskLevel.HIGH,is_partial=True,
        evidence=[SimpleNamespace(quote=quote)]),latency_ms=4,ai=None)
    monkeypatch.setattr(ev,"run_case",lambda *args:out)
    data=ev.metrics_dict(ev.evaluate_config("reglas",[a,b],pipe()))
    assert data["por_origen"]["synthetic_ai"]["casos"] == 1
    assert data["por_origen"]["synthetic_human"]["casos"] == 1
    assert data["por_medio"]["email"]["casos"] == 1
    assert data["por_medio"]["sms"]["casos"] == 1
    assert data["analisis_parciales"] == 2
    assert data["citas_esperadas"] == 2*len(a.expected.expected_quotes)
    assert data["citas_esperadas_cubiertas"] == 2
    assert quote not in json.dumps(data)
    assert a.message.body_text not in json.dumps(data)



def test_adaptador_sin_telemetria_no_inventa_numero_de_llamadas_ni_coste():
    from antifraude.contracts.ai import AiFindings, AiOutput, AiUsage
    from antifraude.contracts.checks import CheckStatus
    class CustomAi:
        def analyze(self, message, technical_findings):
            return AiFindings(status=CheckStatus.DONE,output=AiOutput(),
                usage=AiUsage(input_tokens=1,output_tokens=1,cost_usd=0.01))
    data=ev.metrics_dict(ev.evaluate_config("simulado",[fraud()],pipe(CustomAi())))
    assert data["llamadas_ia"] is None and data["fallos_ia"] is None
    assert data["coste_real_usd"] is None and data["coste_con_usage_usd"] is None


def test_ambiguos_no_inflan_falsos_positivos_y_abstencion_fraude_es_falso_negativo():
    def item(id,expected,obtained,must_alert):
        return ev.CaseResult(id,expected,[expected],obtained,must_alert,
            obtained in {RiskLevel.HIGH,RiskLevel.MEDIUM},1,"synthetic_human","email")
    results=[item("dev-9801",RiskLevel.HIGH,RiskLevel.INCONCLUSIVE,True),
             item("dev-9802",RiskLevel.LOW,RiskLevel.MEDIUM,False),
             item("dev-9803",RiskLevel.INCONCLUSIVE,RiskLevel.MEDIUM,False)]
    _,m=ev._metrics_from(results)
    assert (m.tp,m.fp,m.fn,m.tn)==(0,1,1,0)
    assert m.ambiguous_n==1 and m.ambiguous_alerted==1
    assert m.inconclusive==1 and m.f1==0
    data=ev.metrics_dict(ev.ConfigRun("simulado",results,m))
    assert data["tasa_no_concluyente"]==pytest.approx(1/3)


def test_informe_identifica_fuentes_modificadas_y_entorno_sin_datos(monkeypatch):
    monkeypatch.setattr(ev,"_git_dirty",lambda:True)
    run=ev.evaluate_config("reglas",[fraud()],pipe())
    data=ev.build_report("desarrollo",[run],model=None,sealed_sha256=None)
    assert data["arbol_trabajo_sucio"] is True
    assert data["python"] and data["plataforma"] and len(data["requirements_lock_sha256"])==64
    assert "NO es una evaluación independiente" in data["aviso"]
