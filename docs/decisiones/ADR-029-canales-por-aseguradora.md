# ADR-029 · Canales por aseguradora: afiliación declarada y canales leídos de los sitios oficiales

- **Fecha:** 2026-11-19
- **Categoría:** producto · datos · ética
- **What:** el asistente lleva a la persona al canal oficial de SU aseguradora para lo que
  necesita: el WhatsApp con el resumen del caso ya escrito y la línea del servicio (autos, SOAT,
  hogar, salud, ARL…) o, si no hay, la línea general.
  - La aseguradora la **declara** la persona y queda en su perfil de largo plazo.
  - Los canales salen de las páginas oficiales capturadas (`canales.json`).
  - El descubrimiento prueba rutas comunes de sitemap cuando `robots.txt` no las declara.
- **Why:**
  - **No se puede verificar la afiliación.** Ninguna aseguradora ofrece una API pública para
    consultar pólizas, y pedir cédula o número de póliza va contra la regla de solo datos públicos
    (la API ya los rechaza). Lo honesto es preguntar y recordar lo que la persona dice, con la
    opción de olvidarlo.
  - **Ningún número escrito a mano** (decisión del equipo): un número copiado a mano se desactualiza
    sin que nadie lo note. Leído del sitio, cada canal trae la URL donde se publica y se renueva con
    `make mercado`.
  - **Regla de privacidad:** un celular o WhatsApp que aparece en una sola página puede ser de un
    asesor (dato personal). Solo se guardan los que aparecen en al menos la mitad de las páginas,
    como el canal del encabezado o del pie. Líneas cortas, `01 8000` y fijos son institucionales.
  - **Líneas de ventas fuera:** una línea para cotizar no atiende un siniestro.
  - **Rutas comunes de sitemap:** 10 de 18 aseguradoras no declaran el sitemap en `robots.txt`.
    Probar `/sitemap_index.xml` o `/wp-sitemap.xml` es lo que haría una persona, y siempre se
    respeta `robots.txt`.
- **Alternativas descartadas:**
  - Directorio de números curado a mano: más cobertura, pero se desactualiza.
  - Verificar la póliza con datos personales: prohibido por la Ley 1581 y la regla del proyecto.
- **Where:**
  - `src/sb_asistente/model/mercado/canales.py` y `controller/mercado.py` (`canales_para`,
    `canales_de_bronze` y las rutas comunes)
  - `model/memoria.py` (`extraer_aseguradora`), `view/rpc.py` (`mercado.canales`) y `view/cli.py`
  - pruebas en `tests/test_canales.py`, `tests/test_mercado.py` y `tests/test_rpc.py`
- **Learned:**
  - El servicio de un teléfono está en el título de su sección más que en el enlace. Por eso el
    contexto suma el título anterior, el texto del enlace y el bloque padre.
  - Una frase con «tengo», «mi póliza» o «estoy asegurado» distingue tenencia de pregunta.
