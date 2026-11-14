import { NavLink, Route, Routes } from "react-router-dom";

import Estado from "./pages/Estado";
import Foto from "./pages/Foto";
import Inicio from "./pages/Inicio";

/** Layout común: encabezado con navegación, aviso de proyecto académico y la página activa. */
export default function App() {
  return (
    <div className="app">
      <header className="encabezado">
        <div className="marca">
          <img src="/icono.svg" alt="" width={28} height={28} />
          <div>
            <strong>Asistente de seguros</strong>
            <span className="sub">Información pública · proyecto académico UAO</span>
          </div>
        </div>
        <nav aria-label="Secciones">
          <NavLink to="/" end>
            Chat
          </NavLink>
          <NavLink to="/foto">Foto: ¿qué hago?</NavLink>
          <NavLink to="/estado">Estado</NavLink>
        </nav>
      </header>
      <p className="aviso" role="note">
        No es un canal oficial de la compañía. Las respuestas salen de información pública y citan su fuente.
      </p>
      <main className="contenido">
        <Routes>
          <Route path="/" element={<Inicio />} />
          <Route path="/foto" element={<Foto />} />
          <Route path="/estado" element={<Estado />} />
          <Route path="*" element={<p>Página no encontrada.</p>} />
        </Routes>
      </main>
    </div>
  );
}
