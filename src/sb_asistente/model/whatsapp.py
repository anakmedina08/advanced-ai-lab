"""WhatsApp Cloud API (Meta): verificar el webhook, leer mensajes y responder (SPEC-073).

Piezas sin estado y fáciles de probar:

- ``suscripcion_valida``: el «apretón de manos» con el que Meta confirma que el webhook es nuestro.
- ``firma_valida``: cada POST de Meta trae ``X-Hub-Signature-256`` (HMAC-SHA256 del cuerpo con la
  clave secreta de la app); sin firma válida el mensaje se descarta.
- ``mensajes``: los mensajes entrantes de un evento (texto u otro tipo).
- ``para_whatsapp``: Markdown del agente → formato de WhatsApp (``*negrita*``, sin títulos).
- ``ClienteGraph``: envía la respuesta por la Graph API.

Privacidad (Ley 1581): el número de la persona solo se usa como destinatario de la respuesta; lo
que se guarda (memoria del agente, vínculo con el código) es su hash ``canal_de``.
"""

import hashlib
import hmac
import re
from dataclasses import dataclass
from typing import Protocol

import httpx

MAX_TEXTO = 4096  # límite de WhatsApp por mensaje
MAX_FUENTES = 2
_NEGRITA = re.compile(r"\*\*(.+?)\*\*")
_TITULO = re.compile(r"^#{1,6}\s*", re.MULTILINE)
_CODIGO = re.compile(r"\bYELO[\s-]?[A-Z0-9]{4}[\s-]?[A-Z0-9]{4}\b", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class Entrante:
    """Un mensaje que llegó al número; ``texto`` es ``None`` si no es de texto (audio, imagen…)."""

    id: str
    de: str  # número de la persona (wa_id): solo para responder, nunca se guarda en claro
    texto: str | None


class Enviador(Protocol):
    """Lo que necesita el controlador para responder (el real es ``ClienteGraph``)."""

    def enviar(self, para: str, texto: str) -> None:
        """Envía un mensaje de texto."""
        ...


def suscripcion_valida(modo: str | None, token: str | None, esperado: str) -> bool:
    """True si Meta pide suscribirse con nuestro token de verificación (comparación en tiempo constante)."""
    return modo == "subscribe" and bool(esperado) and hmac.compare_digest(token or "", esperado)


def firma_valida(cuerpo: bytes, cabecera: str | None, secreto: str) -> bool:
    """Comprueba ``X-Hub-Signature-256: sha256=<hex>`` con la clave secreta de la app."""
    if not secreto or not cabecera or not cabecera.startswith("sha256="):
        return False
    esperada = hmac.new(secreto.encode(), cuerpo, hashlib.sha256).hexdigest()
    return hmac.compare_digest(cabecera.removeprefix("sha256="), esperada)


def mensajes(evento: dict) -> list[Entrante]:
    """Mensajes entrantes de un evento del webhook (ignora estados de entrega y otros cambios)."""
    salida: list[Entrante] = []
    for entrada in evento.get("entry", []) or []:
        for cambio in entrada.get("changes", []) or []:
            valor = cambio.get("value", {}) or {}
            for m in valor.get("messages", []) or []:
                if not m.get("id") or not m.get("from"):
                    continue
                texto = (m.get("text") or {}).get("body") if m.get("type") == "text" else None
                salida.append(Entrante(m["id"], m["from"], texto.strip() if texto else None))
    return salida


def canal_de(numero: str) -> str:
    """Id estable y anónimo del número (``wa-`` + hash): conversación, perfil y vínculo con el código."""
    return "wa-" + hashlib.sha256(f"whatsapp:{numero}".encode()).hexdigest()[:32]


def codigo_en(texto: str) -> str | None:
    """El código de acceso si el mensaje lo trae («YELO-7K3M-Q9TD», con o sin guiones)."""
    encontrado = _CODIGO.search(texto)
    return encontrado.group(0) if encontrado else None


def para_whatsapp(respuesta: str, fuentes: list[str]) -> str:
    """Markdown del agente → texto de WhatsApp, con hasta dos fuentes al final y dentro del límite."""
    texto = _TITULO.sub("", _NEGRITA.sub(r"*\1*", respuesta)).strip()
    if fuentes:
        texto += "\n\nFuente: " + "\n".join(fuentes[:MAX_FUENTES])
    return texto if len(texto) <= MAX_TEXTO else texto[: MAX_TEXTO - 1] + "…"


class ClienteGraph:
    """Envía mensajes por la Graph API de Meta (``POST /{phone_number_id}/messages``)."""

    def __init__(
        self, token: str, phone_number_id: str, version: str, http: httpx.Client | None = None
    ) -> None:
        """Guarda las credenciales (vienen del ``.env``; nunca se registran en logs)."""
        self.url = f"https://graph.facebook.com/{version}/{phone_number_id}/messages"
        self.token = token
        self.http = http or httpx.Client(timeout=15)

    def enviar(self, para: str, texto: str) -> None:
        """Mensaje de texto a un número; lanza ``httpx.HTTPStatusError`` si Meta lo rechaza."""
        respuesta = self.http.post(
            self.url,
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": para,
                "type": "text",
                "text": {"preview_url": False, "body": texto},
            },
        )
        respuesta.raise_for_status()
