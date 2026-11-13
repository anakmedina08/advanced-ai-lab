# Plan · SPEC-030 · Pruebas del frontend con Vitest y Testing Library

## Diseño
`vitest.config` dentro de `vite.config.ts`; `src/**/*.test.ts(x)`; `fetch` falso.

## Decisiones
- Vitest comparte la configuración de Vite: cero duplicación.

## Contrato
Script `npm test`.

## Riesgos
- jsdom no implementa todo: se prueban unidades y componentes.

## Alternativas descartadas
- Jest: requiere transformar TS/ESM aparte.

## Estrategia de pruebas
La propia suite. Pruebas AAA sin red ni API de pago.
