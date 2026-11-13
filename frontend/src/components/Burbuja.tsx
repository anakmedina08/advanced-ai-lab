import Markdown from "react-markdown";

import type { Mensaje } from "../chat/estado";

interface Props {
  mensaje: Mensaje;
  transmitiendo: boolean;
  onReintentar?: () => void;
  children?: React.ReactNode;
}

/** Una burbuja del chat: texto en Markdown (sin HTML crudo), fuentes, paso actual y errores. */
export default function Burbuja({ mensaje, transmitiendo, onReintentar, children }: Props) {
  const fuentes = mensaje.turno?.salida.fuentes ?? [];
  return (
    <article className={`burbuja ${mensaje.rol}`} aria-busy={transmitiendo}>
      {mensaje.texto && (
        <div className="texto">
          {transmitiendo ? <p className="crudo">{mensaje.texto}</p> : <Markdown>{mensaje.texto}</Markdown>}
        </div>
      )}
      {mensaje.pasoActual && (
        <p className="paso" role="status">
          <span className="punto" aria-hidden /> {mensaje.pasoActual}
        </p>
      )}
      {fuentes.length > 0 && (
        <ul className="fuentes" aria-label="Fuentes">
          {fuentes.map((url) => (
            <li key={url}>
              <a href={url} target="_blank" rel="noreferrer">
                {url.replace(/^https?:\/\/(www\.)?/, "")}
              </a>
            </li>
          ))}
        </ul>
      )}
      {mensaje.error && (
        <div className="error" role="alert">
          <p>{mensaje.error.detalle}</p>
          {mensaje.error.requestId && <small>request id: {mensaje.error.requestId}</small>}
          {onReintentar && (
            <button type="button" onClick={onReintentar}>
              Reintentar
            </button>
          )}
        </div>
      )}
      {children}
    </article>
  );
}
