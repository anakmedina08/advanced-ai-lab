# Plan · SPEC-051 · Anuncios del curso trazados a requisitos y herramientas

## Diseño
Documentación generada con la skill `seguimiento-anuncios-curso` a partir de los anuncios 001-006 (551462) y 005-007 (551475).

## Decisiones
- Resumen con palabras propias, no copia del correo, porque el repo es público.
- Los anuncios de logística quedan solo en el índice.

## Contrato
Formato de tablas de `docs/anuncios/herramientas.md`: Herramienta | Paquete | Estado | Desde | Reemplazo / nota | En el proyecto.

## Riesgos
- Un anuncio posterior puede cambiar el estado de una herramienta: el paso de seguimiento actualiza la fila y anota el anuncio.

## Alternativas descartadas
- Guardar los correos completos: exponen datos sensibles y de terceros.

## Estrategia de pruebas
Verificación con `make madurez` (K1, K2, K4) y revisión humana de que no haya datos sensibles.
