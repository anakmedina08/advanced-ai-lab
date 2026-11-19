# Plan · SPEC-070 · Canales por aseguradora

## Diseño
- `model/mercado/canales.py`:
  - `canales_de_html` lee los canales de una página (enlaces, texto y servicio por contexto: título
    de la sección, enlace y bloque padre);
  - `agregar_canales` une las páginas y aplica la regla de privacidad;
  - `elegir` toma el mejor WhatsApp y los mejores teléfonos para un servicio (específico > general,
    nunca ventas);
  - `enlace_telefono` arma el URI `tel:`.
- `controller/mercado.py`:
  - `procesar` escribe `canales.json`, también para Seguros Bolívar desde su Bronze;
  - `canales_para` arma la respuesta con el enlace `wa.me`;
  - descubrimiento con rutas comunes de sitemap.
- `model/memoria.py`: `extraer_aseguradora` guarda en el perfil la aseguradora y los seguros que la
  persona dice tener.
- `view/rpc.py`: `mercado.canales`. `view/cli.py`: `sb mercado canales <id> [--servicio] [--resumen]`.

## Decisiones
ADR-029: la afiliación la declara la persona, los canales salen solo de los sitios oficiales y la
regla de privacidad aplica a los celulares.

## Riesgos
- **El contexto de un número puede ser ambiguo:** si no se reconoce el servicio queda como
  «general», y eso solo cambia el orden.
- **Sitios que muestran los teléfonos con JavaScript:** no aparecen en el HTML. Se usa la página
  de contacto como respaldo.

## Estrategia de pruebas
HTML local con secciones por servicio, tablas para `servicio_de`, `tel:` y `elegir`, el controlador
con un `canales.json` temporal, RPC con el directorio en memoria, y la memoria con frases de
tenencia frente a preguntas.
