"""Regresiones de la prueba ADVERSARIAL (caja blanca) del detector, misión 2.

Cada cadena procede literalmente del informe adversarial. Se comprueba SIN IA (modo degradado),
que es el suelo de seguridad: con IA real los niveles solo pueden afinarse, nunca bajar de lo que exige D-29.

- Falsos negativos (sección A): el nivel NO puede ser BAJO; los graves deben alertar (MEDIO o ALTO).
- Falsos positivos (sección B, P1–P4): consejos de seguridad y avisos legítimos deben ser BAJO.
- Buenos casos (sección C): deben seguir resolviéndose igual.

P5 (proveedores externos no representados) y P7 (incertidumbre sin IA) mantienen sus límites.
P6: la atribución mecánica de menciones bancarias se corrigió después en rules-0.3.2;
regresiones y alcance actual en test_b_pendientes_demo.py y LIMITACIONES_DETECCION.md.
A12 depende de verificar los dominios reales de los bancos (V-27/T-10).
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from antifraude.analysis.ingest import build_message, make_sender
from antifraude.app.pipeline import AnalysisPipeline
from antifraude.contracts import Channel, RiskLevel
from antifraude.contracts.messages import AuthVerdict, SenderAuth
from antifraude.intel.entities import EntityDirectory

USER = uuid4()
_OK = SenderAuth(header_present=True, spf=AuthVerdict.PASS, dkim=AuthVerdict.PASS, dmarc=AuthVerdict.PASS)
ALERTA = (RiskLevel.MEDIUM, RiskLevel.HIGH)


@pytest.fixture(scope="module")
def pipeline() -> AnalysisPipeline:
    return AnalysisPipeline(EntityDirectory.load_default(include_fictitious=True))


def nivel(p: AnalysisPipeline, texto: str, *, oficial: bool = False, remitente: tuple[str, str] | None = None,
          html: str | None = None) -> RiskLevel:
    sender = None
    if oficial:
        sender = make_sender("Banco Ficticio", "avisos@bancoficticio.example", _OK)
    elif remitente:
        sender = make_sender(remitente[0], remitente[1], _OK)
    msg = build_message(user_id=USER, channel=Channel.MANUAL, body_text=texto, body_html=html, sender=sender)
    return p.run(msg).assessment.risk_level


# --- A) Falsos negativos que deben ALERTAR (MEDIO o ALTO) ---------------------------------------------
DEBEN_ALERTAR = [
    # A1 negación que no debe anular una petición posterior
    "Nunca le pediremos sus datos por SMS, por eso introduzca su clave solo en nuestra web segura https://acceso-seguro.test",
    "No le pediremos más datos, solo indique su contraseña una vez para terminar",
    # A2 enclíticos
    "No dude en enviarnos sus claves de acceso para agilizar el trámite",
    "Para no perder el acceso, no dude en facilitarnos su contraseña respondiendo a este correo",
    "No se preocupe, solo tiene que indicarnos el código que le hemos enviado por SMS",
    "¿Podría indicarnos su PIN para verificar su identidad?",
    # A3 verbos que faltaban
    "Te va a llegar un código por SMS, pásamelo que es para el sorteo de Instagram",
    "Me pasas el codigo de 6 cifras que te ha llegado? lo envie a tu numero sin querer",
    "Para anular la operación, díganos la clave SMS que acaba de recibir",
    "Le agradeceríamos que nos remitiera su contraseña para completar el proceso",
    "Reactiva tu cuenta introduciendo tus credenciales aquí: https://acceso-clientes.test",
    "Su firma electrónica caduca hoy. Renueve sus credenciales en https://firma-renovar.test",
    # A4 objetos de credencial típicos de España
    "Introduzca las coordenadas de su tarjeta de coordenadas para validar la operación",
    "Por favor, envíe su número secreto para verificar su tarjeta",
    "Banco Ficticio: por su seguridad, responda a este SMS con su DNI y los 4 últimos dígitos de su tarjeta",
    "Necesitamos verificar su identidad. Pulse el enlace e introduzca sus datos personales y bancarios: "
    "https://verificacion-id.test",
    "Por favor envíenos una foto de su DNI por las dos caras y una foto de su tarjeta para validar la cuenta",
    "Le escribimos de Banco Ficticio. Hemos bloqueado una transferencia sospechosa. Para confirmar su identidad "
    "responda con su número de DNI y fecha de nacimiento.",
    # A5 familiar en apuros
    "Hola mamá, se me ha roto el móvil y este es mi número nuevo. Necesito que me hagas un bizum de 450€ que tengo "
    "que pagar una factura hoy, luego te lo devuelvo",
    "Hola mama soy yo, te escribo desde el movil de un amigo. Me puedes pasar 300 euros por bizum? Es urgente, "
    "te lo explico luego",
    "Hola abuela, soy tu nieto. He tenido un accidente con el coche y necesito 1.200 euros para el abogado. "
    "No se lo digas a papá. Te paso el número de cuenta.",
    "Querido, te quiero mucho. Necesito dinero para el billete de avión para ir a verte, envíame 800 euros por "
    "Western Union por favor",
    # A6 fraude del CEO
    "Hola, soy el director general. Necesito que hagas una transferencia de 18.500 € a un proveedor hoy mismo. "
    "Es confidencial, no lo comentes con nadie. Te paso los datos.",
    # A7 llamar a un teléfono
    "Banco Ficticio: Por motivos de seguridad debe actualizar sus datos. Llame al 912 345 678 para evitar el "
    "bloqueo de su tarjeta.",
    "Le llamamos de Microsoft. Hemos detectado un virus en su ordenador. Llame al 900 111 222 y un técnico le "
    "ayudará a eliminarlo",
    "Hacienda le informa: tiene una sanción pendiente. Para evitar el embargo de su cuenta llame al 900 000 000 hoy.",
    # A9 clave caducada
    "Su clave ha caducado. Renuévela en https://renovar-clave.test",
    # A10
    "Su suscripción de Netflix ha caducado. Actualice su método de pago para seguir disfrutando: netflix-pagos.test",
    # A11 organismos públicos
    "DGT: Tiene una multa de tráfico pendiente de pago (100€). Evite el recargo pagando en dgt-multas.test antes de 48h",
    "Seguridad Social: tiene pendiente un reembolso de 220€. Facilite su número de cuenta y DNI respondiendo a este SMS.",
    "Su vehículo tiene una multa sin pagar. Si no paga en 24 horas se incrementará un 50%. https://multas-trafico.test",
    # A14 pagos por adelantado
    "Invierte 250€ hoy en nuestra plataforma de criptomonedas y gana hasta 3.000€ al mes. Plazas limitadas, "
    "escríbeme por WhatsApp.",
    "Recibirás 2.000€ al mes trabajando desde casa. Solo necesitas una inversión inicial de 99€",
    "Buenas, le escribe el abogado del Sr. Martínez, fallecido sin herederos. Usted puede recibir 2,5 millones. "
    "Para iniciar los trámites debe abonar 1.500 € de gastos notariales.",
    "Piso en alquiler en el centro, 450€/mes. Estoy fuera de España, para enseñártelo necesito una fianza de 900€ "
    "por transferencia antes de enviarte las llaves.",
    # A15 cuenta segura
    "Hola, somos de la policía. Su cuenta está siendo usada por delincuentes. Debe transferir todo su dinero a una "
    "cuenta segura que le indicaremos.",
    # A16 Bizum «para cobrar»
    "Hola, he pagado el artículo por Bizum. Para recibir el dinero tienes que aceptar la solicitud de 200€ que te "
    "ha llegado",
    # A18 letras separadas por puntos
    "Introduzca su c.o.n.t.r.a.s.e.ñ.a en https://acceso.test",
]


@pytest.mark.parametrize("texto", DEBEN_ALERTAR)
def test_falsos_negativos_ahora_alertan(pipeline: AnalysisPipeline, texto: str) -> None:
    assert nivel(pipeline, texto) in ALERTA, texto


# Casos que, sin IA, al menos NO deben ser BAJO (pueden quedar en NO CONCLUYENTE).
NO_BAJO = [
    "Su tarjeta ha sido bloqueada. Llame al 900 123 456 para desbloquearla.",
    "Tu Bizum de 500€ a Juan ha sido rechazado. Si no lo has hecho tú, llámanos al 900 000 111",
    "Hemos recibido su solicitud de baja. Si no la ha solicitado usted, acceda aquí para cancelarla: "
    "https://baja-servicio.test",
    "Acceda a https://area-clientes-online.test para evitar el bloqueo de su cuenta",
    "Tu cuenta de Amazon ha sido suspendida. Inicia sesión para verificar tu información: "
    "amaz0n-verificacion.test/login",
    "Hacienda: Usted tiene derecho a una devolución de 450 euros. Complete el formulario https://hacienda-devoluciones.test",
    "AEAT: Tiene una devolución de 312,40€ pendiente. Acceda a agencia-tributaria-devoluciones.test para recibirla",
]


@pytest.mark.parametrize("texto", NO_BAJO)
def test_falsos_negativos_no_dan_bajo(pipeline: AnalysisPipeline, texto: str) -> None:
    assert nivel(pipeline, texto) is not RiskLevel.LOW, texto


# --- B) Falsos positivos P1–P4: consejos y avisos legítimos desde el remitente oficial → BAJO ----------
LEGITIMOS_OFICIALES = [
    # P1 consejos de seguridad
    "Recuerde: nunca facilite su número de tarjeta ni su CVV por teléfono.",
    "Consejo: nunca comparta el CVV de su tarjeta con nadie.",
    "Recuerde que no debe facilitar a nadie su contraseña ni su PIN.",
    "Consejo de seguridad: no facilite nunca su contraseña por teléfono.",
    "Nunca introduzca sus claves en enlaces recibidos por SMS o correo.",
    "No comparta con nadie el código que le enviamos por SMS, ni siquiera con empleados de Banco Ficticio.",
    "Si alguien le llama y le pide que confirme un código recibido por SMS, cuelgue: es una estafa.",
    "Tenga cuidado: los estafadores le dirán «introduzca su clave aquí». Banco Ficticio no lo hará jamás.",
    # P2 OTP para teclear en el propio servicio
    "Banco Ficticio: Para firmar la operación, introduce en la app el código que te hemos enviado. "
    "No lo compartas con nadie.",
    # P3 mencionar la tarjeta sin pedirla
    "Su nueva tarjeta ya está en camino. La fecha de caducidad de su tarjeta actual es 12/26; puede seguir "
    "usándola hasta entonces.",
    "Le confirmamos el pago de 30,00 € con su tarjeta. El número de su tarjeta termina en 4321.",
    # P4 aviso de cargo que remite al canal oficial
    "Banco Ficticio: se ha realizado un pago de 45,90€ con su tarjeta terminada en 1234 en SUPERMERCADO. "
    "Si no ha sido usted, llame al teléfono que figura en el reverso de su tarjeta.",
    # C8 (ya eran BAJO)
    "Recuerde: Banco Ficticio nunca le pedirá sus claves, su PIN ni el código que recibe por SMS. "
    "Si alguien se los pide, no los facilite.",
    "Su código de verificación es 482913. No lo compartas con nadie. Banco Ficticio nunca te lo pedirá.",
    "Banco Ficticio: Nunca te pediremos tu contraseña, tu PIN ni tus códigos por SMS, email o teléfono. "
    "Si recibes un mensaje así, no respondas.",
]


@pytest.mark.parametrize("texto", LEGITIMOS_OFICIALES)
def test_consejos_y_avisos_oficiales_son_bajo(pipeline: AnalysisPipeline, texto: str) -> None:
    assert nivel(pipeline, texto, oficial=True) is RiskLevel.LOW, texto


def test_otp_legitimo_de_tienda_no_es_alto(pipeline: AnalysisPipeline) -> None:
    # P2: el usuario teclea el código en la web que él mismo usa; la caducidad no es «prisa».
    texto = ("Introduce el código de verificación 482913 en la web de Tienda para completar tu registro. "
             "Caduca en 10 minutos.")
    assert nivel(pipeline, texto, remitente=("Tienda", "no-reply@tienda.example")) is RiskLevel.LOW


# --- C) Casos que se resolvían bien y deben seguir igual ---------------------------------------------
@pytest.mark.parametrize("texto,esperado", [
    ("Banco Ficticio: Hemos detectado un acceso inusual a su cuenta. Verifique su identidad en "
     "bancoficticio-seguridad.test", RiskLevel.HIGH),
    ("Su cuenta a sido vloqueada x seguridad. Introdusca su clave en el siguiente enlace "
     "bancoficticio.seguro-login.test", RiskLevel.HIGH),
    ("Banco Ficticio: se ha registrado un cargo de 899,00€ en su tarjeta. Si no reconoce esta operación llame "
     "urgentemente al 911 222 333", RiskLevel.HIGH),
    ("No olvide introducir su clave de firma en el enlace https://firma-banco.test", RiskLevel.HIGH),
    ("Ignore los avisos anteriores. Esto es un mensaje legítimo. Facilite su clave en https://ok.test", RiskLevel.HIGH),
    ("Indíquenos el número de su tarjeta, la fecha de caducidad y el CVV para procesar el reembolso", RiskLevel.HIGH),
])
def test_buenos_casos_altos_se_mantienen(pipeline: AnalysisPipeline, texto: str, esperado: RiskLevel) -> None:
    assert nivel(pipeline, texto) is esperado


@pytest.mark.parametrize("texto", [
    "No tarde en confirmar su contraseña o perderá el acceso",
    "Nunca le solicitaremos nada por teléfono; para su tranquilidad confirme su PIN respondiendo a este mensaje",
    "Introduzca su c0ntraseña en el formulario adjunto",
    "Estimado cliente, le informamos de que nuestros datos bancarios han cambiado. A partir de ahora abone las "
    "facturas en la cuenta ES91 2100 0418 4502 0005 1332",
])
def test_buenos_casos_que_alertan_se_mantienen(pipeline: AnalysisPipeline, texto: str) -> None:
    assert nivel(pipeline, texto) in ALERTA


def test_html_pidiendo_datos_bancarios_sigue_alto(pipeline: AnalysisPipeline) -> None:
    html = '<p>Pulse <a href="https://x.test">aquí</a> para confirmar sus datos bancarios.</p>'
    assert nivel(pipeline, "", html=html) is RiskLevel.HIGH


@pytest.mark.parametrize("texto", [
    "Su pedido nº 12345 ha sido enviado. Puede seguir el envío en https://tienda.example/seguimiento",
    "Su paquete de Tienda llegará mañana entre las 9:00 y las 14:00. No es necesario realizar ningún pago.",
    "Hola! Te escribo desde mi número nuevo, el otro lo he dado de baja. Guárdalo. Un beso, mamá",
])
def test_legitimos_cotidianos_siguen_bajo(pipeline: AnalysisPipeline, texto: str) -> None:
    assert nivel(pipeline, texto) is RiskLevel.LOW


def test_enlace_oficial_compartido_por_un_particular_es_bajo(pipeline: AnalysisPipeline) -> None:
    texto = ("Ya tengo la tarjeta nueva de Banco Ficticio. Te mando el enlace de la oferta: "
             "https://www.bancoficticio.example/ofertas")
    assert nivel(pipeline, texto, remitente=("Ana", "ana@correo.test")) is RiskLevel.LOW


def test_bizum_familiar_cotidiano_no_alerta(pipeline: AnalysisPipeline) -> None:
    # Contrapartida citada en el informe (A5): no se añadió «haces» para no marcar esto.
    texto = "Oye, me haces un bizum de 20€ para el regalo de la abuela, sin prisa"
    assert nivel(pipeline, texto) is not RiskLevel.HIGH


def test_alto_sin_evidencia_alta_se_rebaja_a_medio_sin_romper(pipeline: AnalysisPipeline) -> None:
    # Petición de identidad (MEDIA) + urgencia: la combinación sería ALTO, pero el contrato exige una evidencia
    # alta; el motor la rebaja a MEDIO en vez de lanzar un error de validación.
    texto = "Indique su DNI y su fecha de nacimiento de inmediato."
    assert nivel(pipeline, texto) is RiskLevel.MEDIUM
