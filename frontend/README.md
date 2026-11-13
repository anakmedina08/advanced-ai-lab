# Frontend · Asistente de seguros (React + Vite + TypeScript)

Cliente web **desacoplado** de la API FastAPI: no llama a ningún modelo, solo a la API por HTTP
y Server-Sent Events. Así la frontera frontend/backend se ve en la pestaña *Network*.

| Comando | Qué hace |
|---|---|
| `make api` (raíz) | backend en `http://127.0.0.1:8000` (`/docs`) |
| `make frontend` (raíz) | instala y abre `http://localhost:5173` |
| `npm run build` | tipos (`tsc`) + build de producción en `dist/` |

Variables: `VITE_API_URL` (por defecto `http://127.0.0.1:8000`). La API debe permitir el origen
del frontend en `FRONTEND_ORIGINS` (por defecto incluye `http://localhost:5173`).

Rutas: `/` chat con el agente, `/foto` foto → «¿qué hago?», `/estado` salud del servicio.
Specs: `openspec/specs/022-frontend-base` a `031-ci-frontend`.
