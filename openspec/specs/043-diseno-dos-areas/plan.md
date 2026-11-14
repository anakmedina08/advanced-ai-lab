# Plan · SPEC-043 · Diseño de la aplicación anterior en React: barra lateral y tres áreas

## Diseño
`components/BarraLateral.tsx` con `NavLink`, `layout` en `App.tsx`, variables CSS del tema, `pages/Configuracion.tsx` (proveedor + estado). Páginas de las otras historias como rutas declaradas.

## Decisiones
- Mismo tema en claro para todos (como Streamlit `base = light`), sin depender del modo oscuro del sistema.
- Íconos con Material Symbols (como en Streamlit) servidos desde Google Fonts.

## Contrato
Rutas: `/`, `/foto`, `/guias`, `/configuracion`, `/pipeline`, `/evaluacion`, `/experimentos`, `/sustentacion`.

## Riesgos
- Fuente de íconos externa: sin red se ven los nombres; se agrega texto visible.

## Alternativas descartadas
- Seguir con el diseño nuevo: el equipo prefiere el anterior.

## Estrategia de pruebas
Testing Library: secciones de la barra y proveedor en Configuración. Pruebas AAA sin red ni API de pago.
