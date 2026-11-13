# SPEC-045 · Entregables por curso en React

> Curso: Técnicas M2 · Gestión M3 · Story points: **3** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
La página «Entregables por curso» (requisitos por curso con estado, evidencia y cifras en vivo) solo existe en Streamlit.

## Historia
**Como** jurado de la sustentación, **quiero** ver por curso qué está cumplido, en curso o pendiente, con su evidencia y las cifras del repositorio, **para** recorrer los entregables en vivo durante la sustentación.

## Requisitos
- **R045.1** `GET /proyecto` DEBE devolver los requisitos de `docs/requisitos.md` por sección, los contadores (pruebas, specs, ADR, tareas) y los enlaces.
- **R045.2** La página DEBE mostrar tarjetas de cifras, enlaces, pestañas por curso, barra de progreso y filtro por estado.

## Criterios de aceptación
- **AC1** · **Dado** la sección de Gestión, **cuando** se filtra por «pendiente», **entonces** solo se ven los requisitos pendientes.

## Fuera de alcance
Editar requisitos desde la app.

## Métricas de éxito
Mismas cifras que la página Streamlit.
