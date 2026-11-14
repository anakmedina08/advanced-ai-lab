# SPEC-032 · Elegir el proveedor del LLM desde el frontend

> Curso: Técnicas M2 (3.1) · Story points: **2** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
El backend usa el proveedor de `.env` (en el equipo de la demo, Ollama) y el frontend no puede pedir Claude; el modelo local responde peor y sin streaming de tool calls.

## Historia
**Como** integrante del equipo en la demo, **quiero** elegir Claude, Ollama o DeepSeek en el frontend, **para** mostrar el agente con el modelo adecuado sin tocar el `.env`.

## Requisitos
- **R032.1** El encabezado DEBE tener un selector de proveedor (Claude por defecto, configurable con `VITE_LLM_PROVIDER`) guardado en `localStorage`.
- **R032.2** Cada mensaje al agente DEBE enviar `proveedor`; la API ya lo valida contra la lista de proveedores.

## Criterios de aceptación
- **AC1** · **Dado** el selector en «Claude», **cuando** se envía una pregunta, **entonces** el cuerpo de la petición lleva `proveedor: "anthropic"`.

## Fuera de alcance
Elegir el modelo exacto.

## Métricas de éxito
100 % de las peticiones con el proveedor elegido.
