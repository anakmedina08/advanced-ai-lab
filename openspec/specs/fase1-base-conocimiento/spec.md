# Spec · Fase 1 — Base de conocimiento y sistema Q&A (Seguros Bolívar)

> Qué debe hacer el sistema y cómo se verifica. El **cómo se construye** está en
> [`plan.md`](plan.md) y el **trabajo pendiente** en [`tasks.md`](tasks.md).

## Contexto

La información pública de Seguros Bolívar para personas está repartida en decenas de páginas con
menús y textos repetidos. El sistema la convierte en un corpus limpio y trazable y responde
preguntas citando la página de origen.

## Requisitos

### R1 · Scraping ético y reproducible
- DEBE leer `robots.txt` y `sitemap.xml` antes de descargar y omitir rutas en `Disallow`.
- DEBE limitarse al alcance PERSONAS + CANALES (excluye empresas, proveedores, blog, portales).
- DEBE esperar ≥ 1 s entre peticiones, con timeout y User-Agent identificable.
- DEBE ser reanudable (no repetir páginas ya capturadas con estado 200).
- **Escenario:** dada una URL en `/RecaudosElectronicos/`, cuando se arma el plan, entonces queda
  en «descartadas» con motivo `robots.txt`.

### R2 · Arquitectura Medallion con metadatos
- Bronze guarda el HTML crudo y `capture.jsonl` (url, fecha, estado, sha256); nunca se edita.
- Silver guarda solo el texto editorial; Gold, un `.md` con frontmatter por página, `corpus.jsonl`,
  `chunks.jsonl` y el conocimiento consolidado.
- Cada documento Gold DEBE tener URL, título, sección, fecha de captura y hash.
- Las páginas duplicadas (mismo hash de texto) DEBEN descartarse antes de detectar boilerplate.
- **Escenario:** dado el pie con canales repetido en todas las páginas, cuando se procesa, entonces
  aparece UNA sola vez en el conocimiento consolidado.

### R3 · Q&A, Resumen y FAQ con LangChain
- Usan TODO el conocimiento en el system prompt con Claude, esfuerzo `low` (ADR-001, ADR-010).
- Las respuestas DEBEN citar la URL fuente y, si la información no está, usar la respuesta de
  no-información.
- **Escenario:** dada la pregunta «¿Quién ganó el mundial?», entonces la respuesta es la de
  no-información.
- **Escenario:** dada «¿Puedo comprar el SOAT en línea?», entonces responde que Seguros Bolívar dejó
  de venderlo el 3 de octubre de 2025 y cita la página.

### R4 · Contexto reducido para modelos locales (ADR-006)
- Con Ollama, DEBE poder enviarse solo el bloque de canales y los fragmentos más relevantes, cada
  uno con su URL, en una ventana de 8 192 tokens.
- **Escenario:** dada «¿Cuál es el WhatsApp de atención?», entonces el contexto incluye
  «322 332 2322» y su URL.

### R5 · Interfaz con el proceso visible
- La interfaz DEBE mostrar las etapas descubrir → extraer → limpiar → deduplicar → enriquecer con
  sus métricas (URLs, páginas, tokens, descartes), la tabla del corpus y un Q&A con fuentes citadas.
- DEBE poder reprocesar Bronze → Gold en vivo sin volver a la web.

### R6 · Evaluación
- Banco de ≥ 20 preguntas (incluye fuera de alcance y adversariales) con métricas automáticas:
  palabras clave, cita de la fuente y rechazo correcto; comparación entre versiones de prompt.

### R7 · Calidad y operación
- MVC: las vistas solo hablan con `controller/` (ADR-007).
- ≥ 120 pruebas AAA sin red ni API; Ruff sin errores; CI en verde.
- Imagen Docker multi-stage CPU que corre la interfaz montando `data/` (ADR-008).
