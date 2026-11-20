# SPEC-058 · Guion de las sustentaciones fuera del repositorio público

> Curso: Gestión y Técnicas (higiene del repo) · Story points: **1** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
`docs/sustentacion.md` es el guion interno del equipo para las sustentaciones y estaba publicado en el repo público, enlazado desde el README y la matriz de requisitos.

## Historia
**Como** equipo, **quiero** que el guion de las sustentaciones quede solo en nuestros equipos, **para** no publicar material interno de preparación.

## Requisitos
- **R058.1** `docs/sustentacion.md` DEBE dejar de versionarse y, junto con la carpeta `docs/sustentacion/` (un guion por módulo), quedar en `.gitignore`; cada integrante conserva su copia local.
- **R058.2** README y `docs/requisitos.md` NO DEBEN enlazarlo.
- **R058.3** La página «Sustentación» del frontend y SPEC-042/045 se conservan, porque son parte del producto.

## Criterios de aceptación
- **AC1** · **Dado** `git ls-files docs/sustentacion.md`, **cuando** se ejecuta, **entonces** no devuelve nada.
- **AC2** · **Dado** un integrante con la copia local, **cuando** hace `git status`, **entonces** el archivo no aparece como cambio.

## Fuera de alcance
Borrarlo del historial: si se quiere, se hace junto con la limpieza del historial de ADR-023, en una sola reescritura coordinada.

## Métricas de éxito
0 enlaces rotos en README y en la matriz.
