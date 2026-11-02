# ADR-008 · Imagen Docker multi-stage y estándar jan-project-standard

- **Fecha:** 2026-11-01
- **What:** (1) `Dockerfile` en dos etapas: *builder* con `uv` resuelve `uv.lock`; *runtime* copia solo el `.venv` y el código, corre como usuario sin privilegios y monta `data/` como volumen. (2) Se adopta el skill `jan-project-standard`: `CONSTITUTION.md` como fuente única de verdad, `Makefile` como interfaz, plantillas de PR e issues, Dependabot y labels.
- **Why:** la imagen final no lleva `uv`, cachés ni herramientas de build, y no incluye contenido de Seguros Bolívar (no se redistribuye). El estándar del docente unifica cómo se opera el repo (`make help`).
- **Where:** `Dockerfile`, `.dockerignore`, `Makefile`, `CONSTITUTION.md`, `.github/`, `.claude/skills/jan-project-standard/`.
- **Learned:** el paquete se instala editable para que `config.py` siga ubicando `data/` relativo a `/app`; dentro del contenedor, Ollama del host se alcanza con `OLLAMA_HOST=http://host.docker.internal:11434`.
