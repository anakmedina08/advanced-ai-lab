# SPEC-027 · Foto «¿qué hago?» en el frontend con confianza y estados

> Curso: Gestión M3 (Demo E2E) · Story points: **5** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
La demo de Gestión exige cargar un archivo en el frontend desacoplado, ver los estados y el resultado con su confianza; la API no devuelve la imagen difuminada.

## Historia
**Como** usuaria con una foto de un siniestro o de un bien, **quiero** subir la foto y ver qué detectó el modelo, con su confianza y qué hacer, **para** saber qué seguro aplica sin exponer a las personas de la foto.

## Requisitos
- **R027.1** `POST /fotos` DEBE aceptar `devolver_imagen=true` y responder la imagen difuminada en JPEG base64.
- **R027.2** La página DEBE permitir elegir o arrastrar una imagen (JPG/PNG ≤ 8 MB) y validar tipo y tamaño antes de enviar.
- **R027.3** DEBE mostrar estados `idle`, `cargando`, `listo` y `error`, la imagen difuminada con las cajas, la lista de detecciones con su confianza (%), el plan y la respuesta con fuente.
- **R027.4** DEBE mostrar el tiempo de inferencia y cuántas personas se difuminaron.

## Criterios de aceptación
- **AC1** · **Dado** una foto de 10 MB, **cuando** se elige, **entonces** se rechaza en el navegador sin llamar a la API.
- **AC2** · **Dado** una foto de un carro chocado, **cuando** se envía, **entonces** se ven las cajas con la confianza y el plan «siniestro».

## Fuera de alcance
Cámara en vivo.

## Métricas de éxito
Resultado en < 5 s con YOLO cargado en el *lifespan*.
