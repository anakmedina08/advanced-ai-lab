# Plan · SPEC-048 · Diagrama oficial con Archify y Docker Compose verificado

## Diseño
Skill externa Archify instalada con `make skill-add` (en `skills-lock.json`); `.dockerignore` del frontend; el script propio del diagrama se elimina.

## Decisiones
- La skill externa no se versiona (18 MB): se reinstala con `make skill-add` y queda registrada en `skills-lock.json`.

## Contrato
—

## Riesgos
- La imagen de la API no incluye el extra de visión: `/fotos` responde 503 en Docker hasta instalarlo.

## Alternativas descartadas
- Mantener el diagrama hecho a mano: la rúbrica pide Archify.

## Estrategia de pruebas
Verificación con `archify finalize` y contenedores reales. Pruebas AAA sin red ni API de pago.
