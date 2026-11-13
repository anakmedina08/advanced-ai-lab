import type { Hilo } from "../chat/sesiones";

interface Props {
  hilos: Hilo[];
  activo: string;
  onElegir: (id: string) => void;
  onNuevo: () => void;
  onBorrar: (id: string) => void;
}

/** Lista de conversaciones (hilos) con acciones de abrir, crear y borrar. */
export default function BarraHilos({ hilos, activo, onElegir, onNuevo, onBorrar }: Props) {
  return (
    <nav className="hilos" aria-label="Conversaciones">
      <button type="button" className="primario ancho" onClick={onNuevo}>
        + Nueva conversación
      </button>
      {hilos.length === 0 && <p className="suave">Aún no hay conversaciones guardadas.</p>}
      <ul>
        {hilos.map((h) => (
          <li key={h.id} className={h.id === activo ? "activo" : undefined}>
            <button type="button" className="hilo" onClick={() => onElegir(h.id)} aria-current={h.id === activo}>
              {h.titulo}
            </button>
            <button type="button" className="icono" aria-label={`Borrar «${h.titulo}»`} onClick={() => onBorrar(h.id)}>
              ×
            </button>
          </li>
        ))}
      </ul>
    </nav>
  );
}
