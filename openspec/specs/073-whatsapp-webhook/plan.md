# Plan · SPEC-073

1. **Modelo** `model/whatsapp.py`: `suscripcion_valida`, `firma_valida`, `mensajes`, `canal_de`,
   `codigo_en`, `para_whatsapp` y `ClienteGraph` (httpx). `model/acceso.py`: vínculo canal → código
   (`vincular`, `consumir_canal`, `desvincular`).
2. **Controlador** `controller/whatsapp.py`: `atender` (deduplicar, activar código, olvidar, exigir
   cupo, agente, formato) y `enviador_por_defecto`.
3. **Vista**: `GET` y `POST /whatsapp/webhook` (firma, 200 rápido y `BackgroundTasks`);
   dependencia `get_whatsapp` reemplazable en pruebas.
4. `make tunel` (cloudflared) para probar desde el computador; `.env.example` con las variables.
5. Pruebas `tests/test_whatsapp.py` y `make check`.
