# ADR-028 · Corpus de mercado: varias aseguradoras en un corpus aparte

- **Fecha:** 2026-11-18
- **Categoría:** arquitectura · datos
- **What:** se agrega un **corpus de mercado** con la información pública de varias aseguradoras
  de Colombia (SURA, Allianz, Seguros del Estado, MAPFRE, HDI, AXA Colpatria y otras):
  - **Registro configurable:** `src/sb_asistente/model/mercado/aseguradoras.toml`. Sumar una
    aseguradora es agregar un bloque y correr `make mercado`.
  - **Mismo Medallion, por aseguradora:** `data/{raw,silver,gold}/mercado/<id>/`. La cortesía es la
    de la Fase 1: `robots.txt`, `sitemap`, User-Agent identificable y 1,5 s entre peticiones.
    Además hay un tope de páginas por aseguradora (`MERCADO_MAX_PAGINAS`, 80 por defecto), que se
    llena primero con las páginas de producto.
  - **Reglas genéricas** de alcance y sección (`model/mercado/secciones.py`), con las mismas
    secciones del corpus principal.
  - **WhatsApp oficial:** sale de los enlaces `wa.me` / `api.whatsapp.com` que cada aseguradora
    publica en su propio sitio. Ningún número se escribe a mano.
  - **Búsqueda y comparación:** el buscador híbrido acepta `aseguradora` como filtro. Los métodos
    nuevos son `mercado.buscar`, `mercado.comparar` y `mercado.aseguradoras`.
    `clasificador.clasificar` devuelve además las aseguradoras que nombra el mensaje.
- **Why:**
  - El producto pasa de responder sobre una aseguradora a **orientar entre varias**: comparar
    coberturas y decir a cuál acudir y por qué canal.
  - **Corpus aparte y no mezclado con el principal.** El modo de contexto completo de la Fase 1
    (ADR-001) mete todo el corpus de Seguros Bolívar en el prompt (~36K tokens). Con 20 aseguradoras
    no cabría, y cambiaría las respuestas y las evaluaciones ya medidas. El corpus principal queda
    igual; el de mercado se consulta por recuperación.
  - **Seguros Bolívar no se vuelve a capturar:** su corpus es el del pipeline principal y aquí solo
    se etiqueta con `aseguradora = "seguros-bolivar"`.
  - **Reglas genéricas y no una por sitio:** escribir y mantener reglas para 20 sitios no escala.
    Las palabras de la ruta y del título («soat», «hogar», «canales-de-atencion») significan lo
    mismo en todos.
  - **Portales transaccionales fuera:** el alcance genérico excluye cotizar, comprar, pagar, PSE,
    radicar o reportar un siniestro, formularios y oficinas virtuales; solo entran páginas
    informativas. El descubrimiento también hace la pausa de `REQUEST_DELAY_S` entre cada petición
    (robots.txt y sitemaps), no solo la captura.
  - **El plan se reescribe en cada verificación**, también cuando queda vacío: si hoy `robots.txt`
    no responde, `capturar` no descarga las URLs del plan de ayer. Los sitemaps hijos solo se piden
    si son del mismo sitio y `robots.txt` los permite.
  - **Sin `robots.txt` legible, no se captura.** Un 404 significa que el sitio no pone
    restricciones (estándar de robots); cualquier otro error significa que no se sabe qué permite.
- **Límites (explícitos en la interfaz):**
  - Se compara lo que cada compañía **publica** (coberturas, requisitos, canales). Los precios casi
    nunca son públicos y la cobertura real depende de cada póliza. Por eso la respuesta es
    «posiblemente cubierto según su página pública», no «está cubierto».
  - El recomendador de Gestión sigue entrenado con el catálogo sintético de una sola compañía. Entre
    aseguradoras se informa quién **ofrece** el tipo de seguro, no un ranking de calidad.
- **Alternativas descartadas:**
  - **Meter todo en el corpus principal:** rompe el modo de contexto completo y las evaluaciones de
    la Fase 1.
  - **Reglas de sección por sitio:** demasiado mantenimiento para un registro que debe crecer.
  - **Que el agente converse por WhatsApp con el bot de cada aseguradora a nombre del cliente:**
    exigiría hacerse pasar por la persona con su cédula y su póliza (Ley 1581 y nuestra regla de
    solo datos públicos). Radicar un siniestro por otro requiere un mandato y, en algunos casos,
    ser intermediario autorizado por la Superfinanciera. Las políticas de WhatsApp Business tampoco
    permiten que una empresa le escriba a otra sin la autorización (opt-in) del usuario. En su
    lugar, la interfaz arma un **enlace de traspaso**
    (`wa.me/<número oficial>?text=<resumen del caso>`) que la persona abre y envía desde su cuenta.
  - **Índice vectorial del mercado desde el día uno:** se empieza con BM25, que no depende de
    Ollama. Los embeddings del mercado quedan para cuando el corpus esté estable.
- **Where:**
  - `src/sb_asistente/model/mercado/` (`registro.py`, `secciones.py`, `contactos.py`, `comparar.py`,
    `aseguradoras.toml`)
  - `src/sb_asistente/controller/mercado.py`
  - `src/sb_asistente/model/rag/hibrido.py` (filtro `aseguradora`)
  - `src/sb_asistente/view/rpc.py`, `view/dependencias.py`, `view/cli.py` (`sb mercado …`) y
    `Makefile` (`make mercado`)
  - `src/sb_asistente/controller/herramientas.py`: la CLI y la API dejan de importar el modelo
    directamente (skills, índice y evaluación del RAG, trazas, MLflow), como exige el MVC
  - pruebas en `tests/test_mercado.py` y `tests/test_rpc.py`
- **Recuperación sin cambios:** el filtro `aseguradora` es opcional. `sb rag evaluar` da el mismo
  resultado antes y después (BM25: hit@3 = 13/21, hit@6 = 16/21).
- **Learned:**
  - `normalize_words` quita las palabras vacías («del», «la»), así que la detección compara frases
    ya normalizadas. Por la misma razón, palabras comunes solas («positiva», «estado», «aurora»)
    no sirven como alias: darían falsos positivos.
  - Liberty Seguros se fusionó con HDI: queda como alias de HDI y no como otra aseguradora.
