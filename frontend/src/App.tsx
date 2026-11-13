import { useState } from "react";
import { Route, Routes, useLocation } from "react-router-dom";

import { useProveedor } from "./chat/proveedor";
import { useSalud } from "./chat/salud";
import AvisoConexion from "./components/AvisoConexion";
import BarraLateral from "./components/BarraLateral";
import Icono from "./components/Icono";
import { paginaDe } from "./navegacion";
import Configuracion from "./pages/Configuracion";
import Foto from "./pages/Foto";
import Inicio from "./pages/Inicio";
import Pendiente from "./pages/Pendiente";

/** Layout de la versión Streamlit: barra lateral oscura con tres áreas y el contenido a la derecha. */
export default function App() {
  const { estado, reintentar } = useSalud();
  const [proveedor, setProveedor] = useProveedor();
  const [menuAbierto, setMenuAbierto] = useState(false);
  const pagina = paginaDe(useLocation().pathname);
  const reintentarSalud = () => void reintentar();
  const configuracion = (
    <Configuracion proveedor={proveedor} onProveedor={setProveedor} salud={estado} onReintentar={reintentarSalud} />
  );

  return (
    <div className={`app ${menuAbierto ? "menu-abierto" : ""}`}>
      <aside className="barra-lateral" id="barra-lateral">
        <BarraLateral onNavegar={() => setMenuAbierto(false)} />
      </aside>
      <div className="area-principal">
        <button
          type="button"
          className="boton-barra"
          aria-expanded={menuAbierto}
          aria-controls="barra-lateral"
          onClick={() => setMenuAbierto((v) => !v)}
        >
          <Icono nombre="menu" /> Menú
        </button>
        <AvisoConexion estado={estado} onReintentar={reintentarSalud} />
        <main className="contenido">
          {pagina && (
            <h1 className="titulo-pagina">
              <Icono nombre={pagina.icono} /> {pagina.titulo}
            </h1>
          )}
          <Routes>
            <Route path="/" element={<Inicio proveedor={proveedor} />} />
            <Route path="/foto" element={<Foto />} />
            <Route path="/configuracion" element={configuracion} />
            <Route path="/estado" element={configuracion} />
            <Route path="/guias" element={<Pendiente />} />
            <Route path="/pipeline" element={<Pendiente />} />
            <Route path="/evaluacion" element={<Pendiente />} />
            <Route path="/experimentos" element={<Pendiente />} />
            <Route path="/sustentacion" element={<Pendiente />} />
            <Route path="*" element={<p>Página no encontrada.</p>} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
