# ADR-014 · Skills propias y de terceros (Claude Code, OpenCode y skills.sh)

- **Fecha:** 2026-11-06
- **What:** las skills son carpetas con `SKILL.md` en `.claude/skills`, `.agents/skills` o `.opencode/skills` (las tres rutas que lee OpenCode; Claude Code lee `.claude/skills`). `model/skills.py` las valida con las reglas de OpenCode. Las propias se crean con `make skill-new`; las existentes se buscan e instalan desde el directorio abierto con `make skill-find` y `make skill-add` (`npx skills add … -a claude-code -a opencode`). `opencode.json` define los permisos.
- **Why:** reutilizar skills de la comunidad en ambos agentes y sumar comportamiento al chat (formato, comparación, lenguaje simple) sin tocar el código.
- **Where:** `.claude/skills/` (respuesta-cliente, comparar-seguros, explicar-simple, operar-asistente, jan-project-standard), `model/skills.py`, `GET /skills`, `sb skills`, `Makefile`, `opencode.json`, `skills-lock.json` (lo crea `npx skills`).
- **Learned:** solo `metadata.uso: asistente` llega al chat público, así que una skill externa entra como herramienta de desarrollo hasta que un PR revisado la marque. Las instrucciones se recortan a 4 000 caracteres, sus llaves se escapan y las `<reglas>` del prompt mantienen prioridad. `npx skills` enlaza `.claude/skills` → `.agents/skills`; el cargador ignora el enlace duplicado.
