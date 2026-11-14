# Plan · SPEC-029 · Diseño responsive y accesible

## Diseño
CSS con variables, `@media`, `:focus-visible`; botón de menú.

## Decisiones
- Mobile-first con un solo punto de quiebre.

## Contrato
—

## Riesgos
- Contraste del tema oscuro: se validan los colores.

## Alternativas descartadas
- Framework CSS: peso innecesario.

## Estrategia de pruebas
Prueba de que la barra se pliega (Testing Library) y revisión manual a 375 px. Pruebas AAA sin red ni API de pago.
