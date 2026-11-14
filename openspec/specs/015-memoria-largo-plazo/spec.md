# SPEC-015 · Memoria de largo plazo con Store y namespace por usuario

> Curso: Técnicas M2 (1.3) · Story points: **5** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
El agente recuerda dentro de un hilo (checkpointer) pero en una conversación nueva olvida quién es el usuario.

## Historia
**Como** usuaria recurrente, **quiero** que el asistente recuerde mi nombre, empresa y perfil (vehículo, vivienda, mascota) en un hilo nuevo, **para** no repetir mis datos en cada conversación.

## Requisitos
- **R015.1** Un `SqliteStore` persistente DEBE guardar hechos en el namespace `("usuarios", usuario_id, "perfil")`.
- **R015.2** Los hechos DEBEN extraerse sin LLM («me llamo…», «trabajo en…», «vivo en…» y el perfil de `intencion`) y guardarse con `store.put`.
- **R015.3** Un `dynamic_prompt` DEBE recuperar el perfil con `store.search` y añadirlo al prompt del sistema dentro de `<perfil_usuario>`.
- **R015.4** DEBE poder consultarse y borrarse el perfil (derecho a la supresión).
- **R015.5** Correos, teléfonos y números de documento NUNCA se guardan.

## Criterios de aceptación
- **AC1** · **Dado** «Me llamo Ana y trabajo en Carvajal» en el hilo A, **cuando** se abre el hilo B del mismo usuario y se pregunta «¿dónde trabajo?», **entonces** el prompt del hilo B contiene `empresa: Carvajal`.
- **AC2** · **Dado** el usuario borra su perfil, **cuando** se consulta, **entonces** el namespace está vacío.

## Fuera de alcance
Búsqueda semántica en el Store (índice de embeddings).

## Métricas de éxito
Recuperación del perfil en el 100 % de los hilos nuevos de las pruebas.
