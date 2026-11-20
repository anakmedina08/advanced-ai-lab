# Plan · SPEC-056 · Política de uso de IA en el proyecto

## Diseño
Documento corto con tablas, alineado con `.claude/settings.json`, ADR-023 y los subagentes de `.claude/agents/`.

## Decisiones
- La política describe lo que ya está configurado: si cambia la configuración, cambia la política en el mismo PR.

## Contrato
—

## Riesgos
- Que la política y la configuración se separen con el tiempo: el checklist del PR lo revisa.

## Alternativas descartadas
- Dejarlo en AGENTS.md: ese archivo es para el agente; la política es para personas y evaluadores.

## Estrategia de pruebas
Revisión humana y `make madurez` (G1).
