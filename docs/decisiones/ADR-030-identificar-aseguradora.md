# ADR-030 · Identificar la aseguradora con pistas y documentos leídos en memoria, sin LLM

- **Fecha:** 2026-11-19
- **Categoría:** producto · datos · ética
- **What:**
  - El agente atiende con todas las aseguradoras del registro: compara lo que publican, identifica
    la de la persona y la lleva a su canal oficial (tools `comparar_aseguradoras`,
    `identificar_aseguradora` y `canales_aseguradora`).
  - La aseguradora se identifica con lo que la persona tiene a mano: pistas escritas o un
    documento (recibo de pago, carátula, extracto, certificado) leído con OCR local.
- **Why:**
  - **No hay fuente pública de afiliación.** No existe una API ni un MCP de pólizas en Colombia; el
    RUNT muestra la aseguradora del SOAT, pero solo para vehículos y detrás de un captcha que no se
    automatiza. Y el seguro puede ser de cualquier tipo (hogar, vida, salud, ARL, exequias).
  - **El documento lo tiene la persona** y dice la razón social de la aseguradora y su dominio.
    Leerlo en el servidor, en memoria y con Tesseract, no gasta tokens ni manda la imagen a un
    tercero. Solo sale el nombre del registro; la cédula, la póliza y la dirección que trae el
    documento nunca salen ni se guardan (Ley 1581).
  - **Señales simples e interpretables** (nombre y dominio) en lugar de un modelo: se pueden
    explicar a la persona («encontré el dominio mapfre.com.co») y probar caso por caso.
  - **No adivinar:** con empate o sin señales, el asistente pregunta en vez de elegir.
- **Alternativas descartadas:**
  - Claude Vision sobre el documento: más preciso con fotos malas, pero manda un documento con
    datos personales a un tercero y gasta tokens en cada consulta pública.
  - Consultar el RUNT o a la aseguradora con la cédula: datos personales y captcha.
  - Mapear bancos a aseguradoras («si lo compró en el banco X es la aseguradora Y»): las alianzas
    cambian y un banco vende seguros de varias compañías.
- **Where:**
  - `src/sb_asistente/model/mercado/identificar.py` y `lectura.py`
  - `controller/mercado.py`, `model/agente.py`, `model/router.py`, `controller/agente.py`
  - `view/rpc.py` (`mercado.identificar`), `view/api.py` (`POST /aseguradoras/identificar`) y `view/cli.py`
  - skill `.claude/skills/identificar-aseguradora/` y pruebas en `tests/test_identificar.py`
- **Learned:**
  - «Bolívar» en un recibo casi siempre es una dirección: los alias de una palabra que son lugares
    no cuentan en documentos.
  - El dominio del correo de notificaciones es la pista más confiable que la persona suele tener.
