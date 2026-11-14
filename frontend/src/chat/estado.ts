/**
 * Estado del chat como máquina explícita (`useReducer`): cada evento del streaming es una acción.
 *
 * Estados de la conversación: `idle` → `enviando` → `transmitiendo` → `listo` | `error`.
 */

import type { AgenteOut, DecisionOut, EventoAgente, MensajeHistorial } from "../api/types";

export type Fase = "idle" | "enviando" | "transmitiendo" | "listo" | "error";

export interface Mensaje {
  id: string;
  rol: "usuario" | "asistente";
  texto: string;
  decision?: DecisionOut;
  turno?: AgenteOut;
  pasoActual?: string;
  toolsUsadas?: string[];
  error?: { detalle: string; requestId: string | null };
}

export interface EstadoChat {
  fase: Fase;
  mensajes: Mensaje[];
  ultimaPregunta: string | null;
}

export type Accion =
  | { tipo: "enviar"; texto: string; id: string }
  | { tipo: "evento"; evento: EventoAgente }
  | { tipo: "fallo"; detalle: string; requestId: string | null }
  | { tipo: "detener" }
  | { tipo: "cargar"; mensajes: MensajeHistorial[] }
  | { tipo: "reiniciar" };

export const inicial: EstadoChat = { fase: "idle", mensajes: [], ultimaPregunta: null };

const PASOS: Record<string, string> = {
  buscar_conocimiento: "Buscando en la base pública…",
  consultar_datos: "Consultando los datos…",
  recomendar_seguros: "Buscando seguros para su perfil…",
};

function actualizarUltimo(estado: EstadoChat, cambio: (m: Mensaje) => Mensaje): Mensaje[] {
  const mensajes = [...estado.mensajes];
  const i = mensajes.length - 1;
  if (i >= 0 && mensajes[i].rol === "asistente") mensajes[i] = cambio(mensajes[i]);
  return mensajes;
}

function aplicarEvento(estado: EstadoChat, e: EventoAgente): EstadoChat {
  switch (e.tipo) {
    case "router": {
      const { tipo: _tipo, ...decision } = e;
      return { ...estado, fase: "transmitiendo", mensajes: actualizarUltimo(estado, (m) => ({ ...m, decision })) };
    }
    case "tool_inicio":
      return {
        ...estado,
        mensajes: actualizarUltimo(estado, (m) => ({
          ...m,
          pasoActual: PASOS[e.tool] ?? `Usando ${e.tool}…`,
          toolsUsadas: [...(m.toolsUsadas ?? []), e.tool],
        })),
      };
    case "tool_fin":
      return { ...estado, mensajes: actualizarUltimo(estado, (m) => ({ ...m, pasoActual: "Redactando la respuesta…" })) };
    case "texto":
      return {
        ...estado,
        fase: "transmitiendo",
        mensajes: actualizarUltimo(estado, (m) => ({ ...m, texto: m.texto + e.delta, pasoActual: undefined })),
      };
    case "final":
      return {
        ...estado,
        fase: "listo",
        mensajes: actualizarUltimo(estado, (m) => ({
          ...m,
          texto: e.turno.salida.respuesta,
          turno: e.turno,
          decision: e.turno.decision,
          pasoActual: undefined,
        })),
      };
    case "error":
      return {
        ...estado,
        fase: "error",
        mensajes: actualizarUltimo(estado, (m) => ({ ...m, pasoActual: undefined, error: { detalle: e.detalle, requestId: null } })),
      };
  }
}

export function reducir(estado: EstadoChat, accion: Accion): EstadoChat {
  switch (accion.tipo) {
    case "enviar":
      return {
        fase: "enviando",
        ultimaPregunta: accion.texto,
        mensajes: [
          ...estado.mensajes,
          { id: `${accion.id}-u`, rol: "usuario", texto: accion.texto },
          { id: `${accion.id}-a`, rol: "asistente", texto: "", pasoActual: "Pensando…" },
        ],
      };
    case "evento":
      return aplicarEvento(estado, accion.evento);
    case "fallo":
      return {
        ...estado,
        fase: "error",
        mensajes: actualizarUltimo(estado, (m) => ({
          ...m,
          pasoActual: undefined,
          error: { detalle: accion.detalle, requestId: accion.requestId },
        })),
      };
    case "detener":
      return {
        ...estado,
        fase: "listo",
        mensajes: actualizarUltimo(estado, (m) => ({ ...m, pasoActual: undefined, texto: m.texto || "(Respuesta detenida)" })),
      };
    case "cargar":
      return {
        fase: "idle",
        ultimaPregunta: null,
        mensajes: accion.mensajes.map((m, i) => ({ id: `h-${i}`, rol: m.rol, texto: m.texto })),
      };
    case "reiniciar":
      return inicial;
  }
}

/** Quita el último par pregunta/respuesta fallido para reintentar la misma pregunta. */
export function sinUltimoIntento(estado: EstadoChat): EstadoChat {
  return { ...estado, fase: "idle", mensajes: estado.mensajes.slice(0, -2) };
}
