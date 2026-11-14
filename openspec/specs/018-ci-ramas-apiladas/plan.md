# Plan · SPEC-018 · CI en las PR apiladas (base feature/*)

## Diseño
Se amplía el filtro `branches` del evento `pull_request` en `.github/workflows/ci.yml`.

## Decisiones
- Patrón `feature/**` en lugar de `**`: las ramas de bots siguen apuntando a `develop`.

## Contrato
Filtro de ramas del workflow.

## Riesgos
- Más minutos de CI: las PR son pequeñas.

## Alternativas descartadas
- Esperar a que GitHub reapunte cada PR al fusionar la anterior: se revisaría sin evidencia.

## Estrategia de pruebas
La propia PR muestra el check en verde. Pruebas AAA sin red ni API de pago.
