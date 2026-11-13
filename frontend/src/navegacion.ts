/** Estructura de la navegación: la misma de la versión Streamlit (tres áreas en la barra lateral). */

export interface Pagina {
  ruta: string;
  titulo: string;
  icono: string; // nombre de Material Symbols
}

export interface Seccion {
  nombre: string;
  paginas: Pagina[];
}

export const SECCIONES: Seccion[] = [
  {
    nombre: "Atención al cliente",
    paginas: [
      { ruta: "/", titulo: "Asistente", icono: "support_agent" },
      { ruta: "/foto", titulo: "Foto: ¿qué hago?", icono: "photo_camera" },
      { ruta: "/guias", titulo: "Guías de seguros", icono: "menu_book" },
    ],
  },
  {
    nombre: "Panel del equipo",
    paginas: [
      { ruta: "/configuracion", titulo: "Configuración", icono: "tune" },
      { ruta: "/pipeline", titulo: "Pipeline de datos", icono: "account_tree" },
      { ruta: "/evaluacion", titulo: "Evaluación", icono: "analytics" },
      { ruta: "/experimentos", titulo: "Experimentos (MLflow)", icono: "science" },
    ],
  },
  {
    nombre: "Sustentación",
    paginas: [{ ruta: "/sustentacion", titulo: "Entregables por curso", icono: "school" }],
  },
];

export const PAGINAS: Pagina[] = SECCIONES.flatMap((s) => s.paginas);

/** Página que corresponde a la ruta actual (para el título con ícono). */
export function paginaDe(ruta: string): Pagina | undefined {
  return PAGINAS.find((p) => p.ruta === ruta);
}
