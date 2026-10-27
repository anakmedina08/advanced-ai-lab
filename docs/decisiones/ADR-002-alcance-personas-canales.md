# ADR-002 · Alcance PERSONAS + CANALES DE ATENCIÓN

- **Categoría:** datos / alcance
- **Why:** el cliente objetivo es quien interactúa por primera vez. Incluir 54 páginas de empresas y
  1.225 artículos de blog diluye el contexto y multiplica el costo.
- **Where:** `config.EXCLUDE_PATTERNS` y `config.SECTION_RULES`.
- **Consecuencias:** preguntas de empresas o del blog → respuesta de no-información (comportamiento correcto).
- **Lección:** el pie del sitio contiene los canales de atención: se guarda una sola vez como documento
  propio y se elimina de cada página (si no, el RAG lo devolvería en cada consulta).
