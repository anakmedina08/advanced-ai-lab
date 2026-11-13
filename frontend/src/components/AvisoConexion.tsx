import type { EstadoSalud } from "../chat/salud";

interface Props {
  estado: EstadoSalud;
  onReintentar: () => void;
}

/** Aviso global y persistente cuando la API no responde. */
export default function AvisoConexion({ estado, onReintentar }: Props) {
  if (estado.fase !== "caida") return null;
  return (
    <div className="aviso-conexion" role="alert">
      <span>
        <strong>No hay conexión con la API.</strong> {estado.detalle}
      </span>
      <button type="button" onClick={onReintentar}>
        Reintentar
      </button>
    </div>
  );
}
