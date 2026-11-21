# ADR-034 · Despliegue en un Droplet con Docker Compose, Caddy y deploy por SSH desde GitLab

- **Fecha:** 2026-11-21
- **Categoría:** infraestructura · CI/CD · seguridad
- **What:** GitLab construye dos imágenes (API y frontend), las publica en su Container Registry con
  el SHA del commit y un job `deploy` entra por SSH al Droplet (Ubuntu 24.04, 2 GB) para hacer
  `docker compose pull && up -d`. Caddy es el único servicio expuesto y obtiene el certificado de
  Let's Encrypt solo. Dominio: `<ip-con-guiones>.sslip.io`, cambiable por variable.
- **Why:**
  - **Caddy** y no Nginx + Certbot: HTTPS automático y renovación sin cron ni pasos extra.
  - **sslip.io**: resuelve cualquier IP sin tocar DNS; un subdominio propio queda a una variable.
  - **Tag por SHA**: cada contenedor en producción se rastrea hasta su commit y su pipeline.
  - **Usuario `deploy` sin sudo** y llave solo en una variable protegida: el grupo docker equivale a
    root, así que la llave no sale de GitLab. `known_hosts` fijo: no se acepta cualquier servidor.
  - **Token del Registry por stdin** y `docker logout` al terminar: no queda en disco ni en `ps`.
  - Plan de 2 GB: con 512 MB o 1 GB la API se queda sin memoria; el costo es por hora y el Droplet
    se destruye después de la sustentación.
- **Alternativas descartadas:**
  - App Platform de DigitalOcean: la rúbrica pide Droplet, proxy y SSH.
  - Kubernetes: desproporcionado para un servicio y un integrante a cargo.
  - Watchtower (pull automático): el deploy dejaría de ser trazable desde el pipeline.
- **Where:** `deploy/`, `.gitlab-ci.yml`, `opencode.json`, `tests/test_despliegue.py`,
  `docs/despliegue.md`.
