#!/bin/sh
# Despliegue en el Droplet · SPEC-075. Lo ejecuta el job `deploy` de GitLab por SSH, dentro de
# /opt/advanced-ai-lab, con IMAGEN_API, IMAGEN_FRONTEND y DOMINIO en el entorno. El token del
# Registry llega por la entrada estándar (no queda en la línea de comandos ni en el historial).
set -eu

: "${IMAGEN_API:?falta IMAGEN_API}"
: "${IMAGEN_FRONTEND:?falta IMAGEN_FRONTEND}"
: "${DOMINIO:?falta DOMINIO}"
REGISTRO="${REGISTRO:-registry.gitlab.com}"
ESPERA="${ESPERA:-180}"  # segundos máximos hasta que la API quede healthy
COMPOSE="docker compose -f docker-compose.prod.yml"

test -f app.env || { echo "Falta app.env (variable de CI ENV_PRODUCCION)"; exit 1; }
chmod 600 app.env
mkdir -p data

# 1. Login de corta duración: se descarga la imagen y se cierra la sesión.
docker login -u gitlab-ci-token --password-stdin "$REGISTRO"
$COMPOSE pull
docker logout "$REGISTRO"

# 2. Reemplazo de los contenedores que cambiaron (Caddy y sus certificados se conservan).
$COMPOSE up -d --remove-orphans

# Compose no recrea un contenedor cuando solo cambia un archivo montado: si el Caddyfile cambió,
# se recrea Caddy para que lo lea (los certificados viven en el volumen caddy_datos).
huella=$(sha256sum Caddyfile | cut -d' ' -f1)
if [ "$(cat .caddyfile.sha256 2>/dev/null || true)" != "$huella" ]; then
  echo "Caddyfile nuevo: recreando caddy"
  $COMPOSE up -d --no-deps --force-recreate caddy
  echo "$huella" > .caddyfile.sha256
fi

# 3. Healthcheck: espera a que Docker marque la API como healthy.
contenedor=$($COMPOSE ps -q api)
transcurrido=0
while :; do
  estado=$(docker inspect -f '{{.State.Health.Status}}' "$contenedor" 2>/dev/null || echo desconocido)
  echo "api: $estado (${transcurrido}s)"
  [ "$estado" = healthy ] && break
  if [ "$transcurrido" -ge "$ESPERA" ]; then
    echo "La API no quedó healthy en ${ESPERA}s. Últimos registros:"
    $COMPOSE logs --tail 50 api
    exit 1
  fi
  sleep 5
  transcurrido=$((transcurrido + 5))
done

# 4. Limpieza de imágenes viejas para no llenar el disco del Droplet.
docker image prune -f >/dev/null
echo "Desplegado: https://$DOMINIO y https://api.$DOMINIO"
