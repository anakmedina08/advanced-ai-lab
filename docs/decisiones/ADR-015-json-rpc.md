# ADR-015 · JSON-RPC 2.0 sobre FastAPI

- **Fecha:** 2026-11-07
- **What:** `POST /rpc` (`view/rpc.py`) expone los procedimientos del producto: `sistema.salud`, `conocimiento.buscar`, `asistente.preguntar`, `asistente.chat`, `agente.conversar|historial|olvidar`, `recomendador.recomendar|por_perfil`, `clasificador.clasificar`, `skills.listar` y `rpc.descubrir`. Los parámetros de cada método son modelos Pydantic; hay lotes (máx. 10), notificaciones y los códigos de error del estándar (-32700 a -32603) más -32001 (no encontrado) y -32002 (datos no listos). El front de yellowdata.com.co llama por RPC; los endpoints REST siguen para `/docs` y compatibilidad.
- **Why:** recomendación del curso. Un front que invoca acciones («conversar», «recomendar») se modela mejor como procedimientos que como recursos; un solo endpoint simplifica el proxy del sitio y el registro de eventos. Se eligió JSON-RPC y no gRPC porque el navegador y cPanel no necesitan proxy ni protobuf.
- **Where:** `view/rpc.py`, `view/dependencias.py` (inyección compartida con REST), `tests/test_rpc.py`, `lib/asistente.ts` del sitio.
- **Alternativas evaluadas (actualizado 2026-11-18, SPEC-068):** RPC es un **estilo de contrato** y FastAPI un **servidor HTTP**; no compiten. La pregunta real era sobre qué servidor montar el RPC:

  | Opción | Ventaja | Por qué no (o por qué sí) |
  |---|---|---|
  | **JSON-RPC sobre FastAPI** (elegida) | Reutiliza los modelos Pydantic, la inyección con `Depends`, `TestClient` y el mismo proceso que REST | Un solo despliegue, un solo puerto y una sola validación; el curso pide FastAPI en el módulo 3 |
  | Servidor JSON-RPC aparte (`jsonrpcserver`, `xmlrpc.server`) | Menos código de despacho | Duplica la validación y la inyección de dependencias; `xmlrpc` además expone tipos sin esquema |
  | gRPC (`grpcio` + protobuf) | Tipado fuerte y streaming binario | El navegador necesita gRPC-Web y un proxy (Envoy), que el hosting del sitio no permite |
  | Solo REST | Documentación automática en `/docs` | Las acciones («conversar», «olvidar», «recomendar») no son recursos; se quedan como compatibilidad |

  El despachador (`rpc.ejecutar`) no depende de FastAPI, así que puede moverse a otro transporte (por ejemplo WebSocket o un adaptador de WhatsApp o Telegram) sin cambiar los métodos. Sus pruebas tabuladas están en `tests/test_esquemas_rpc_casos.py`.
- **Learned:** los handlers del LLM corren en `run_in_threadpool` para no bloquear el event loop. Los errores internos nunca devuelven su detalle (puede incluir claves). gRPC queda como opción para comunicación entre servicios internos si se separan las APIs.
