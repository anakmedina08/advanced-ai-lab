# Plan · SPEC-022 · Frontend propio con React, Vite y TypeScript

## Diseño
SPA con Vite; `src/main.tsx` monta `BrowserRouter`; `src/App.tsx` define el layout y las rutas; CSS propio con variables (tema claro/oscuro).

## Decisiones
- React + Vite: arranque rápido y el ecosistema más conocido por el equipo.
- Sin librerías de componentes pesadas: CSS propio con variables.

## Contrato
Variable `VITE_API_URL`; rutas `/`, `/foto`, `/estado`.

## Riesgos
- Node no es parte de `uv`: se documenta la versión (Node 20+) y se usa `npm ci` con lockfile.

## Alternativas descartadas
- Next.js: SSR innecesario para una SPA contra una API existente.
- Seguir con Streamlit: no se acepta.

## Estrategia de pruebas
`npm run build` (tsc + vite) en la CI (historia 031). Pruebas AAA sin red ni API de pago.
