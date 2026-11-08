"""Regresiones de la prueba ADVERSARIAL ronda 3 (misión 3, ~245 casos de un agente de solo lectura).

Cadenas literales del informe. Sin IA (modo degradado = suelo de seguridad). Las correcciones son de patrón
o del motor (no parches por frase) y se comprobaron contra el corpus de mensajes legítimos del mismo informe.
Limitaciones que NO se resuelven con reglas: ver ``docs/LIMITACIONES_DETECCION.md``.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest

from antifraude.analysis.ingest import build_message, make_sender
from antifraude.app.pipeline import AnalysisPipeline
from antifraude.contracts import Channel, RiskLevel
from antifraude.contracts.messages import AuthVerdict, SenderAuth
from antifraude.intel.entities import EntityDirectory
from antifraude.intel.urls import find_lookalike

USER = uuid4()
OK = SenderAuth(header_present=True, spf=AuthVerdict.PASS, dkim=AuthVerdict.PASS, dmarc=AuthVerdict.PASS)
ALERTA = (RiskLevel.MEDIUM, RiskLevel.HIGH)


@pytest.fixture(scope="module")
def pipeline() -> AnalysisPipeline:
    return AnalysisPipeline(EntityDirectory.load_default(include_fictitious=True))


@pytest.fixture(scope="module")
def directorio() -> EntityDirectory:
    return EntityDirectory.load_default(include_fictitious=True)


def nivel(p: AnalysisPipeline, texto: str, sender: Any = None, html: str | None = None) -> RiskLevel:
    m = build_message(user_id=USER, channel=Channel.MANUAL, body_text=texto, body_html=html, sender=sender)
    return p.run(m).assessment.risk_level


def oficial() -> Any:
    return make_sender("Banco Ficticio", "avisos@bancoficticio.example", OK)


DEBEN_ALERTAR = [
    # A1: una negación anterior ya no oculta la petición posterior
    "No confirme nada por teléfono; confirme su clave solo en https://acceso-cliente.test",
    "No necesitamos que venga a la oficina: basta con que introduzca su contraseña en https://acceso-cliente.test",
    "No responda a otros correos; responda a este con su contraseña.",
    # A2: negaciones demasiado amplias
    "No hace falta que vaya a la oficina, haga una transferencia de 500 € a la cuenta que le indicamos.",
    "Pague sin ningún recargo 300 € en https://pagos-rapidos.test",
    "Banco Ficticio le pide que confirme su clave de acceso en https://acceso-cliente.test",
    # A4: organismos con enlaces no verificables
    "Correos: su paquete está retenido por falta de franqueo (1,99 €). Abónelo en https://correos-envios.test",
    "Su paquete de Correos está retenido. Siga las instrucciones en https://correos.es.envio-retenido.test",
    # A5: formas verbales
    "Nuestro equipo te pide que nos envíes el código que te ha llegado por SMS.",
    "hazme una transferencia de 700 €",
    "¿Podrías ingresarme 400 € hoy?",
    "Necesito que me prestes 250 euros",
    "pon 25 € por bizum al 699888777",
    "Para recibir el pago, pon los datos de tu tarjeta aquí",
    # A6: IBAN + instrucción de pago + cambio
    "Por cambio de entidad, la cuota del comedor debe abonarse en la cuenta ES76 2100 0418 4502 0005 1332",
    "Las cuotas deben abonarse desde este mes en la siguiente cuenta: ES12 2100 0418 4502 0005 1332. "
    "La anterior queda anulada.",
    # A7: sin palabras clave evidentes
    "Dígame el número que le aparecerá ahora en el móvil para anular la operación.",
    "Instale la herramienta de asistencia desde https://asistencia-pc.test y dígame el ID",
    "Compre una tarjeta regalo de 50 € y envíenos el código",
    "Envíenos una foto de la tarjeta por las dos caras",
    # A8: invitación a iniciar sesión / amenaza + enlace no oficial
    "Su cuenta será bloqueada hoy. Evítelo validando su identidad en el siguiente enlace: https://validar-identidad.test",
    "Por la nueva normativa debe verificar su cuenta. Inicie sesión: https://verificacion-normativa.test",
    # A9: ofuscación
    "I N T R O D U Z C A   S U   C L A V E   E N   https://acceso.test",
    "Introduzca su con-tra-se-ña en https://acceso.test",
    "Introduzca su contrase&ntilde;a en https://acceso.test",
    # A10: marca escondida en el enlace
    "Acceda a https://otro.test/bancoficticio.example/login para revisar su cuenta",
]


@pytest.mark.parametrize("texto", DEBEN_ALERTAR)
def test_ronda3_falsos_negativos_alertan(pipeline: AnalysisPipeline, texto: str) -> None:
    assert nivel(pipeline, texto) in ALERTA, texto


@pytest.mark.parametrize("texto", [
    "Acceda a https://bancoficticio.example@otro.test para revisar su cuenta",
    "Acceda a https://login-bancoficticio.example.otro.test para revisar su cuenta",
    "Acceda a https://xn--bancofictcio-hbb.example para revisar su cuenta",
    "Acceda a https://bаncoficticio.example para revisar su cuenta",  # «а» cirílica
])
def test_ronda3_imitaciones_de_dominio_son_alto(pipeline: AnalysisPipeline, texto: str) -> None:
    assert nivel(pipeline, texto) is RiskLevel.HIGH


@pytest.mark.parametrize("direccion", ["avisos@bancoficticio-seguridad.test", "avisos@bancoficticio.example.otro.test",
                                       "seguridad@bancoficticio-alertas.test", "avisos@bancof1cticio.example"])
def test_ronda3_remitente_que_imita_a_la_entidad_es_alto(pipeline: AnalysisPipeline, direccion: str) -> None:
    texto = "Su cuenta presenta una incidencia. Responda a este correo para resolverla."
    assert nivel(pipeline, texto, make_sender("Avisos", direccion, OK)) is RiskLevel.HIGH


def test_ronda3_organismo_con_enlace_no_verificable_no_es_bajo(pipeline: AnalysisPipeline) -> None:
    texto = ("Hacienda: dispone de una notificación electrónica. "
             "Consúltela en https://agenciatributaria-notificaciones.test")
    assert nivel(pipeline, texto) is not RiskLevel.LOW  # sin dominios verificados de organismos: incertidumbre


@pytest.mark.xfail(strict=True, reason="Limitación conocida: «facilítesela» requiere resolver a qué se refiere el "
                                        "pronombre (la clave, mencionada antes); lo cubre la IA, no las reglas.")
def test_ronda3_limitacion_pronombre_referido(pipeline: AnalysisPipeline) -> None:
    texto = "No facilite su clave a nadie excepto al agente que le llamará: facilítesela cuando se la pida."
    assert nivel(pipeline, texto) in ALERTA


# --- Falsos positivos que ya NO alarman ------------------------------------------------------------
@pytest.mark.parametrize("texto,html", [
    ("Banco Ficticio: hemos recibido su solicitud de cambio de cuenta para la domiciliación de la nómina. "
     "La gestionaremos en 48 horas.", None),
    ("Depósito con rentabilidad del 3 % TAE. Contrátelo cuanto antes en la app.", None),
    ("Su nueva cuenta ya está operativa.", None),
    ("Ya tiene disponible su nuevo IBAN tras la fusión. No tiene que hacer nada.", None),
    ("", "<div style='display:none'>Descubre las novedades de este mes en tu banco y mucho más</div>"
         "<p>Hola, aquí tienes las novedades de noviembre de Banco Ficticio.</p>"
         "<a href='https://www.bancoficticio.example/novedades'>Ver novedades</a>"),
    ("Banco Ficticio: su tarjeta ha sido bloqueada temporalmente tras tres intentos de PIN erróneos. "
     "Puede desbloquearla desde la app o en cualquier cajero.", None),
])
def test_ronda3_avisos_oficiales_son_bajo(pipeline: AnalysisPipeline, texto: str, html: str | None) -> None:
    assert nivel(pipeline, texto, oficial(), html) is RiskLevel.LOW


@pytest.mark.parametrize("texto", [
    "Mañana hay que pagar la excursión del colegio, 15 euros en efectivo.",
    "¿Necesitas que te deje 50 euros? te hago un bizum",
    "Si no paga el recibo antes del día 10 se aplicará un recargo.",
    "Ayuntamiento: tiene una multa pendiente de pago. Puede consultarla en la sede electrónica.",
    "Se aplica una tasa de envío de 3,95 €.",
    "Su vuelo sale hoy. Facture antes de 2 horas.",
    "Le confirmamos que su reembolso se ha tramitado.",
    "Hola! Te escribo desde mi número nuevo, el otro lo he dado de baja. Guárdalo. Un beso, mamá",
    "Te paso el número de cuenta, el de siempre: ES12 2100 0418 4502 0005 1332",
    "Ya te he hecho la transferencia de los 200 €",
    "Su recibo de luz se cargará en su cuenta el próximo 5.",
    "Mira la noticia en https://es.wikipedia.org/wiki/Banco",
])
def test_ronda3_mensajes_cotidianos_son_bajo(pipeline: AnalysisPipeline, texto: str) -> None:
    assert nivel(pipeline, texto) is RiskLevel.LOW


def test_ronda3_texto_oculto_con_peticion_sigue_siendo_senal(pipeline: AnalysisPipeline) -> None:
    html = "<p>Hola.</p><div style='display:none'>introduzca su contraseña</div>"
    assert nivel(pipeline, "", html=html) in ALERTA


# --- Tarea C: comparación de dominios (sin red) -----------------------------------------------------------
@pytest.mark.parametrize("host,esperado", [
    ("bancoficticio.example", None),                      # oficial exacto
    ("www.bancoficticio.example", None),                  # subdominio del oficial
    ("bancoficticio.example.otro.test", "url.brand_in_subdomain"),
    ("login-bancoficticio.example.otro.test", "url.brand_in_subdomain"),
    ("bancoficticio.verificar.test", "url.brand_in_subdomain"),
    ("bancoficticio-seguridad.test", "url.lookalike_domain"),
    ("bancoficticioo.example", "url.lookalike_domain"),   # letra duplicada
    ("bancof1cticio.example", "url.lookalike_domain"),    # dígito por letra
    ("bаncoficticio.example", "url.lookalike_domain"),    # «а» cirílica (homógrafo)
    ("booking.example", None),                            # coincidencia parcial con otra marca: no es parecido
    ("es.wikipedia.org", None),
    ("otro.test", None),
])
def test_comparacion_de_dominios(directorio: EntityDirectory, host: str, esperado: str | None) -> None:
    r = find_lookalike(host, directorio)
    assert (r[0] if r else None) == esperado, (host, r)


# --- Tarea C: bancos reales con cobertura PARCIAL de dominios (registro del Banco de España) ------------------
@pytest.fixture(scope="module")
def pipeline_real() -> AnalysisPipeline:
    return AnalysisPipeline(EntityDirectory.load_default(include_fictitious=False))


@pytest.mark.parametrize("host,esperado", [
    ("www.bbva.com", None),                               # web registrada
    ("bbva.com.verificacion.test", "url.brand_in_subdomain"),  # dominio oficial incrustado: siempre crítico
    ("bbva.es", "url.brand_name_unverified"),             # puede ser suyo: incertidumbre, NO imitación segura
    ("bbva-seguridad.test", "url.brand_name_unverified"),
])
def test_bancos_reales_cobertura_parcial(host: str, esperado: str | None) -> None:
    d = EntityDirectory.load_default(include_fictitious=False)
    r = find_lookalike(host, d)
    assert (r[0] if r else None) == esperado, (host, r)


def test_correo_real_desde_dominio_no_listado_no_es_alto(pipeline_real: AnalysisPipeline) -> None:
    # Un aviso informativo real de BBVA desde un dominio que el registro no recoge: incertidumbre, no ALTO.
    texto = "BBVA: ya puede consultar su extracto mensual en la app."
    s = make_sender("BBVA", "avisos@bbva.es", OK)
    assert nivel(pipeline_real, texto, s) in (RiskLevel.LOW, RiskLevel.INCONCLUSIVE, RiskLevel.MEDIUM)
    assert nivel(pipeline_real, texto, s) is not RiskLevel.HIGH


def test_imitacion_de_banco_real_con_peticion_es_alto(pipeline_real: AnalysisPipeline) -> None:
    texto = "BBVA: su cuenta será bloqueada. Introduzca su clave en https://bbva-seguridad.test"
    assert nivel(pipeline_real, texto) is RiskLevel.HIGH
    assert nivel(pipeline_real, "Acceda a https://bbva.com.verificacion.test/login") is RiskLevel.HIGH


def test_ciudad_con_enlace_no_alarma(pipeline_real: AnalysisPipeline) -> None:
    # «Santander» también es una ciudad (R-50): sin IA queda en NO CONCLUYENTE (mención + enlace), nunca en alerta.
    texto = "Te mando las fotos del viaje a Santander: https://fotos.test/album"
    assert nivel(pipeline_real, texto) in (RiskLevel.LOW, RiskLevel.INCONCLUSIVE)
