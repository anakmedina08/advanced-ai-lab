# ADR-031 · Códigos de acceso con vencimiento y cupo para lo que gasta tokens

- **Fecha:** 2026-11-19
- **Categoría:** producto · costos · seguridad
- **What:** en el sitio público, todo lo que llama a un LLM exige un código de acceso que genera un
  administrador (`sb acceso crear`), con vencimiento en horas y cupo de mensajes. Lo que corre en
  local (YOLO, OCR, canales, comparar, recomendador) sigue libre.
- **Why:**
  - **Controlar el gasto:** cada mensaje del chat cuesta tokens; un código que vence y se agota
    pone un techo por persona (por ejemplo, el jurado de la sustentación) sin cuentas de usuario.
  - **Sin datos personales:** no hay registro ni correo; el código es lo único que se entrega.
  - **Seguro por diseño:** el código sale de `secrets`, se guarda solo su hash SHA-256 y el consumo
    es un `UPDATE` condicionado (atómico): el cupo no se supera con pestañas en paralelo.
  - **Gastar antes de llamar:** el mensaje se descuenta antes de invocar el modelo; un código sin
    cupo nunca llega al LLM.
  - **Apagado por defecto:** el curso y las pruebas siguen igual; solo el servidor público lo activa.
- **Alternativas descartadas:**
  - Cuentas con usuario y contraseña: más fricción y datos personales que guardar.
  - Límite por IP: se evade con otra red y castiga redes compartidas (universidad, oficina).
  - Un solo token fijo en la página: queda visible en el navegador y no vence.
- **Where:**
  - `src/sb_asistente/model/acceso.py` y `controller/acceso.py`
  - `view/rpc.py` (`usa_llm`, `-32003`, `acceso.estado`), `view/api.py` (`requiere_codigo`,
    `GET /acceso/estado`) y `view/cli.py` (`sb acceso`)
  - pruebas en `tests/test_acceso.py`
- **Learned:**
  - Marcar en el registro de métodos cuál usa el LLM (`usa_llm`) evita olvidar un método nuevo.
