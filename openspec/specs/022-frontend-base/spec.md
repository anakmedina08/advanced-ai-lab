# SPEC-022 · Frontend propio con React, Vite y TypeScript

> Curso: Técnicas M2 (3.1) · Gestión M3 (Demo E2E) · Story points: **3** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
La interfaz es Streamlit, que mezcla UI y lógica en el mismo proceso; ambos cursos la prohíben desde este módulo y exigen un cliente desacoplado que hable con la API por HTTP.

## Historia
**Como** usuaria del asistente, **quiero** abrir una aplicación web propia que hable con la API FastAPI, **para** usar el asistente con una interfaz moderna, separada del backend.

## Requisitos
- **R022.1** DEBE existir `frontend/` con React 18, Vite y TypeScript estricto, con su propio `package.json` y `package-lock.json`.
- **R022.2** DEBE tener rutas (`react-router-dom`): `/` (chat), `/foto` y `/estado`, con un encabezado común y el aviso «No es un canal oficial».
- **R022.3** La URL de la API DEBE leerse de `VITE_API_URL` (por defecto `http://127.0.0.1:8000`).
- **R022.4** `make frontend` DEBE instalar y levantar el servidor de desarrollo en `http://localhost:5173`.
- **R022.5** El frontend NO DEBE llamar a ningún modelo directamente: solo a la API.

## Criterios de aceptación
- **AC1** · **Dado** el repositorio recién clonado, **cuando** se ejecuta `make frontend`, **entonces** la app abre en el puerto 5173.
- **AC2** · **Dado** la app abierta, **cuando** se navega a `/estado`, **entonces** se ve la página sin recargar el documento.

## Fuera de alcance
Despliegue en Vercel.

## Métricas de éxito
`npm run build` sin errores de TypeScript.
