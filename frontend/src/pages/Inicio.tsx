import { useCallback, useEffect, useState } from "react";

import { ApiError, borrarConversacion, historial } from "../api/client";
import type { MensajeHistorial } from "../api/types";
import { useSesiones } from "../chat/sesiones";
import BarraHilos from "../components/BarraHilos";
import PanelPerfil from "../components/PanelPerfil";
import Chat from "./Chat";

/** Página principal: lista de hilos, chat del hilo activo y memoria de largo plazo. */
export default function Inicio() {
  const { usuarioId, hilos, activo, elegir, nuevo, titular, quitar } = useSesiones();
  const [mensajes, setMensajes] = useState<MensajeHistorial[] | undefined>(undefined);
  const [aviso, setAviso] = useState<string | null>(null);
  const [version, setVersion] = useState(0);
  const [menuAbierto, setMenuAbierto] = useState(false);

  // Al abrir un hilo guardado se recupera su historial desde la API (sobrevive al reinicio).
  useEffect(() => {
    let vigente = true;
    setAviso(null);
    setMensajes(undefined);
    if (!hilos.some((h) => h.id === activo)) {
      setMensajes(undefined);
      return;
    }
    historial(activo)
      .then((r) => vigente && setMensajes(r.mensajes))
      .catch((e) => vigente && setAviso(e instanceof ApiError ? e.detalle : String(e)));
    return () => {
      vigente = false;
    };
  }, [activo]); // solo al cambiar de hilo

  const borrar = useCallback(
    async (id: string) => {
      try {
        await borrarConversacion(id);
      } catch {
        // si la API no responde, igual se quita de la lista local
      }
      quitar(id);
    },
    [quitar],
  );

  const alElegir = (id: string) => {
    elegir(id);
    setMenuAbierto(false);
  };

  return (
    <div className={`conversaciones ${menuAbierto ? "menu-abierto" : ""}`}>
      <button
        type="button"
        className="boton-menu"
        aria-expanded={menuAbierto}
        aria-controls="lateral"
        onClick={() => setMenuAbierto((v) => !v)}
      >
        ☰ Conversaciones
      </button>
      <aside id="lateral" className="lateral">
        <BarraHilos
          hilos={hilos}
          activo={activo}
          onElegir={alElegir}
          onNuevo={() => {
            nuevo();
            setMenuAbierto(false);
          }}
          onBorrar={(id) => void borrar(id)}
        />
        <PanelPerfil usuarioId={usuarioId} version={version} />
      </aside>
      <div className="principal">
        {aviso && (
          <p className="error" role="alert">
            No se pudo recuperar el historial: {aviso}
          </p>
        )}
        <Chat
          key={activo}
          conversacionId={activo}
          usuarioId={usuarioId}
          historial={mensajes}
          onPrimerMensaje={titular}
          onTurno={() => setVersion((v) => v + 1)}
        />
      </div>
    </div>
  );
}
