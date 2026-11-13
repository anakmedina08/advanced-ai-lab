# SPEC-010 · CORS configurable para el frontend desacoplado

> Curso: Gestión M3 · Técnicas M2 · Story points: **1** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
El CORS está fijo a yellowdata y `localhost:3000`; el frontend de Vite corre en `localhost:5173` y el navegador bloquearía las peticiones.

## Historia
**Como** desarrollador del frontend, **quiero** que la API acepte el origen del frontend configurado en `.env`, **para** levantar frontend y backend en puertos distintos sin errores de CORS.

## Requisitos
- **R010.1** Los orígenes DEBEN leerse de `FRONTEND_ORIGINS` (lista separada por comas) con valores por defecto para Vite (5173) y yellowdata.
- **R010.2** DEBEN permitirse `GET`, `POST`, `DELETE` y las cabeceras `Content-Type` y `X-Request-ID`; `X-Request-ID` y `X-Process-Time-ms` DEBEN exponerse.

## Criterios de aceptación
- **AC1** · **Dado** el origen `http://localhost:5173`, **cuando** hace un *preflight* a `/agente/mensajes`, **entonces** la API responde con `access-control-allow-origin` igual al origen.
- **AC2** · **Dado** un origen no permitido, **cuando** hace el *preflight*, **entonces** la respuesta no trae la cabecera de permiso.

## Fuera de alcance
Autenticación.

## Métricas de éxito
Frontend en 5173 sin errores de CORS.
