# 1 · Fundamentos

Esta dimensión es la base de `jan-project-standard`. Si falta, se aplica esa skill primero
(`--audit` y luego el modo no destructivo) o se resuelve aquí brecha por brecha.

| ID | Control | Cómo |
|---|---|---|
| F1 | `requires-python` | `requires-python = ">=3.13"` en `[project]` |
| F2 | Lockfile versionado | `uv lock`; **sí** se versiona `uv.lock`; la CI usa `uv sync --frozen` |
| F3 | `.python-version` | `3.13` |
| F4 | src-layout | `src/<paquete>/__init__.py`; evita importar el código sin instalarlo |
| F5 | Makefile `help` + `check` | `help` lista los targets con `## comentario`; `check` = lint + formato + tipos + pruebas |
| F6 | pre-commit | `make dev` instala los hooks `pre-commit` y `commit-msg` |
| F7 | README, LICENSE, CONSTITUTION | La constitución es la fuente única de verdad |
| F8 | `.editorconfig` | UTF-8, LF, 4 espacios en Python y 2 en YAML/JSON/TS |

**Regla de oro:** `git clone && make dev && make check` debe funcionar en una máquina limpia.
