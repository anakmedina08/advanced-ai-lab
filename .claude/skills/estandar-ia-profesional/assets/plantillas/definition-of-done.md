## Definition of Ready (antes de empezar)
- [ ] La historia tiene criterios de aceptación verificables.
- [ ] Existe una spec (`openspec/specs/NNN-*`) o no aplica.
- [ ] Dependencias y datos necesarios están identificados.

## Definition of Done (antes de fusionar)
- [ ] Cumple los criterios de aceptación de la spec.
- [ ] `make check` en verde (lint, formato, tipos y pruebas con cobertura ≥ umbral).
- [ ] Hay pruebas nuevas para el comportamiento nuevo.
- [ ] Si toca prompts, RAG o agente: evals sin regresión.
- [ ] Documentación actualizada (README, docs, ADR si hubo decisión).
- [ ] `CONSTITUTION.md` actualizada si cambió arquitectura, stack o proceso.
- [ ] Sin secretos ni datos personales (gitleaks en verde).
- [ ] Revisado y aprobado por una persona distinta al autor.
