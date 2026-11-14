# Plan · SPEC-041 · Docker Compose: API, frontend y MLflow

## Diseño
Compose v2 con volúmenes y variables desde `.env`.

## Decisiones
- nginx sirve los estáticos; la API sigue aparte (separación visible).

## Contrato
Puertos 8000, 5173 y 5050.

## Riesgos
- Imagen del backend pesada por torch: CPU.

## Alternativas descartadas
- Una sola imagen con todo: mezcla frontend y backend.

## Estrategia de pruebas
Build del frontend en la CI. Pruebas AAA sin red ni API de pago.
