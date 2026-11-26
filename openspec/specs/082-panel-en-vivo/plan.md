# Plan · SPEC-082

1. **Modelo.** `model/panel.py`: `publicar()` (opcional, hilo *daemon*, timeout 3 s, recorte a
   120 caracteres), `tool_por_mcp()` y `turno_trazado()`; solo biblioteca estándar.
2. **Vista.** `view/mcp.py`: cada tool se envuelve en `_ConAviso`, que avisa el nombre y delega en el
   `BaseTool` de LangChain (el MCP sigue siendo un adaptador delgado).
3. **Controlador.** `AgenteAsistente._trazar` llama a `panel.turno_trazado` después de registrar la traza.
4. **CI.** `.aviso_panel` en `.gitlab-ci.yml` con un ancla YAML (`safe_load` la entiende), usada en
   `.uv`, `.docker` y `deploy`. Usa `python3` si existe y si no `curl`.
5. **Plantilla.** `deploy/app.env.example` con la URL interna y el token vacío.
6. **Servidor (equipo).** Mismo token en `yellowdata.env`, `ENV_PRODUCCION` y las variables de CI de
   los dos proyectos; redesplegar.

## Orden de dependencias
El paso 6 depende de que Yellowdata ya tenga el grafo (commit del proyecto `daalrasi/yellowdata`).
Los pasos 1–5 no cambian el comportamiento mientras no existan las variables.
