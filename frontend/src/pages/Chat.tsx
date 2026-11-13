import { useCallback, useEffect, useReducer, useRef, useState } from "react";

import { ApiError, streamAgente } from "../api/client";
import { inicial, reducir, sinUltimoIntento } from "../chat/estado";
import Burbuja from "../components/Burbuja";
import PanelDecision from "../components/PanelDecision";

const SUGERENCIAS = [
  "¿Qué cubre el SOAT?",
  "¿Cuántas pólizas se vendieron en el tercer trimestre de 2025?",
  "¿Qué cubre el seguro de hogar y cuántas pólizas de hogar se vendieron en 2025?",
  "¿Cuál es el WhatsApp de atención?",
];

interface Props {
  conversacionId: string;
  usuarioId: string | null;
  /** Se llama con el primer mensaje del hilo (para titularlo en la lista de hilos). */
  onPrimerMensaje?: (texto: string) => void;
  /** Historial inicial del hilo (al abrir uno existente). */
  historial?: { rol: "usuario" | "asistente"; texto: string }[];
  /** Se llama al terminar cada turno (p. ej., para refrescar la memoria de largo plazo). */
  onTurno?: () => void;
  /** Proveedor del LLM elegido en el encabezado (si falta, el de la API). */
  proveedor?: string;
}

/** Chat con el agente: la respuesta llega por SSE y se ve crecer mientras se genera. */
export default function Chat({ conversacionId, usuarioId, onPrimerMensaje, historial, onTurno, proveedor }: Props) {
  const [estado, despachar] = useReducer(reducir, inicial);
  const [borrador, setBorrador] = useState("");
  const control = useRef<AbortController | null>(null);
  const fin = useRef<HTMLDivElement>(null);
  const ocupado = estado.fase === "enviando" || estado.fase === "transmitiendo";

  useEffect(() => {
    despachar(historial ? { tipo: "cargar", mensajes: historial } : { tipo: "reiniciar" });
    return () => control.current?.abort();
  }, [conversacionId, historial]);

  useEffect(() => {
    fin.current?.scrollIntoView?.({ behavior: "smooth", block: "end" });
  }, [estado.mensajes]);

  const enviar = useCallback(
    async (texto: string) => {
      const limpio = texto.trim();
      if (!limpio || ocupado) return;
      if (estado.mensajes.length === 0) onPrimerMensaje?.(limpio);
      setBorrador("");
      despachar({ tipo: "enviar", texto: limpio, id: crypto.randomUUID() });
      control.current = new AbortController();
      try {
        const entrada = { mensaje: limpio, conversacion_id: conversacionId, usuario_id: usuarioId, proveedor };
        for await (const evento of streamAgente(entrada, control.current.signal)) {
          despachar({ tipo: "evento", evento });
          if (evento.tipo === "final") onTurno?.();
        }
      } catch (e) {
        if (e instanceof ApiError && e.codigo === "cancelado") return;
        const error = e instanceof ApiError ? e : new ApiError(0, "desconocido", String(e));
        despachar({ tipo: "fallo", detalle: error.detalle, requestId: error.requestId });
      } finally {
        control.current = null;
      }
    },
    [conversacionId, usuarioId, proveedor, ocupado, estado.mensajes.length, onPrimerMensaje, onTurno],
  );

  const detener = () => {
    control.current?.abort();
    despachar({ tipo: "detener" });
  };

  const reintentar = () => {
    const pregunta = estado.ultimaPregunta;
    if (!pregunta) return;
    despachar({ tipo: "cargar", mensajes: sinUltimoIntento(estado).mensajes });
    void enviar(pregunta);
  };

  return (
    <section className="chat" aria-label="Chat con el asistente">
      <div className="mensajes" aria-live="polite">
        {estado.mensajes.length === 0 && (
          <div className="vacio">
            <h1>¿En qué le puedo ayudar?</h1>
            <p>Respondo con información pública y cito la página de donde sale cada dato.</p>
            <div className="sugerencias">
              {SUGERENCIAS.map((s) => (
                <button key={s} type="button" onClick={() => void enviar(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {estado.mensajes.map((m, i) => {
          const ultimo = i === estado.mensajes.length - 1;
          return (
            <Burbuja
              key={m.id}
              mensaje={m}
              transmitiendo={ultimo && ocupado}
              onReintentar={ultimo && m.error ? reintentar : undefined}
            >
              {m.decision && <PanelDecision decision={m.decision} turno={m.turno} toolsEnCurso={m.toolsUsadas} />}
            </Burbuja>
          );
        })}
        <div ref={fin} />
      </div>
      <form
        className="entrada"
        onSubmit={(e) => {
          e.preventDefault();
          void enviar(borrador);
        }}
      >
        <label htmlFor="mensaje" className="oculto">
          Mensaje
        </label>
        <textarea
          id="mensaje"
          rows={2}
          maxLength={800}
          placeholder="Escriba su pregunta (sin datos personales: cédula, correo o teléfono)"
          value={borrador}
          onChange={(e) => setBorrador(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void enviar(borrador);
            }
          }}
        />
        {ocupado ? (
          <button type="button" onClick={detener}>
            Detener
          </button>
        ) : (
          <button type="submit" className="primario" disabled={!borrador.trim()}>
            Enviar
          </button>
        )}
      </form>
    </section>
  );
}
