# SPEC-051 · Anuncios del curso trazados a requisitos y herramientas

> Curso: Técnicas y Gestión (trazabilidad) · Story points: **3** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
Los requisitos de cada módulo llegan por anuncios del campus y cambian con el semestre (por ejemplo, Streamlit quedó prohibido desde el M2). No había un registro en el repo de qué pidió cada anuncio ni de qué herramientas se exigen o no se permiten.

## Historia
**Como** equipo, **quiero** cada anuncio del profesor resumido y contrastado con el repo, **para** no perder requisitos y detectar a tiempo lo que el curso ya no permite.

## Requisitos
- **R051.1** `docs/anuncios/README.md` DEBE indexar los anuncios de las dos materias con tipo, fechas y pendientes.
- **R051.2** `docs/anuncios/herramientas.md` DEBE listar herramientas exigidas, deseables y no permitidas, con la columna Paquete para las verificables.
- **R051.3** Cada anuncio con requisitos DEBE tener su resumen con la tabla de contraste.
- **R051.4** Los resúmenes NO DEBEN incluir contraseñas, enlaces de grabaciones o grupos ni nombres de otros estudiantes.
- **R051.5** `docs/requisitos.md` DEBE incluir los requisitos nuevos con su plan (spec o historia).

## Criterios de aceptación
- **AC1** · **Dado** `make madurez`, **cuando** se evalúa la dimensión 9, **entonces** K1 y K2 están en ✅.
- **AC2** · **Dado** que el repo usa un paquete ⛔ del catálogo, **cuando** corre el auditor, **entonces** K4 falla hasta retirarlo (SPEC-052).

## Fuera de alcance
Implementar los requisitos nuevos (cada uno tiene su spec).

## Métricas de éxito
Dimensión 9 con K1 y K2 en ✅; K4 en ❌ hasta SPEC-052.
