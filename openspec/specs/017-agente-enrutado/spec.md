# SPEC-017 · Agente con router: tools por ruta y decisión visible

> Curso: Técnicas M2 (2.3) · Story points: **5** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
El router existe aislado; el agente sigue teniendo todas las tools y el usuario no ve por qué se tomó una ruta.

## Historia
**Como** jurado de la sustentación, **quiero** ver en cada turno la ruta elegida, las tools usadas y las fuentes, **para** comprobar que el agente no busca ante un saludo y combina fuentes en la pregunta mixta.

## Requisitos
- **R017.1** El controlador DEBE enrutar antes de invocar el agente y pasar la ruta en el contexto del turno.
- **R017.2** Un middleware DEBE dejar al modelo solo las tools de la ruta (directo → ninguna).
- **R017.3** `fuera_de_alcance` DEBE responderse sin llamar al LLM.
- **R017.4** `TurnoAgente` DEBE incluir la `decision` del router y `usuario_id`.
- **R017.5** `POST /agente/mensajes` DEBE exponer el turno por REST con `AgenteIn`/`AgenteOut`.

## Criterios de aceptación
- **AC1** · **Dado** «hola», **cuando** se conversa, **entonces** no hay llamadas a `buscar_conocimiento`.
- **AC2** · **Dado** «¿cuántas pólizas se vendieron en 2025?», **cuando** se conversa, **entonces** la única tool ofrecida al modelo es `consultar_datos`.
- **AC3** · **Dado** «cuéntame un chiste de fútbol», **cuando** se conversa, **entonces** la respuesta es fija y el LLM no se llama.

## Fuera de alcance
Streaming (historia 018).

## Métricas de éxito
0 búsquedas en saludos en el banco del router.
