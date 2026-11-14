# SPEC-020 · Sesiones: historial, checkpoints (time travel) y borrado por REST

> Curso: Técnicas M2 (1.1) · Story points: **3** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
El historial y el borrado solo existen por JSON-RPC; el frontend necesita recuperar un hilo tras reiniciar y mostrar sus checkpoints.

## Historia
**Como** usuaria que vuelve a una conversación, **quiero** recuperar el hilo al recargar la página o reiniciar el backend, **para** continuar donde iba.

## Requisitos
- **R020.1** `GET /agente/conversaciones/{id}` DEBE devolver los mensajes guardados.
- **R020.2** `GET /agente/conversaciones/{id}/checkpoints` DEBE listar los checkpoints (id, paso, fecha, mensajes) para inspeccionar el hilo (time travel).
- **R020.3** `DELETE /agente/conversaciones/{id}` DEBE borrar el hilo.
- **R020.4** `GET` y `DELETE /agente/usuarios/{uid}/perfil` DEBEN consultar y borrar la memoria de largo plazo.
- **R020.5** Los ids DEBEN validarse (6–64 caracteres seguros).

## Criterios de aceptación
- **AC1** · **Dado** un hilo con dos turnos, **cuando** se reinicia el backend y se pide el historial, **entonces** vuelven los dos turnos.
- **AC2** · **Dado** un id con `/`, **cuando** se pide, **entonces** responde 422.

## Fuera de alcance
Bifurcar un hilo desde un checkpoint (se documenta como trabajo futuro).

## Métricas de éxito
Hilo recuperado tras reinicio en la prueba con SQLite en disco.
