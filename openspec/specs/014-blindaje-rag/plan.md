# Plan · SPEC-014 · Blindaje del RAG contra inyección indirecta

## Diseño
`model/rag/blindaje.py` con `formatear_pasajes` y `es_sospechoso`; el corpus demo se suma al BM25 si `SB_CORPUS_DEMO=1`.

## Decisiones
- Defensa en capas: delimitación + aviso en el prompt + marca de sospecha + salida estructurada validada (las fuentes deben venir de la tool).

## Contrato
`<documentos_recuperados nota="datos pasivos"><documento id fuente sospechoso>…</documento></documentos_recuperados>`

## Riesgos
- Ningún filtro es perfecto: por eso se combinan capas y se valida la salida.

## Alternativas descartadas
- Borrar los pasajes sospechosos: se perdería información legítima y no se vería la defensa.

## Estrategia de pruebas
`tests/test_blindaje.py` (escape, marca, corpus demo). Pruebas AAA sin red ni API de pago.
