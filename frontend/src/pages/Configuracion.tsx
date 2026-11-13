import { PROVEEDORES } from "../chat/proveedor";
import type { EstadoSalud } from "../chat/salud";
import Icono from "../components/Icono";
import Estado from "./Estado";

interface Props {
  proveedor: string;
  onProveedor: (id: string) => void;
  salud: EstadoSalud;
  onReintentar: () => void;
}

const AYUDA: Record<string, string> = {
  anthropic: "Claude: el modelo evaluado (v3 cita la fuente en el 100 % de las respuestas).",
  ollama: "Modelo local en CPU: gratis y privado, pero más lento y menos preciso con las tools.",
  deepseek: "Alternativa en la nube, económica.",
};

/** Configuración (panel del equipo): proveedor del modelo y estado del sistema. */
export default function Configuracion({ proveedor, onProveedor, salud, onReintentar }: Props) {
  return (
    <div className="pila">
      <p className="leyenda">Ajustes técnicos de esta sesión. El área de atención al cliente los usa sin mostrarlos.</p>
      <section className="tarjeta">
        <h2>
          <Icono nombre="psychology" /> Modelo
        </h2>
        <div className="segmentado" role="radiogroup" aria-label="Proveedor del modelo">
          {PROVEEDORES.map((p) => (
            <button
              key={p.id}
              type="button"
              role="radio"
              aria-checked={proveedor === p.id}
              className={proveedor === p.id ? "activo" : undefined}
              onClick={() => onProveedor(p.id)}
            >
              {p.nombre}
            </button>
          ))}
        </div>
        <p className="leyenda">{AYUDA[proveedor] ?? ""}</p>
      </section>
      <section className="tarjeta">
        <h2>
          <Icono nombre="monitor_heart" /> Estado del sistema
        </h2>
        <Estado estado={salud} onReintentar={onReintentar} />
      </section>
    </div>
  );
}
