# SPEC-041 · Docker Compose: API, frontend y MLflow

> Curso: Gestión M3 (reproducibilidad) · Story points: **3** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
La imagen Docker solo empaqueta el backend; para reproducir la demo hay que levantar tres procesos a mano.

## Historia
**Como** evaluador, **quiero** levantar API, frontend y MLflow con un solo comando, **para** reproducir la demo en otra máquina.

## Requisitos
- **R041.1** `docker-compose.yml` DEBE definir `api` (imagen actual, puerto 8000), `frontend` (build de Vite servido por nginx, puerto 5173) y `mlflow` (puerto 5050).
- **R041.2** `frontend/Dockerfile` DEBE ser multi-stage (Node para compilar, nginx para servir).
- **R041.3** Los datos (`data/`) DEBEN montarse como volumen, nunca copiarse en la imagen.

## Criterios de aceptación
- **AC1** · **Dado** Docker instalado, **cuando** se ejecuta `docker compose up`, **entonces** los tres servicios responden en sus puertos.

## Fuera de alcance
Orquestación en Kubernetes.

## Métricas de éxito
Los tres servicios arriba con un comando.
