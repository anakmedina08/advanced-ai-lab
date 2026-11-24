# Plan · SPEC-075

1. `deploy/preparar-servidor.sh`: Docker oficial, usuario `deploy`, ufw (22/80/443), SSH solo con
   llave y swap. Se ejecuta una vez como root.
2. `deploy/docker-compose.prod.yml` + `deploy/Caddyfile`: API y frontend internos, Caddy con HTTPS
   automático. Dominio por defecto `<ip-con-guiones>.sslip.io` (sin DNS).
3. `deploy/desplegar.sh`: login con el token por stdin, `pull`, `up -d`, espera a *healthy*, logout.
4. `.gitlab-ci.yml`: `build_api`, `build_frontend` (Docker-in-Docker) y `deploy` (Alpine + SSH).
5. `opencode.json` con el MCP de GitLab y guía `docs/despliegue.md` (servidor, variables, `glab`).
6. Pruebas `tests/test_despliegue.py`.
