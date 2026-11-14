# Plan · SPEC-024 · Chat con streaming de la respuesta del agente

## Diseño
`src/pages/Chat.tsx` + `src/components/Burbuja.tsx`; estado con `useReducer`; Markdown con `react-markdown`.

## Decisiones
- `useReducer` para que las transiciones de estado sean explícitas y probables.

## Contrato
Consume `POST /agente/stream`.

## Riesgos
- Markdown con HTML: `react-markdown` no renderiza HTML crudo (sin XSS).

## Alternativas descartadas
- Esperar el JSON completo: no hay streaming.

## Estrategia de pruebas
Vitest + Testing Library con un `fetch` falso que emite SSE. Pruebas AAA sin red ni API de pago.
