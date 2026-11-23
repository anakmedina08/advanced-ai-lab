# SPEC-075 · Build, Container Registry y deploy al Droplet con HTTPS (Módulo 4, Parte 2)

> Curso: Gestión de Proyectos en IA y CD (551475) · Story points: **8** · Responsable: Daniel
> Silva · Anuncio [008](../../../docs/anuncios/551475-anuncio-008.md) · Historias M4-02 a M4-07 ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md). Decisión:
> [ADR-034](../../../docs/decisiones/ADR-034-despliegue-droplet-caddy.md). Guía:
> [`docs/despliegue.md`](../../../docs/despliegue.md).

## Problema
El pipeline de GitLab (SPEC-074) valida el código, pero el producto no está en línea: la rúbrica del
M4 pide imagen en el Registry, Droplet con firewall, proxy con HTTPS, deploy por SSH con
healthcheck y secretos solo en variables de CI.

## Historia
**Como** equipo, **queremos** que un push a `main` construya las imágenes, las publique en el
Container Registry y las despliegue en el Droplet detrás de HTTPS, **para** que el cambio llegue a
la URL pública sin pasos manuales y con trazabilidad por commit.

## Requisitos
- **R075.1** El pipeline DEBE tener las etapas `lint → test → build → deploy`.
- **R075.2** `build_api` y `build_frontend` DEBEN publicar en `$CI_REGISTRY_IMAGE/{api,frontend}`
  con el tag `$CI_COMMIT_SHORT_SHA`, el de la rama y `latest` en `main`.
- **R075.3** El deploy DEBE ser automático en `main`, manual en `develop` y nunca simultáneo
  (`resource_group`).
- **R075.4** El deploy DEBE conectarse por SSH con llave y `known_hosts` verificados (sin
  `StrictHostKeyChecking=no`), descargar la imagen del commit, reemplazar los contenedores y esperar
  a que la API quede *healthy*; luego DEBE comprobar `https://api.$DOMINIO/health` desde fuera.
- **R075.5** Solo Caddy DEBE publicar puertos (80 y 443) y obtener el certificado automáticamente.
- **R075.6** El servidor DEBE tener un usuario sin contraseña ni sudo para el deploy, firewall con
  22/80/443 y SSH solo con llave.
- **R075.7** La llave SSH, el `known_hosts` y el `.env` de producción DEBEN vivir en variables de CI
  protegidas; el token del Registry DEBE viajar por stdin y la sesión cerrarse tras el `pull`.
- **R075.8** `opencode.json` DEBE declarar el MCP oficial de GitLab.

## Criterios de aceptación
- **AC1** · **Dado** un push a `main`, **cuando** termina el pipeline, **entonces** las imágenes con
  el SHA están en el Registry y `https://$DOMINIO` sirve la versión nueva con certificado válido.
- **AC2** · **Dado** que la API no queda *healthy* en 180 s, **cuando** corre `deploy`, **entonces**
  el job falla y muestra los últimos registros.
- **AC3** · `opencode mcp list` muestra `gitlab` *connected* y `glab auth status` está autenticado.

## Fuera de alcance
Descarga del modelo YOLO desde Generic Packages (la imagen no incluye el extra de visión),
despliegue sin caída con dos réplicas y MLflow en el Droplet.
