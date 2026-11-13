# Plan · SPEC-038 · Diagramas de arquitectura (Archify) y del grafo del agente

## Diseño
JSON fuente (componentes, relaciones, límites de confianza) renderizado a HTML+SVG autocontenido; Mermaid en Markdown. La skill Archify es externa: instalarla requiere aprobación del equipo (`make skill-add REPO=tt-a1i/archify SKILL=archify`).

## Decisiones
- Mermaid se ve en GitHub y se versiona como texto.

## Contrato
—

## Riesgos
- Diagramas que envejecen: se actualizan en la misma PR que cambie la arquitectura.

## Alternativas descartadas
- Imágenes PNG: no se revisan en el diff.

## Estrategia de pruebas
Revisión visual en GitHub. Pruebas AAA sin red ni API de pago.
