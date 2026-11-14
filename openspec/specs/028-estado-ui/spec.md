# SPEC-028 · Página de estado del servicio y aviso de API caída

> Curso: Gestión M3 (Demo E2E) · Story points: **2** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
Si la API no responde, el usuario ve errores sueltos; en la demo conviene mostrar el estado de cada componente.

## Historia
**Como** integrante del equipo, **quiero** ver en `/estado` qué componentes están listos y un aviso global si la API no responde, **para** detectar y explicar fallas en la sustentación.

## Requisitos
- **R028.1** `/estado` DEBE mostrar `GET /health`: estado, versión, LLM y cada componente con su indicador.
- **R028.2** Al iniciar, la app DEBE consultar `/health` y mostrar un aviso persistente si la API no responde, con «Reintentar».

## Criterios de aceptación
- **AC1** · **Dado** la API apagada, **cuando** se abre la app, **entonces** aparece el aviso «No hay conexión con la API».
- **AC2** · **Dado** la API arriba sin índice Qdrant, **cuando** se abre `/estado`, **entonces** el componente `indice_qdrant` aparece en rojo.

## Fuera de alcance
Alertas por correo.

## Métricas de éxito
Aviso visible en < 5 s.
