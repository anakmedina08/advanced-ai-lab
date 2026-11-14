# Plan · SPEC-047 · Cierre para la sustentación: matriz al día, estado «no planeado» y tablero sin pendientes

## Diseño
Nuevo estado en `model/proyecto.ESTADOS`, en `RequisitoOut` y en la página; actualización de la matriz.

## Decisiones
- Cerrar como *not planned* (no como hecho) lo que no se hará: es lo honesto y lo que pide el curso.

## Contrato
Estado `no planeado`.

## Riesgos
- Ocultar trabajo pendiente: cada tarea cerrada deja su motivo en el issue.

## Alternativas descartadas
- Dejar los issues abiertos: incumple la regla del profesor.

## Estrategia de pruebas
Pytest del lector de la matriz y Vitest del filtro. Pruebas AAA sin red ni API de pago.
