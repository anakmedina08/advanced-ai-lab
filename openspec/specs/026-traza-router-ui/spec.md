# SPEC-026 · Panel de la decisión del router, tools y fuentes

> Curso: Técnicas M2 (2.3, 5.1) · Story points: **3** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
La rúbrica pide que se vea la decisión del router, no solo la respuesta; hoy esa información solo está en el JSON.

## Historia
**Como** jurado de la sustentación, **quiero** ver bajo cada respuesta la ruta, la confianza, las tools con su latencia y las fuentes, **para** comprobar que el agente decide con criterio.

## Requisitos
- **R026.1** Cada respuesta DEBE mostrar una insignia con la ruta (directo, datos, RAG, mixto, fuera de alcance) y su confianza.
- **R026.2** Un panel desplegable DEBE listar señales, tools habilitadas, tools usadas con milisegundos, fuentes y fuentes descartadas.
- **R026.3** Mientras transmite, DEBE verse el paso actual («Buscando en la base…», «Consultando datos…»).

## Criterios de aceptación
- **AC1** · **Dado** una respuesta de la ruta `datos`, **cuando** se abre el panel, **entonces** aparece `consultar_datos` con sus ms.
- **AC2** · **Dado** un saludo, **cuando** llega la respuesta, **entonces** la insignia dice «directo · sin búsqueda».

## Fuera de alcance
Gráficas históricas.

## Métricas de éxito
La decisión visible en el 100 % de las respuestas.
