# ADR-003 · requests + trafilatura, sin Selenium

- **Categoría:** scraping
- **Why:** segurosbolivar.com usa Angular con renderizado en servidor: el HTML de `requests` ya trae
  el contenido (verificado: 2–5 mil caracteres útiles por página). Selenium sería más lento y frágil.
- **Where:** `scraping/fetch.py`, `processing/clean.py` (se extrae `<main>`, se quitan `nav`, `header`
  y `footer`, que el sitio anida DENTRO de `<main>`).
- **Limitación detectada:** en las pestañas de coberturas solo la primera pestaña viene renderizada;
  el detalle completo está en los clausulados PDF (registrados en `pdf_links.json` para la Fase 2).
- **Alternativa:** Scrapling (Clase 3) si el sitio cambia a renderizado en cliente.
