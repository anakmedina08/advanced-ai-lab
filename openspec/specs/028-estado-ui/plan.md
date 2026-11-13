# Plan · SPEC-028 · Página de estado del servicio y aviso de API caída

## Diseño
Hook `useSalud` y componente `AvisoConexion`.

## Decisiones
- Un solo chequeo al cargar y al reintentar: no se satura la API.

## Contrato
Usa `GET /health`.

## Riesgos
- Falsos negativos por timeout corto: 5 s.

## Alternativas descartadas
- Sondeo cada pocos segundos: ruido innecesario.

## Estrategia de pruebas
Prueba del componente con `fetch` falso. Pruebas AAA sin red ni API de pago.
