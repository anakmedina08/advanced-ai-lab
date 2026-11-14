import { API_URL } from "../api/client";
import type { EstadoSalud } from "../chat/salud";

const NOMBRES: Record<string, string> = {
  corpus: "Corpus Gold (chunks)",
  recomendador: "Datos sintéticos (CSV)",
  indice_qdrant: "Índice Qdrant (RAG)",
  memoria: "Memoria (SQLite: checkpointer y Store)",
  vision_instalada: "Extra de visión (ultralytics)",
  modelo_yolo: "Modelo YOLO cargado",
};

interface Props {
  estado: EstadoSalud;
  onReintentar: () => void;
}

/** Estado del backend: `GET /health` con cada componente y su indicador. */
export default function Estado({ estado, onReintentar }: Props) {
  return (
    <section>
      <h1>Estado del servicio</h1>
      <p className="suave">
        API: <code>{API_URL}</code> · documentación en{" "}
        <a href={`${API_URL}/docs`} target="_blank" rel="noreferrer">
          /docs
        </a>
      </p>
      {estado.fase === "cargando" && <p role="status">Consultando /health…</p>}
      {estado.fase === "caida" && (
        <div className="error" role="alert">
          <p>{estado.detalle}</p>
          <button type="button" onClick={onReintentar}>
            Reintentar
          </button>
        </div>
      )}
      {estado.fase === "ok" && (
        <div className="tarjeta">
          <p>
            <span className={`insignia ${estado.datos.status === "ok" ? "ruta-datos" : "ruta-mixto"}`}>
              {estado.datos.status === "ok" ? "Operativo" : "Degradado"}
            </span>{" "}
            versión {estado.datos.version} · LLM: {estado.datos.llm}
          </p>
          <ul className="componentes">
            {Object.entries(estado.datos.componentes).map(([clave, listo]) => (
              <li key={clave}>
                <span className={`luz ${listo ? "verde" : "roja"}`} aria-hidden />
                {NOMBRES[clave] ?? clave}: <strong>{listo ? "listo" : "no disponible"}</strong>
              </li>
            ))}
          </ul>
          <button type="button" onClick={onReintentar}>
            Actualizar
          </button>
        </div>
      )}
    </section>
  );
}
