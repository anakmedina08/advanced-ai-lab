import { NavLink } from "react-router-dom";

import { SECCIONES } from "../navegacion";
import Icono from "./Icono";

/** Barra lateral oscura con el logo, las tres áreas y el aviso académico (como en Streamlit). */
export default function BarraLateral({ onNavegar }: { onNavegar?: () => void }) {
  return (
    <div className="barra-contenido">
      <img src="/logo.svg" alt="Asistente de seguros" className="logo" width={220} height={39} />
      <nav aria-label="Navegación principal">
        {SECCIONES.map((seccion) => (
          <div key={seccion.nombre} className="seccion">
            <p className="seccion-titulo">{seccion.nombre}</p>
            <ul>
              {seccion.paginas.map((p) => (
                <li key={p.ruta}>
                  <NavLink to={p.ruta} end={p.ruta === "/"} onClick={onNavegar}>
                    <Icono nombre={p.icono} />
                    <span>{p.titulo}</span>
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>
      <p className="aviso-academico">
        <Icono nombre="school" /> Proyecto académico (UAO) con información pública. No es un canal oficial de la
        compañía.
      </p>
    </div>
  );
}
