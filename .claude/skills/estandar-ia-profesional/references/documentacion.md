# 5 · Documentación y decisiones

## Estructura recomendada (Diátaxis)
```
docs/
├── README.md            ← índice
├── arquitectura.{json,html}  ← diagrama (Archify) o *.mmd (Mermaid)
├── decisiones/          ← ADRs + README.md (índice) + plantilla.md
├── runbook.md           ← operación
├── model-card.md / data-card.md
├── politica-uso-ia.md
└── madurez.md           ← informe del auditor
```

## D2-D3 · ADRs
- Un ADR por decisión que sea **difícil de revertir** o que alguien podría cuestionar después.
- Formato en `assets/plantillas/adr.md`: Contexto, Decisión, Alternativas, Consecuencias y Estado.
- Los ADRs son inmutables: si una decisión cambia, se escribe uno nuevo con "Reemplaza a ADR-00X".
- `docs/decisiones/README.md` es una tabla con número, título, estado y fecha.

## D6 · Runbook
Copiar `assets/plantillas/runbook.md`. Debe responder:
- cómo levantar todo;
- cómo saber si está sano;
- los 5 fallos más probables y cómo resolverlos;
- cómo rotar una llave;
- a quién escalar.

## D7 · Contexto para agentes
`AGENTS.md` (leído por Claude Code, OpenCode, Codex y Cursor) contiene:
- stack y comandos (`make help`);
- reglas no negociables;
- rutas prohibidas;
- dónde están las specs;
- cómo validar un cambio.

Se mantiene corto, de 200 líneas como máximo, y enlaza en lugar de copiar.
