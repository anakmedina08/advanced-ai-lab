# Plan · SPEC-076

1. Repositorio `yellowdata`: `Dockerfile` (Next.js standalone, Node 22), `.dockerignore`,
   `.gitlab-ci.yml` (build y push de `:SHA` y `:latest`), `output: "standalone"` solo con
   `NEXT_STANDALONE=1` para no romper `next start` en cPanel.
2. Este repositorio: servicio `yellowdata` en `deploy/docker-compose.prod.yml`, sitio `app.` en el
   `Caddyfile`, CORS para `app.` y verificación HTTPS de las tres URL en el job `deploy`.
3. GitLab: proyecto `daalrasi/yellowdata` con `advanced-ai-lab` en la lista de *job token*.
