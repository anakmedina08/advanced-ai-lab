# Plan · SPEC-069 · Corpus de mercado

## Diseño
- **Registro:** `model/mercado/aseguradoras.toml` + `registro.py`. Valida al cargar, indexa por id y
  detecta las aseguradoras nombradas comparando frases normalizadas.
- **Reglas genéricas:** `secciones.py`, para alcance (empresas, blog, legales, portales fuera),
  prioridad (páginas de producto primero) y sección (ruta y título).
- **Contactos:** `contactos.py` extrae el WhatsApp de los enlaces publicados, normaliza números de
  Colombia y arma el enlace de traspaso `wa.me`.
- **Pipeline:** `controller/mercado.py`, con `descubrir` (también sirve de verificación),
  `capturar` (reutiliza `BronzeFetcher`) y `procesar` (reutiliza `clean` y `gold`, por
  aseguradora). `chunks_mercado()` une el corpus principal etiquetado y el de mercado.
- **Búsqueda:** `RecuperadorHibrido.buscar(..., aseguradora=)` y `Fragmento.aseguradora` (campo con
  valor por defecto: compatible).
- **API:** `mercado.*` en JSON-RPC, más `deps.get_mercado` para inyectar el buscador en pruebas.
- **CLI:** `sb mercado listar|verificar|capturar|procesar|buscar|comparar`, y `make mercado`.

## Decisiones
Ver ADR-028: corpus aparte, reglas genéricas, BM25 primero, WhatsApp solo de las páginas oficiales
y traspaso en vez de automatizar conversaciones con terceros.

## Contrato
- Nuevo: `mercado.aseguradoras`, `mercado.buscar`, `mercado.comparar`.
- `clasificador.clasificar` suma el campo `aseguradoras` (aditivo).
- Los fragmentos de `conocimiento.buscar` no cambian de forma.

## Riesgos
- **Sitios sin sitemap o con `robots.txt` restrictivo:** se informan en `verificar` y se omiten.
- **Dominios del registro desactualizados:** `verificado = false` hasta correr `verificar`.
- **Sitios armados con JavaScript** (contenido vacío sin navegador): quedan como «descartadas por
  cortas»; si son muchas, se evalúa capturar con navegador en otra spec.

## Alternativas descartadas
Corpus único, reglas por sitio y bots que conversan con terceros (ver ADR-028).

## Estrategia de pruebas
Sitios falsos en memoria, sin red: robots, sitemap, alcance, captura, Gold y WhatsApp. Tablas
`parametrize` para alcance, secciones, números y detección. RPC con `dependency_overrides`.
