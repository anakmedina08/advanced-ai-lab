# ADR-013 · Chat orquestado: clasificador de intención antes del LLM

- **Fecha:** 2026-11-06
- **What:** `POST /chat` (`controller/chat.py`) resuelve cada turno en pasos: el clasificador por reglas (`model/intencion.py`) detecta intención, sección y perfil; luego llama al Q&A con fuentes, al recomendador (por cliente sintético o por el perfil descrito, `recomendar_por_perfil`) o a una respuesta fija. Cada paso queda en la `traza` que muestra el front (yellowdata.com.co/casos/asistente-seguros/chat) y cada turno publica un evento «Chat» en el panel de agentes, sin el texto del usuario.
- **Why:** saludos y temas ajenos no gastan tokens (saldo inicial de 10 USD); el recomendador funciona en un chat público sin pedir identificación; la traza hace visible el flujo agéntico del producto, no solo el del desarrollo.
- **Where:** `model/intencion.py`, `controller/chat.py`, `controller/recomendador.py`, `view/api.py`, `view/schemas.py` (`ChatIn`, `ChatOut`), `sb chat`.
- **Learned:** ante la duda el clasificador envía al Q&A, que ya tiene la respuesta de no-información; así un falso «fuera de alcance» no bloquea preguntas válidas. El clasificador por reglas es la línea base de T-27: el modelo entrenado debe superarlo en el mismo banco.
