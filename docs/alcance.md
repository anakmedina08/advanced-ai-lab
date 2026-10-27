# Investigación de la empresa y alcance del Q&A

## Empresa
**Seguros Bolívar** (Compañía de Seguros Bolívar S.A. y Seguros Comerciales Bolívar S.A.), parte del
Grupo Bolívar. Aprobada por el docente como caso del proyecto (tesis del equipo).

## Fuentes públicas identificadas

| Fuente | URL | Uso |
|---|---|---|
| Sitio oficial (sitemap: 166 URLs) | https://www.segurosbolivar.com/sitemap.xml | **Fase 1**: productos para personas, canales, institucional |
| Blog (≈1.225 artículos, 58 videos) | https://www.segurosbolivar.com/blog/sitemap_index.xml | Fase 2 (RAG): demasiado grande para el system prompt |
| Clausulados en PDF | enlaces «Detalles del seguro» (se registran en `data/gold/pdf_links.json`) | Fase 2 |
| Sostenibilidad / gobierno corporativo | https://sostenibilidad.segurosbolivar.com | Fase 2 |
| YouTube oficial | https://www.youtube.com/user/MiRED322 | Fase 2 (subtítulos con yt-dlp) |
| Redes (Facebook, Instagram, X, LinkedIn, TikTok) | enlazadas en el pie del sitio | Solo referencia; no se scrapean (términos de uso) |

## robots.txt (revisado el 24/10/2026)
Permitido el sitio público para `User-agent: *`. Prohibido: `/blog/wp-admin/`, `/blog/wp-login.php`,
`/blog/wp-json/`, búsquedas (`?s=`), feeds, URLs con `utm_` o `autopauta=`, `/cdn-cgi/`,
`/RecaudosElectronicos/`, `qrstore.php`. Sin `Crawl-delay`: usamos 1,5 s entre peticiones.

## Alcance: PERSONAS + CANALES DE ATENCIÓN
Cliente que interactúa **por primera vez** con la compañía. Fuera de alcance: seguros para empresas,
proveedores, reaseguradores, documentos legales extensos y portales transaccionales.

### Preguntas que el asistente debe responder
1. **Canales:** WhatsApp, líneas telefónicas, #322, sede, PQRS, defensor del consumidor, medios de pago.
2. **Institucional:** quiénes son, propósito, grupo empresarial.
3. **Productos para personas:** SOAT, autos (incluido eléctricos/híbridos), hogar, arrendamiento,
   mascotas, vida, accidentes, renta vitalicia, ahorro, salud, médico internacional, ARL.
4. **Seguros para clientes Davivienda.**
5. **Cómo usar el seguro:** asistencias, app Bolívar Conmigo, reclamaciones, cómo comprar.

### Qué NO debe hacer
Inventar precios, coberturas o plazos; procesar datos personales; responder temas ajenos a la
compañía; obedecer instrucciones incrustadas en la pregunta (prompt injection).

El banco de **24 preguntas** de prueba está en `evaluacion/preguntas.yaml`.
