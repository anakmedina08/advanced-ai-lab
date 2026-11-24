# 8 · Gobernanza de agentes de IA

**Objetivo:** que los agentes (Claude Code, OpenCode, subagentes, skills) aceleren el trabajo
**sin** tener más permisos que un practicante nuevo y **sin** que su intervención sea ambigua.

## G1 · Política de uso de IA
`assets/plantillas/politica-uso-ia.md` define:
- qué herramientas se usan;
- qué pueden hacer;
- qué está prohibido;
- cómo se revisa;
- cómo se declara el uso en entregas académicas o a clientes.

La política se decide **una vez**, no en cada PR.

## G2 · Permisos del agente
```json
"permissions": {
  "deny": ["Read(./.env)", "Read(./.env.*)", "Read(./data/**)", "Bash(git filter-repo:*)"],
  "ask":  ["Bash(git push:*)", "Bash(gh pr merge:*)", "Bash(gh pr create:*)"]
}
```
El agente nunca lee secretos ni datos crudos. Push, creación y fusión de PRs quedan en `ask`: solo
ocurren si una persona los aprueba en ese momento (o las hace ella misma).

## G3 · Atribución
La atribución en commits y PRs se decide en `.claude/settings.json`, para que no dependa de la configuración de cada máquina:
```json
"attribution": { "commit": "", "pr": "" }
```
- **Vacío:** los commits aparecen solo a nombre de la persona; el uso de IA se declara en la política (G1).
- **Texto propio** (por ejemplo `"Asistido por IA"`): queda visible en cada commit, sin coautor.

Lo importante es que sea una **decisión explícita y registrada en un ADR**, no un efecto secundario.

## G4 · Filtro de trailers
Algunas versiones de los agentes ignoran la configuración de `attribution`. La red de seguridad
es un hook `commit-msg` **del proyecto** que elimina esas líneas antes de validar el mensaje.

El agente crea `scripts/limpiar_trailers_ia.py` con esta lógica y su prueba en `tests/`:

```python
import re, sys
from pathlib import Path

TRAILERS_IA = re.compile(
    r"^(co-authored-by:.*(claude|anthropic|copilot|openai|cursor|devin).*"
    r"|claude-session:.*|.*generated with \[?claude code.*"
    r"|https://claude\.ai/code/session_\S+)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

def limpiar(texto: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", TRAILERS_IA.sub("", texto)).rstrip() + "\n"

if __name__ == "__main__":
    ruta = Path(sys.argv[1]); original = ruta.read_text(encoding="utf-8")
    if (limpio := limpiar(original)) != original:
        ruta.write_text(limpio, encoding="utf-8")
```

Se registra en `.pre-commit-config.yaml` con `stages: [commit-msg]`, **antes** del validador de
Conventional Commits. Los commits hechos desde la web de GitHub no pasan por él.

## G5-G7 · Skills y subagentes
- **Skills propias:**
  - frontmatter validado (`name` igual a la carpeta, `description` que dice cuándo usarla);
  - `metadata.uso: asistente` o `desarrollo`;
  - una sola tarea por skill.
- **Skills de terceros:** se instalan con `npx skills add`, quedan fijadas por hash en `skills-lock.json` y se revisan como cualquier dependencia.
- **Subagentes** (`.claude/agents/*.md`):
  - responsabilidad única;
  - herramientas mínimas;
  - descripción que diga cuándo delegarles.

## G8 · Humano en el circuito
- CODEOWNERS sobre `.claude/`, `.github/`, `src/` y `pyproject.toml`.
- Protección de rama: los PRs generados por un agente requieren la aprobación de una persona distinta a quien lo lanzó.
- Para acciones con costo (evals con LLM pagado, despliegues): `environment` de GitHub con revisores obligatorios.
