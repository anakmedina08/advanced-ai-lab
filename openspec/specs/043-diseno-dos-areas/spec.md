# SPEC-043 · Diseño de la aplicación anterior en React: barra lateral y tres áreas

> Curso: Técnicas M2 (3.1) · Gestión M3 · Story points: **5** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
El frontend React cambió el diseño que el equipo ya tenía en Streamlit (tema claro azul marino, barra lateral oscura con logo y todo en una misma pantalla); el equipo prefiere conservarlo.

## Historia
**Como** integrante del equipo, **quiero** ver la aplicación React con el mismo diseño y la misma organización de antes, **para** mostrar en una sola pantalla la atención al cliente, el panel del equipo y la sustentación.

## Requisitos
- **R043.1** El tema DEBE ser el de `.streamlit/config.toml`: claro, azul `#1F4E8C`, fondos `#F3F5F9`, bordes `#DCE2EA`, texto `#1E293B`, fuente Inter y barra lateral `#0F2742`.
- **R043.2** La barra lateral DEBE mostrar el logo y tres secciones con íconos: Atención al cliente (Asistente, Foto: ¿qué hago?, Guías de seguros), Panel del equipo (Configuración, Pipeline de datos, Evaluación, Experimentos) y Sustentación (Entregables por curso), además del aviso académico.
- **R043.3** Cada página DEBE tener su título con ícono, como en Streamlit; «Asistente» es la página por defecto.
- **R043.4** La Configuración DEBE contener el proveedor del modelo (antes en el encabezado) y el estado del sistema (`/health`).
- **R043.5** En pantallas pequeñas la barra lateral DEBE plegarse tras un botón.

## Criterios de aceptación
- **AC1** · **Dado** la aplicación abierta, **cuando** se mira la barra lateral, **entonces** aparecen las tres secciones con sus páginas.
- **AC2** · **Dado** la página Configuración, **cuando** se elige Claude, **entonces** el chat envía `proveedor: anthropic`.

## Fuera de alcance
Cambiar el diseño de Streamlit.

## Métricas de éxito
Las mismas secciones y colores que la versión Streamlit.
