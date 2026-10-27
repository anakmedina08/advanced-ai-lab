# Spec · Fase 1 — Base de conocimiento semántico y sistema Q&A

## Requisitos

### R1 · Scraping ético y reproducible
- El sistema DEBE leer `robots.txt` y `sitemap.xml` antes de descargar.
- El sistema DEBE omitir rutas en `Disallow` y fuera del alcance PERSONAS + CANALES.
- El sistema DEBE esperar ≥ 1 s entre peticiones y enviar un User-Agent identificable.
- **Escenario:** dada una URL en `/RecaudosElectronicos/`, cuando se arma el plan, entonces queda en
  "descartadas" con motivo `robots.txt`.

### R2 · Arquitectura Medallion
- Bronze guarda el HTML crudo y `capture.jsonl` (url, fecha, estado, sha256); nunca se edita.
- Silver contiene solo el texto editorial; Gold contiene un `.md` por página con metadatos,
  `corpus.jsonl`, `chunks.jsonl` y el conocimiento consolidado.
- **Escenario:** dado el pie con canales repetido en todas las páginas, cuando se procesa, entonces
  aparece UNA sola vez en el conocimiento consolidado.

### R3 · Tres tareas con LangChain
- Q&A, Resumen y FAQ usan TODO el conocimiento consolidado en el system prompt, temperatura 0.
- Las respuestas DEBEN citar la URL fuente y, si la información no está, usar la respuesta de
  no-información.
- **Escenario:** dada la pregunta "¿Quién ganó el mundial?", entonces la respuesta es la de no-información.

### R4 · Interfaz y evaluación
- Streamlit con pestañas Q&A, Resumen y FAQ.
- Banco de ≥ 20 preguntas con métricas automáticas y columnas de calificación manual.

## Tareas
- [x] T1 Descubrimiento (robots + sitemap + filtro de alcance)
- [x] T2 Descarga a Bronze con cortesía y reanudación
- [x] T3 Limpieza Silver (main, boilerplate, pie de canales)
- [x] T4 Gold (Markdown, corpus, chunks, conocimiento consolidado)
- [x] T5 Prompts versionados v1/v2/v3 y servicio LangChain
- [x] T6 Streamlit (3 funcionalidades)
- [x] T7 Banco de 24 preguntas y evaluación
- [ ] T8 Ejecutar scraping real y ajustar palabras clave del banco
- [ ] T9 Experimentación v1 vs v2 vs v3 y análisis para el informe
