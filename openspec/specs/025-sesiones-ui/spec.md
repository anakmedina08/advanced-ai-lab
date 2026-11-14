# SPEC-025 · Sesiones en el frontend: hilos, usuario y memoria visible

> Curso: Técnicas M2 (1.1, 1.3) · Story points: **3** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
Para demostrar la memoria hay que abrir un hilo nuevo, volver a uno anterior tras reiniciar el backend y ver qué recuerda el asistente del usuario.

## Historia
**Como** usuaria recurrente, **quiero** ver mis conversaciones, abrir una nueva y saber qué recuerda el asistente de mí, **para** retomar conversaciones y controlar mis datos.

## Requisitos
- **R025.1** La barra lateral DEBE listar los hilos (guardados en `localStorage`) con el título de su primer mensaje y permitir crear uno nuevo.
- **R025.2** Al elegir un hilo DEBE cargarse su historial desde `GET /agente/conversaciones/{id}`.
- **R025.3** El `usuario_id` DEBE generarse una vez y conservarse; el panel «Lo que recuerdo de ti» DEBE mostrar `GET /agente/usuarios/{id}/perfil` y permitir borrarlo.
- **R025.4** Borrar un hilo DEBE llamar a `DELETE` y quitarlo de la lista.

## Criterios de aceptación
- **AC1** · **Dado** un hilo con mensajes y el backend reiniciado, **cuando** se recarga la página y se abre el hilo, **entonces** se ve el historial.
- **AC2** · **Dado** el perfil con nombre y empresa, **cuando** se pulsa «Olvidar», **entonces** el panel queda vacío.

## Fuera de alcance
Cuentas de usuario con contraseña.

## Métricas de éxito
Hilo recuperado tras reiniciar el backend en la demo.
