"""Controlador del asistente por WhatsApp (SPEC-073): de un evento de Meta a la respuesta.

Flujo por mensaje:

1. Si ya se atendió (Meta reintenta), se ignora.
2. Si trae un código de acceso (``YELO-XXXX-XXXX``), se vincula al número (en hash) y se confirma.
3. «olvidar» borra la conversación y el vínculo con el código.
4. Si el número no tiene código vigente (y WhatsApp lo exige), se le explica cómo pedirlo:
   el LLM no se llama.
5. Si lo tiene, se gasta un mensaje del cupo, responde el agente (todas las aseguradoras,
   canales e identificación) y la respuesta vuelve por WhatsApp.
"""

import logging
from collections import deque
from collections.abc import Callable

from sb_asistente import config
from sb_asistente.controller.agente import AgenteAsistente
from sb_asistente.model import whatsapp
from sb_asistente.model.acceso import AccesoDenegadoError, CodigosAcceso

logger = logging.getLogger(__name__)

PIDE_CODIGO = (
    "Hola, soy Yelo, el asistente de seguros de Yellow Data (proyecto académico, no somos una "
    "aseguradora). Para conversar con la IA envíame tu código de acceso (YELO-XXXX-XXXX). "
    "No me envíes tu cédula ni tu número de póliza."
)
SOLO_TEXTO = "Por ahora solo leo mensajes de texto. Escríbeme tu pregunta."
OLVIDADO = "Listo: borré esta conversación y el código de este número."
ERROR = "No pude responder en este momento. Intenta de nuevo en unos minutos."

_atendidos: deque[str] = deque(maxlen=config.WHATSAPP_RECORDAR_IDS)


def _ya_atendido(mensaje_id: str) -> bool:
    if mensaje_id in _atendidos:
        return True
    _atendidos.append(mensaje_id)
    return False


def _codigos() -> CodigosAcceso:
    return CodigosAcceso(config.ACCESO_DB)


def _hora(c: object) -> str:
    expira = getattr(c, "expira", None)
    return expira.astimezone().strftime("%d/%m %H:%M") if expira else ""


def atender(
    evento: dict,
    agente: Callable[[], AgenteAsistente],
    enviador: whatsapp.Enviador,
) -> int:
    """Responde los mensajes de un evento; devuelve cuántos respondió (para las pruebas y el log)."""
    respondidos = 0
    for m in whatsapp.mensajes(evento):
        if _ya_atendido(m.id):
            continue
        canal = whatsapp.canal_de(m.de)
        try:
            texto = _respuesta(m, canal, agente)
        except Exception:  # noqa: BLE001 - el detalle va al log; la persona recibe un aviso
            logger.exception("whatsapp: no se pudo responder un mensaje")
            texto = ERROR
        try:
            enviador.enviar(m.de, texto)
            respondidos += 1
        except Exception:  # noqa: BLE001 - Meta rechazó el envío (token vencido, número no permitido)
            logger.exception("whatsapp: Meta rechazó la respuesta")
    return respondidos


def _respuesta(m: whatsapp.Entrante, canal: str, agente: Callable[[], AgenteAsistente]) -> str:
    if m.texto is None:
        return SOLO_TEXTO
    codigo = whatsapp.codigo_en(m.texto)
    if codigo:
        try:
            c = _codigos().vincular(canal, codigo)
        except AccesoDenegadoError as exc:
            return str(exc)
        return f"Código activado: tienes {c.restantes} mensajes con IA hasta el {_hora(c)}. ¿Qué necesitas?"
    if m.texto.strip().lower() in {"olvidar", "olvidame", "olvídame", "borrar"}:
        agente().olvidar(canal)
        _codigos().desvincular(canal)
        return OLVIDADO
    if config.WHATSAPP_EXIGE_CODIGO:
        try:
            _codigos().consumir_canal(canal)  # gasta el mensaje ANTES de llamar al LLM
        except AccesoDenegadoError as exc:
            return PIDE_CODIGO if "aún no tiene" in str(exc) else f"{exc} {PIDE_CODIGO}"
    turno = agente().responder(m.texto, canal, canal)
    return whatsapp.para_whatsapp(turno.salida.respuesta, turno.salida.fuentes)


def enviador_por_defecto() -> whatsapp.Enviador | None:
    """Cliente de la Graph API con las credenciales del ``.env`` (``None`` si faltan)."""
    if not (config.WHATSAPP_TOKEN and config.WHATSAPP_PHONE_NUMBER_ID):
        return None
    return whatsapp.ClienteGraph(
        config.WHATSAPP_TOKEN, config.WHATSAPP_PHONE_NUMBER_ID, config.WHATSAPP_GRAPH_VERSION
    )


def suscripcion_valida(modo: str | None, token: str | None) -> bool:
    """Indica si Meta está verificando nuestro webhook con el token correcto."""
    return whatsapp.suscripcion_valida(modo, token, config.WHATSAPP_VERIFY_TOKEN)


def firma_valida(cuerpo: bytes, cabecera: str | None) -> bool:
    """Indica si el evento lo firmó Meta con la clave secreta de nuestra app."""
    return whatsapp.firma_valida(cuerpo, cabecera, config.WHATSAPP_APP_SECRET)


def configurado() -> bool:
    """True si el ``.env`` tiene lo mínimo para verificar el webhook y los eventos."""
    return bool(config.WHATSAPP_VERIFY_TOKEN and config.WHATSAPP_APP_SECRET)
