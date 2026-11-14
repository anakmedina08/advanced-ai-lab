# SPEC-048 · Diagrama oficial con Archify y Docker Compose verificado

> Curso: Gestión M3 (documentación y reproducibilidad) · Story points: **3** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
El diagrama de arquitectura usaba el formato de Archify pero no su herramienta, y Docker Compose estaba escrito sin probar; el build del frontend fallaba porque se copiaba node_modules de Windows.

## Historia
**Como** jurado de Gestión, **quiero** ver el diagrama generado con Archify y la demo reproducible con Docker, **para** verificar la arquitectura y la reproducibilidad del proyecto.

## Requisitos
- **R048.1** `docs/arquitectura.html` DEBE generarse con Archify (`finalize` con perfil showcase y evidencia del repositorio) desde `docs/arquitectura.json`.
- **R048.2** `frontend/.dockerignore` DEBE excluir node_modules, dist y la caché de Vite para que la imagen compile en Linux.
- **R048.3** `docker compose build` DEBE construir la API y el frontend, y sus contenedores DEBEN responder (`/health` y la SPA).
- **R048.4** La matriz de requisitos DEBE reflejar solo lo verificado.

## Criterios de aceptación
- **AC1** · **Dado** Docker Desktop encendido, **cuando** se ejecuta `docker compose build`, **entonces** las imágenes de la API y del frontend se construyen.
- **AC2** · **Dado** el contenedor de la API, **cuando** se consulta `/health`, **entonces** responde `status: ok`.

## Fuera de alcance
Despliegue en la nube.

## Métricas de éxito
Archify con todos sus checks en verde; contenedores respondiendo.
