---
name: operar-asistente
description: Opera el Asistente Seguros Bolívar en este repositorio - scraping Medallion, API FastAPI, chat, recomendador, skills y telemetría de agentes - con los comandos make y sb correctos. Úsala cuando haya que levantar, actualizar, probar o depurar cualquier parte del producto.
license: MIT
compatibility: Claude Code y OpenCode. Requiere uv y Python 3.13; npx solo para instalar skills externas.
metadata:
  uso: desarrollo
  autor: equipo-sb-asistente
---

## Mapa rápido
| Necesidad | Comando |
|---|---|
| Preparar entorno | `make dev` |
| Datos del asistente (scraping → Gold) | `make data` · sin red: `make process` |
| Datos del recomendador | `make reco` |
| API (y chat) | `make api` → `http://127.0.0.1:8000/docs` · `POST /chat` |
| Calidad | `make check` (ruff + formato + pytest ≥ 85 %) |
| Skills | `make skills` · `make skill-new NAME=x DESC="..." USO=asistente` · `make skill-add REPO=owner/repo SKILL=nombre` |
| Eventos de agentes | `make agentes` |

## Reglas
1. Lee `CONSTITUTION.md` y `AGENTS.md` antes de planear; la spec activa está en `openspec/specs/fase2-producto-unico/`.
2. MVC: la vista (API, Streamlit, CLI) solo llama al controlador.
3. Nunca leas ni escribas `.env` ni `data/`; nunca pegues claves en el chat.
4. Una skill externa entra como `desarrollo`; marcarla `uso: asistente` requiere PR revisado y que respete las reglas del prompt.
5. Al cerrar una tarea, delega en `documentador` para actualizar `docs/requisitos.md`.

## Depurar el chat
- `GET /salud` dice si faltan `data/gold/chunks.jsonl` o `data/recomendador/clientes.csv`.
- `POST /chat` con `{"mensaje": "...", "modo": "clasificador"}` muestra la intención sin gastar tokens.
