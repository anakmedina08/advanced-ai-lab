# SPEC-069 · Corpus de mercado: varias aseguradoras, comparación y canales

> Curso: Técnicas Avanzadas de IA (551462) y Gestión de Proyectos en IA y CD (551475) ·
> Story points: **8** · Responsable: Daniel Silva · Plan en [`plan.md`](plan.md); tareas en
> [`tasks.md`](tasks.md). Decisión: [ADR-028](../../../docs/decisiones/ADR-028-corpus-mercado-aseguradoras.md).

## Problema
El asistente solo conoce la información pública de Seguros Bolívar. Una persona que quiere saber
qué aseguradora le conviene, comparar coberturas o encontrar el canal de atención de su compañía no
recibe respuesta. El sitio público (yellowdata) necesita además el WhatsApp oficial de cada
aseguradora, para pasarle el caso a la persona correcta.

## Historia
**Como** persona que busca un seguro o tiene un siniestro, **quiero** que el asistente compare la
información pública de varias aseguradoras y me diga por qué canal atenderme, **para** decidir con
fuentes oficiales y no perder tiempo buscando en cada sitio.

## Requisitos
- **R069.1** El registro de aseguradoras DEBE vivir en un solo archivo (`aseguradoras.toml`) y
  validarse al cargar: ids únicos, sitio https y prefijo con «/». Sumar una aseguradora NO DEBE
  requerir cambios de código.
- **R069.2** El scraping de cada aseguradora DEBE respetar su `robots.txt` (sin `robots.txt`
  legible, salvo 404, no se captura), usar sus sitemaps, quedarse en su dominio y aplicar el
  alcance PERSONAS + CANALES, con un tope de páginas por aseguradora.
- **R069.3** Cada chunk Gold del mercado DEBE llevar `aseguradora` y una sección del mismo
  vocabulario del corpus principal.
- **R069.4** El corpus principal (Seguros Bolívar) NO DEBE cambiar; en el mercado se reutiliza
  etiquetado como `seguros-bolivar`.
- **R069.5** El WhatsApp de cada aseguradora DEBE salir de sus propias páginas (enlaces `wa.me` /
  `api.whatsapp.com`), nunca escrito a mano, y solo con números de Colombia.
- **R069.6** El buscador híbrido DEBE aceptar el filtro `aseguradora`, sin cambiar el
  comportamiento cuando no se usa.
- **R069.7** La API DEBE exponer `mercado.aseguradoras`, `mercado.buscar` y `mercado.comparar`
  (máximo 8 aseguradoras); `clasificador.clasificar` DEBE devolver las aseguradoras que nombra el
  mensaje.
- **R069.8** Solo información pública: el pipeline NO DEBE guardar ni procesar datos de clientes
  (Ley 1581).

## Criterios de aceptación
- **AC1** · **Dado** el registro, **cuando** se corre `uv run sb mercado verificar`, **entonces**
  cada aseguradora activa muestra cuántas URLs del sitemap se capturarían, o por qué no.
- **AC2** · **Dado** un sitio con una ruta prohibida en `robots.txt`, **cuando** se descubre,
  **entonces** esa URL queda descartada con motivo «robots.txt».
- **AC3** · **Dado** `make mercado`, **cuando** termina, **entonces** `data/gold/mercado/chunks.jsonl`
  tiene chunks con `aseguradora` y `resumen.json` trae el WhatsApp encontrado por aseguradora.
- **AC4** · **Dado** «¿El hogar de Sura cubre lo mismo que Allianz?», **cuando** se clasifica,
  **entonces** `aseguradoras = ["sura", "allianz"]`.
- **AC5** · **Dado** `mercado.comparar` con tres aseguradoras, **cuando** una no publica nada sobre
  la consulta, **entonces** aparece al final y sin fragmentos.
- **AC6** · **Dado** el repositorio, **cuando** se corre `make check`, **entonces** pasan las
  pruebas nuevas y las existentes.

## Fuera de alcance
- Precios y cotizaciones (no son públicos).
- Conversar con el bot de WhatsApp de otra aseguradora a nombre del cliente (ver ADR-028).
- Índice vectorial del mercado (por ahora, BM25).
- La interfaz de yellowdata (va en su propio repositorio).

## Métricas de éxito
- Al menos 10 aseguradoras con documentos tras `make mercado`.
- 0 URLs capturadas que su `robots.txt` prohíba.
- +100 pruebas.
