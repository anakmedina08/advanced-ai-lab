# SPEC-035 · Model Registry del YOLO que usa la API

> Curso: Gestión M3 (MLflow) · Story points: **5** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
La rúbrica pide que el modelo que carga el backend esté versionado en el Model Registry y sea consistente con `repo@rev`.

## Historia
**Como** responsable del despliegue, **quiero** registrar el YOLO de la API como modelo versionado con alias `produccion`, **para** saber exactamente qué pesos sirve la API.

## Requisitos
- **R035.1** El YOLO DEBE registrarse como `pyfunc` (`sb-yolo-difuminado`) con los pesos como artefacto y una firma de entrada/salida.
- **R035.2** La versión DEBE llevar alias `produccion` y tags `repo@rev`, `sha256`, licencia y umbral; DEBE enlazar a la corrida de evaluación.
- **R035.3** `/health` DEBE informar el sha256 corto de los pesos cargados para comparar con el Registry.

## Criterios de aceptación
- **AC1** · **Dado** el registro ejecutado, **cuando** se abre Models en la UI, **entonces** aparece `sb-yolo-difuminado` versión 1 con alias `produccion`.

## Fuera de alcance
Servir el modelo desde MLflow.

## Métricas de éxito
Versión del Registry = pesos de la API (mismo sha256).
