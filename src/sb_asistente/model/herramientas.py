"""Doce tools adicionales del asistente (SPEC-079, anuncio 551462-007).

Completan las 20 tools de la rúbrica (ítem 1.1). Casi todas envuelven lógica que ya existe en el
repo; las dependencias entran por constructor (sesión HTTP, LLM, reloj) para probarlas **sin red ni
API**:

- **Estáticas** (sin red): ``listar_productos`` (catálogo sintético), ``explicar_termino``
  (glosario propio) y ``checklist_siniestro`` (pasos genéricos de un siniestro).
- **De conocimiento con fuente** (RAG): ``citar_fuente`` y ``guia_tramite`` devuelven pasajes del
  corpus Gold con su URL (regla de citación).
- **De estado**: ``guardar_perfil``, ``ver_perfil`` y ``olvidar_datos`` toman el ``usuario_id`` del
  ``runtime.context`` (nunca del modelo) y ``estado_codigo_acceso`` consulta ``CodigosAcceso``.
- **De medios** (visión y OCR, opcionales): ``analizar_foto`` y ``leer_documento`` reciben el
  contenido en base64 y delegan en un callable inyectado.
- **HITL**: ``escalar_a_humano`` entrega el canal oficial (PQR) con el resumen del caso.
"""

import base64
import json
import unicodedata
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from typing import Literal

from langchain_core.tools import BaseTool, tool
from langgraph.prebuilt.tool_node import ToolRuntime
from pydantic import BaseModel, Field

from sb_asistente.model.acceso import CodigosAcceso
from sb_asistente.model.memoria import PerfilStore
from sb_asistente.model.rag.blindaje import formatear_pasajes
from sb_asistente.model.rag.hibrido import RecuperadorHibrido
from sb_asistente.model.recomendador.catalogo import CATALOGO, Producto

# --------------------------------------------------------------------------- contenido estático

GLOSARIO: dict[str, str] = {
    "prima": "Lo que pagas por tu seguro (mensual o anual) para tener la cobertura activa.",
    "deducible": "La parte que tú asumes de un siniestro antes de que la aseguradora pague el resto.",
    "cobertura": "Lo que el seguro sí te protege o reembolsa, con sus límites y exclusiones.",
    "siniestro": "El hecho cubierto por la póliza: un accidente, un robo, un daño en el hogar.",
    "beneficiario": "La persona que recibe la indemnización o la suma asegurada cuando corresponde.",
    "poliza": "El contrato del seguro: dice quién está cubierto, qué, hasta cuánto y por cuánto.",
    "soat": "Seguro Obligatorio de Accidentes de Tránsito: cubre lesiones de personas, no el vehículo.",
    "exclusion": "Lo que la póliza NO cubre; conviene leerlo antes de contratar.",
    "vigencia": "El periodo durante el cual la póliza está activa.",
}

CHECKLISTS: dict[str, list[str]] = {
    "auto": [
        "Verifica que nadie esté herido y llama a la línea de emergencias si hace falta.",
        "No muevas el vehículo si no es necesario y toma fotos de la escena y los daños.",
        "Anota los datos del otro conductor y del vehículo (placa, SOAT).",
        "Reporta el siniestro a la aseguradora lo antes posible por su canal oficial.",
        "Guarda los documentos que te pidan y el número del caso.",
    ],
    "hogar": [
        "Corta el riesgo si es seguro (llave del agua, del gas, del suministro eléctrico).",
        "Toma fotos o video de los daños antes de limpiar o reparar.",
        "Haz un inventario de lo afectado con sus valores aproximados.",
        "Reporta el siniestro a la aseguradora por su canal oficial.",
        "No botes los objetos dañados hasta que te lo indiquen.",
    ],
    "salud": [
        "Acude a la red de prestadores autorizada por tu plan o póliza.",
        "Lleva tu documento de identidad y el carné o número de póliza.",
        "Si es una urgencia, usa la línea de urgencias del plan.",
        "Guarda las órdenes, fórmulas y soportes de pago para el reembolso.",
        "Verifica qué procedimientos requieren autorización previa.",
    ],
    "general": [
        "Identifica qué pasó y qué cubre tu póliza (lee coberturas y exclusiones).",
        "Reúne los documentos del caso y toma evidencia (fotos, recibos).",
        "Reporta por el canal oficial de la aseguradora y guarda el número del caso.",
        "Sigue las indicaciones del asesor para no perder cobertura.",
    ],
}

LINEAS = Literal["movilidad", "hogar", "salud", "vida", "mascota", "general"]
TIPOS_SINIESTRO = Literal["auto", "hogar", "salud", "general"]


class GuardarPerfil(BaseModel):
    """Hechos a guardar en el perfil del usuario actual (el usuario lo pone el runtime)."""

    hechos: dict[str, str] = Field(description="Hechos a recordar (aseguradora, vivienda, etc.).")


class ConsultarFuente(BaseModel):
    """Consulta de la que se quieren las fuentes."""

    consulta: str = Field(description="Qué buscar para devolver sus páginas de origen.")


class ContenidoBase64(BaseModel):
    """Contenido binario (foto o documento) codificado en base64."""

    contenido_base64: str = Field(description="Archivo codificado en base64.")


def _json(objeto: object) -> str:
    return json.dumps(objeto, ensure_ascii=False, default=str)


def _ahora() -> datetime:
    return datetime.now(UTC)


def _plano(texto: str) -> str:
    """Minúsculas sin tildes (para que «póliza» y «poliza» coincidan)."""
    return unicodedata.normalize("NFKD", texto.strip().lower()).encode("ascii", "ignore").decode()


def _usuario(runtime: ToolRuntime) -> str | None:
    """El usuario del turno desde ``runtime.context`` (nunca desde el modelo)."""
    contexto = getattr(runtime, "context", None)
    return getattr(contexto, "usuario_id", None)


# -------------------------------------------------------------------------------------- fábrica


def crear_tools_extra(
    *,
    catalogo: Iterable[Producto] = CATALOGO,
    perfil: PerfilStore | None = None,
    acceso: CodigosAcceso | None = None,
    recuperador: RecuperadorHibrido | None = None,
    escalar: Callable[[str, str], dict] | None = None,
    analizar_foto_fn: Callable[[bytes], object] | None = None,
    leer_documento_fn: Callable[[bytes], dict] | None = None,
    reloj: Callable[[], datetime] = _ahora,
) -> list[BaseTool]:
    """Devuelve las 12 tools adicionales con sus dependencias inyectadas (dobles en pruebas)."""
    productos = list(catalogo)

    @tool
    def listar_productos(linea: LINEAS | None = None) -> str:
        """Lista los productos de seguros para personas (catálogo sintético de práctica).

        Args:
            linea: Opcional, filtra por línea (movilidad, hogar, salud, vida, mascota, general).

        """
        filtrados = [p for p in productos if linea is None or p.linea == linea]
        return _json(
            [
                {
                    "producto": p.nombre,
                    "linea": p.linea,
                    "descripcion": p.descripcion,
                }
                for p in filtrados
            ]
        )

    @tool(args_schema=ConsultarFuente)
    def citar_fuente(consulta: str) -> str:
        """Devuelve las páginas de origen (URL y título) de la base pública para una consulta.

        Args:
            consulta: Qué buscar para devolver sus fuentes.

        """
        if recuperador is None:
            return "No hay recuperador disponible."
        fragmentos = recuperador.buscar(consulta)
        if not fragmentos:
            return "Sin resultados en la base pública para esa consulta."
        return _json([{"titulo": f.titulo, "url": f.url} for f in fragmentos])

    @tool
    def explicar_termino(termino: str) -> str:
        """Explica un término de seguros en lenguaje sencillo.

        Args:
            termino: La palabra a explicar (prima, deducible, cobertura, siniestro, póliza, soat…).

        """
        clave = _plano(termino)
        if clave in GLOSARIO:
            return GLOSARIO[clave]
        if recuperador is not None:
            fragmentos = recuperador.buscar(f"qué es {termino} seguros")
            if fragmentos:
                bloque, _ = formatear_pasajes(fragmentos)
                return bloque
        return (
            f"No tengo una definición propia de «{termino}»; "
            "pregúntame por prima, deducible, cobertura o siniestro."
        )

    @tool
    def guia_tramite(tramite: str) -> str:
        """Da los pasos para un trámite (reclamar, contactar, cambiar datos) con su fuente.

        Args:
            tramite: El trámite o gestión que la persona quiere hacer.

        """
        if recuperador is None:
            return "No hay recuperador disponible."
        fragmentos = recuperador.buscar(tramite)
        if not fragmentos:
            return "Sin resultados en la base pública para ese trámite."
        bloque, _ = formatear_pasajes(fragmentos)
        return bloque

    @tool
    def checklist_siniestro(tipo: TIPOS_SINIESTRO = "general") -> str:
        """Entrega una lista de pasos para atender un siniestro.

        Args:
            tipo: auto, hogar, salud o general (por defecto).

        """
        pasos = CHECKLISTS.get(tipo, CHECKLISTS["general"])
        return "\n".join(f"{i}. {paso}" for i, paso in enumerate(pasos, 1))

    @tool(args_schema=GuardarPerfil)
    def guardar_perfil(runtime: ToolRuntime, hechos: dict[str, str]) -> str:  # noqa: D417 - runtime inyectado
        """Guarda hechos en el perfil del usuario del turno (sin datos personales en claro).

        Args:
            hechos: Hechos a recordar (la aseguradora, el tipo de vivienda, etc.).

        """
        usuario_id = _usuario(runtime)
        if not usuario_id:
            return "No hay usuario identificado en este turno."
        if perfil is None:
            return "No hay almacén de perfil disponible."
        perfil.guardar(usuario_id, hechos)
        return _json({"guardado": sorted(hechos)})

    @tool
    def ver_perfil(runtime: ToolRuntime) -> str:
        """Devuelve el perfil guardado del usuario del turno."""
        usuario_id = _usuario(runtime)
        if not usuario_id:
            return "No hay usuario identificado en este turno."
        if perfil is None:
            return "No hay almacén de perfil disponible."
        return _json(perfil.leer(usuario_id))

    @tool
    def olvidar_datos(runtime: ToolRuntime) -> str:
        """Borra el perfil del usuario del turno (derecho a la supresión)."""
        usuario_id = _usuario(runtime)
        if not usuario_id:
            return "No hay usuario identificado en este turno."
        if perfil is None:
            return "No hay almacén de perfil disponible."
        return _json({"borrados": perfil.borrar(usuario_id)})

    @tool
    def estado_codigo_acceso(codigo: str) -> str:
        """Consulta el estado de un código de acceso (vigente, cupo y vencimiento).

        Args:
            codigo: El código de acceso a revisar.

        """
        if acceso is None:
            return "No hay registro de códigos de acceso disponible."
        estado = acceso.estado(codigo)
        if estado is None:
            return "Código no encontrado o inválido."
        return _json(
            {
                "vigente": estado.vigente(reloj()),
                "expira": estado.expira.isoformat(),
                "restantes": estado.restantes,
                "revocado": estado.revocado,
            }
        )

    @tool
    def escalar_a_humano(aseguradora: str, motivo: str) -> str:
        """Escala a un humano: entrega el canal oficial (PQR) con el resumen del caso.

        Args:
            aseguradora: La aseguradora de la persona.
            motivo: Un resumen breve del caso a escalar.

        """
        if escalar is None:
            return "No hay canales de escalamiento disponibles."
        return _json(escalar(aseguradora, motivo))

    @tool(args_schema=ContenidoBase64)
    def analizar_foto(contenido_base64: str) -> str:
        """Analiza una foto (accidente, daño, robo o bien a asegurar) y sugiere qué hacer o qué seguro aplica.

        Args:
            contenido_base64: La foto codificada en base64.

        """
        if analizar_foto_fn is None:
            return "El análisis de fotos no está disponible en este entorno."
        try:
            datos = base64.b64decode(contenido_base64)
        except ValueError:
            return "La foto no es un base64 válido."
        return _json(analizar_foto_fn(datos))

    @tool(args_schema=ContenidoBase64)
    def leer_documento(contenido_base64: str) -> str:
        """Lee un documento (recibo, carátula) para identificar la aseguradora, sin exponer su texto.

        Args:
            contenido_base64: El documento codificado en base64.

        """
        if leer_documento_fn is None:
            return "La lectura de documentos no está disponible en este entorno."
        try:
            datos = base64.b64decode(contenido_base64)
        except ValueError:
            return "El documento no es un base64 válido."
        return _json(leer_documento_fn(datos))

    # Solo se devuelven las tools cuyas dependencias están presentes: una tool sin su dependencia
    # respondería siempre «no disponible» y no aporta (el agente y el MCP filtran las que no aplican).
    herramientas: list[BaseTool] = [
        listar_productos,
        checklist_siniestro,
        explicar_termino,  # el glosario siempre está; sin recuperador no hay respaldo RAG
    ]
    if recuperador is not None:
        herramientas += [citar_fuente, guia_tramite]
    if perfil is not None:
        herramientas += [guardar_perfil, ver_perfil, olvidar_datos]
    if acceso is not None:
        herramientas += [estado_codigo_acceso]
    if escalar is not None:
        herramientas += [escalar_a_humano]
    if analizar_foto_fn is not None:
        herramientas += [analizar_foto]
    if leer_documento_fn is not None:
        herramientas += [leer_documento]
    return herramientas
