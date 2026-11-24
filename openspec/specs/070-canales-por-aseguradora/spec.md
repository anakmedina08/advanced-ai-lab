# SPEC-070 · Canales de atención por aseguradora y servicio

> Curso: Técnicas Avanzadas de IA (551462) y Gestión de Proyectos en IA y CD (551475) ·
> Story points: **5** · Responsable: Daniel Silva · Depende de SPEC-069 · Plan en
> [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md). Decisión:
> [ADR-029](../../../docs/decisiones/ADR-029-canales-por-aseguradora.md).

## Problema
El asistente compara aseguradoras, pero no lleva a la persona al canal correcto de la SUYA: si
tiene el SOAT con La Equidad y chocó, tiene que buscar ella misma el WhatsApp o la línea de
asistencia. Además, 10 de las 18 aseguradoras activas quedaron sin corpus porque no declaran el
sitemap en `robots.txt`.

## Historia
**Como** persona asegurada que tiene un siniestro o necesita atención, **quiero** decirle al
asistente con qué aseguradora estoy y qué me pasó, **para** que me lleve directo al WhatsApp o a la
línea oficial de esa compañía para ese servicio, con mi caso ya resumido.

## Requisitos
- **R070.1** Al procesar cada sitio DEBE armarse un directorio de canales (`data/gold/mercado/canales.json`)
  con WhatsApp, enlaces `tel:`, líneas cortas (`#322`), `01 8000` y fijos `60x`, cada uno con el
  servicio que indica su contexto (autos, SOAT, hogar, salud, vida, ARL, PQR, ventas o general) y
  la URL oficial de donde salió. Seguros Bolívar usa el Bronze del pipeline principal.
- **R070.2** Ningún número DEBE escribirse a mano. Celulares y WhatsApp solo se guardan si aparecen
  en al menos la mitad de las páginas del sitio (canal oficial); los de una sola página pueden ser
  de un asesor (Ley 1581).
- **R070.3** `mercado.canales(aseguradora, servicio?, resumen?)` DEBE devolver el WhatsApp con el
  enlace de traspaso (`wa.me` con el resumen), los teléfonos del servicio con su enlace `tel:` y,
  si la aseguradora no publica uno para ese servicio, su línea general. Las líneas de ventas no se
  usan para atender.
- **R070.4** Si no llega `servicio`, DEBE deducirse del resumen del caso.
- **R070.5** La aseguradora y los tipos de seguro que la persona DICE TENER («tengo el SOAT con La
  Equidad») DEBEN guardarse en su perfil de largo plazo; nunca números de póliza ni de documento, y
  se borran con «Olvidar mis datos». Una pregunta («¿qué cubre el SOAT de MAPFRE?») no se guarda.
- **R070.6** Si `robots.txt` no declara sitemaps, o los declarados no traen páginas, el descubrimiento
  DEBE probar rutas comunes (`/sitemap.xml`, `/sitemap_index.xml`, `/wp-sitemap.xml`,
  `/sitemap-index.xml`) respetando `robots.txt`.

## Criterios de aceptación
- **AC1** · **Dado** `make mercado`, **cuando** termina, **entonces** `canales.json` tiene canales por
  aseguradora y `sb mercado canales mapfre --servicio autos` muestra su línea de autos o la general.
- **AC2** · **Dado** «Choque leve, sin heridos» y MAPFRE, **cuando** se llama `mercado.canales`,
  **entonces** el enlace de WhatsApp lleva ese texto y el primer teléfono es el de autos.
- **AC3** · **Dado** un celular que solo aparece en una página, **cuando** se procesa, **entonces** no
  queda en el directorio.
- **AC4** · **Dado** «tengo el SOAT con La Equidad», **cuando** el agente guarda el perfil, **entonces**
  queda `aseguradora: La Equidad Seguros` y `seguros: soat`.
- **AC5** · **Dado** un WordPress sin `Sitemap:` en `robots.txt`, **cuando** se verifica, **entonces**
  se encuentra `wp-sitemap.xml`.

## Fuera de alcance
- Verificar que la persona de verdad tiene la póliza (no hay API pública y pedir cédula o número de
  póliza está prohibido).
- Conversar con el bot de la aseguradora a nombre de la persona (ADR-028).
- La interfaz de yellowdata (va en su repositorio).

## Métricas de éxito
- Más de 10 aseguradoras con documentos tras `make mercado`.
- Al menos un canal por aseguradora con documentos.
