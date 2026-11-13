# Plan · SPEC-046 · Paridad con la versión Streamlit: modos de contexto, reprocesar y foto con Claude

## Diseño
Hook `useAjustes` (proveedor, modo, versión) en `localStorage`; endpoints finos sobre los controladores existentes.

## Decisiones
- El agente M2 sigue siendo el modo por defecto del chat (memoria, router y streaming); los demás modos son los de la Fase 1 y 2 para comparar.

## Contrato
`POST /preguntas{modo: completo|reducido|rag|agente}`, `GET /sistema`, `POST /pipeline/procesar`, `POST /pipeline/descubrir`.

## Riesgos
- Reprocesar cambia el corpus: si cambia el contenido, Qdrant recalcula embeddings al siguiente uso.

## Alternativas descartadas
- Dejar esas funciones solo en Streamlit: Streamlit no se acepta en la demo.

## Estrategia de pruebas
Pytest de los endpoints y Vitest del modo en el chat y de la foto. Pruebas AAA sin red ni API de pago.
