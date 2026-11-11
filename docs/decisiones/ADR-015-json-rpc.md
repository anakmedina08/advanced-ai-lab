# ADR-015 · JSON-RPC 2.0 sobre FastAPI

- **Fecha:** 2026-11-07
- **What:** `POST /rpc` (`view/rpc.py`) expone los procedimientos del producto: `sistema.salud`, `conocimiento.buscar`, `asistente.preguntar`, `asistente.chat`, `agente.conversar|historial|olvidar`, `recomendador.recomendar|por_perfil`, `clasificador.clasificar`, `skills.listar` y `rpc.descubrir`. Los parámetros de cada método son modelos Pydantic; hay lotes (máx. 10), notificaciones y los códigos de error del estándar (-32700 a -32603) más -32001 (no encontrado) y -32002 (datos no listos). El front de yellowdata.com.co llama por RPC; los endpoints REST siguen para `/docs` y compatibilidad.
- **Why:** recomendación del curso. Un front que invoca acciones («conversar», «recomendar») se modela mejor como procedimientos que como recursos; un solo endpoint simplifica el proxy del sitio y el registro de eventos. Se eligió JSON-RPC y no gRPC porque el navegador y cPanel no necesitan proxy ni protobuf.
- **Where:** `view/rpc.py`, `view/dependencias.py` (inyección compartida con REST), `tests/test_rpc.py`, `lib/asistente.ts` del sitio.
- **Learned:** los handlers del LLM corren en `run_in_threadpool` para no bloquear el event loop. Los errores internos nunca devuelven su detalle (puede incluir claves). gRPC queda como opción para comunicación entre servicios internos si se separan las APIs.
