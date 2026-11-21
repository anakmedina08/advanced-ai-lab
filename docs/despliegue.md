# Despliegue en el Droplet (SPEC-075)

Flujo: push a `main` en GitHub → espejo a GitLab → `lint` → `test` → `build_api` / `build_frontend`
(Container Registry) → `deploy` (SSH al Droplet) → `https://<DOMINIO>` (Yellowdata),
`https://app.<DOMINIO>` (panel del equipo) y `https://api.<DOMINIO>` (API).
Decisión: [ADR-034](decisiones/ADR-034-despliegue-droplet-caddy.md).

## 1. Preparar el servidor (una vez)
Desde el Mac, en la raíz del repositorio:

```bash
# Llave exclusiva del pipeline (sin frase: la usa un job). La privada solo irá a GitLab.
ssh-keygen -t ed25519 -f ~/.ssh/gitlab_deploy -N "" -C gitlab-deploy

# Docker, usuario deploy, firewall 22/80/443, SSH solo con llave y swap
ssh root@<IP> "sh -s -- '$(cat ~/.ssh/gitlab_deploy.pub)'" < deploy/preparar-servidor.sh

# Prueba de acceso con el usuario de despliegue
ssh -i ~/.ssh/gitlab_deploy deploy@<IP> 'docker ps && ufw status'

# Datos públicos del corpus (no van en la imagen ni en Git)
rsync -az -e "ssh -i ~/.ssh/gitlab_deploy" data/gold data/recomendador deploy@<IP>:/opt/advanced-ai-lab/data/
```

## 2. Variables de CI en GitLab
**Settings → CI/CD → Variables** (todas *Protected*; las ramas `main` y `develop` deben estar en
**Settings → Repository → Protected branches**).

| Clave | Tipo | Valor |
|---|---|---|
| `SSH_KEY` | File | contenido de `~/.ssh/gitlab_deploy` (privada) |
| `SSH_KNOWN_HOSTS` | Variable | salida de `ssh-keyscan -t ed25519 <IP>` |
| `ENV_PRODUCCION` | File | `.env` de producción a partir de `deploy/app.env.example` |
| `DEPLOY_HOST` | Variable | IP del Droplet |
| `DEPLOY_USER` | Variable | `deploy` |
| `DOMINIO` | Variable | `<ip-con-guiones>.sslip.io` o un subdominio propio con registro A |

Las llaves de API van solo en `ENV_PRODUCCION`. `CI_REGISTRY_USER`, `CI_REGISTRY_PASSWORD` y
`CI_JOB_TOKEN` los crea GitLab en cada job.

## 3. Yellowdata (SPEC-076)
Yellowdata vive en su propio proyecto, `gitlab.com/daalrasi/yellowdata`, cuyo pipeline publica
`registry.gitlab.com/daalrasi/yellowdata:latest`. El deploy de este repositorio la descarga.

1. En el proyecto `yellowdata`: **Settings → CI/CD → Job token permissions → Add** →
   `daalrasi/advanced-ai-lab` (sin esto el `pull` falla con *denied*).
2. Variables opcionales de Yellowdata en el servidor: `/opt/advanced-ai-lab/yellowdata.env`.
3. Un cambio solo en Yellowdata se publica con su pipeline y luego ▶ `deploy` aquí.
4. cPanel (`www.yellowdata.com.co`): `ASSISTANT_API_URL=https://api.<DOMINIO>`.

## 4. Desplegar
- `main`: automático al terminar `build`.
- `develop`: botón ▶ del job `deploy` en **Build → Pipelines** (manual).
- Imágenes: **Deploy → Container Registry** (`api` y `frontend`, tags SHA, rama y `latest`).
- Entornos: **Operate → Environments → produccion** muestra el commit desplegado.

## 5. Herramientas de la sustentación
```bash
# GitLab CLI
brew install glab
glab auth login --hostname gitlab.com --web   # el remoto es GitHub: indicar el host
glab auth status
glab ci status -R daalrasi/advanced-ai-lab -b develop
glab ci view               # vista interactiva de los jobs

# GitLab MCP en OpenCode (ya declarado en opencode.json)
opencode mcp auth gitlab   # aprueba en el navegador
opencode mcp list          # gitlab → connected
```

## 6. Operación y costo
```bash
ssh -i ~/.ssh/gitlab_deploy deploy@<IP>
cd /opt/advanced-ai-lab && docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f api
```
El Droplet cobra por hora mientras exista (apagado también cobra). Después de la sustentación:
**Droplet → Destroy**.
