# ADR-023 · Commits y PRs a nombre de las personas; el uso de IA se declara aparte

- **Fecha:** 2026-11-17
- **What:** los commits y las descripciones de PR quedan solo a nombre de quien los hace. Se aplica
  en dos capas:
  - `.claude/settings.json` fija `"attribution": {"commit": "", "pr": ""}` para todo el proyecto.
  - El hook `commit-msg` `limpiar-trailers-ia` borra `Co-Authored-By` de asistentes de IA,
    `Claude-Session` y «Generated with Claude Code» antes de validar Conventional Commits.

  Además, `git push`, `gh pr create` y `gh pr merge` quedan en `ask`: el agente solo los ejecuta si
  una persona lo aprueba en ese momento.
- **Why:**
  - 98 de 182 commits de `develop` tenían a Claude como coautor, y GitHub lo listaba como contributor.
  - El anuncio 007 de Gestión califica el trabajo de cada integrante (piso de 8 PR y 8 specs por persona).
  - La atribución dependía de la configuración de cada máquina.
- **Decisiones de diseño:**
  - **Borrar en vez de rechazar:** el commit no se interrumpe.
  - **Coautores humanos se conservan.**
  - **El uso de IA no se oculta:** se declara en la política de uso de IA (SPEC-056) y en el README.
  - **Historial existente sin reescribir:** reescribir `develop`/`main` cambia todos los SHA, rompe
    los clones e invalida firmas. Si el equipo lo decide, se hace una sola vez con
    `git filter-repo --message-callback`, coordinado y con respaldo.
- **Where:**
  - `.claude/settings.json`.
  - `.pre-commit-config.yaml` (hook `limpiar-trailers-ia`).
  - `scripts/limpiar_trailers_ia.py`.
  - `tests/test_limpiar_trailers_ia.py`.
- **Learned:**
  - Algunas versiones del agente ignoran `attribution`; el hook local es la red de seguridad.
  - Los commits hechos desde la web de GitHub no pasan por hooks: se revisan en el PR.
