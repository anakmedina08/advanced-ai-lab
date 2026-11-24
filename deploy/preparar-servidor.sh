#!/bin/sh
# Preparación única del Droplet (Ubuntu 24.04) · SPEC-075, historia M4-03.
# Se ejecuta UNA vez como root, desde el Mac:
#   ssh root@IP "sh -s -- '$(cat ~/.ssh/gitlab_deploy.pub)'" < deploy/preparar-servidor.sh
#   - Docker Engine + plugin compose (repositorio oficial de Docker)
#   - usuario `deploy` sin contraseña, en el grupo docker, con la llave pública del job de CI
#   - firewall: solo 22 (SSH), 80 y 443 (Caddy)
#   - 2 GB de swap (el plan de 2 GB de RAM queda holgado)
# El grupo docker equivale a root en el servidor: por eso la llave de CI solo existe en GitLab
# (variable protegida SSH_KEY) y el usuario no tiene sudo.
set -eu

LLAVE_CI="${1:-}"
[ -n "$LLAVE_CI" ] || { echo "Uso: sh preparar-servidor.sh '<ssh-ed25519 AAAA... gitlab-deploy>'"; exit 1; }
DIR=/opt/advanced-ai-lab

export DEBIAN_FRONTEND=noninteractive
apt-get update -q
apt-get install -y -q ca-certificates curl ufw

# Docker desde su repositorio oficial
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $VERSION_CODENAME stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update -q
apt-get install -y -q docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker

# Usuario de despliegue (sin contraseña ni sudo)
id deploy >/dev/null 2>&1 || adduser --disabled-password --gecos "" deploy
usermod -aG docker deploy
install -d -m 700 -o deploy -g deploy /home/deploy/.ssh
printf '%s\n' "$LLAVE_CI" > /home/deploy/.ssh/authorized_keys
chown deploy:deploy /home/deploy/.ssh/authorized_keys
chmod 600 /home/deploy/.ssh/authorized_keys
install -d -o deploy -g deploy "$DIR" "$DIR/data"

# Firewall: SSH, HTTP (redirección y reto ACME) y HTTPS (también HTTP/3 por UDP)
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 443/udp
ufw --force enable

# SSH solo con llave
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl reload ssh

# Swap de 2 GB
if ! swapon --show | grep -q /swapfile; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

docker --version
docker compose version
ufw status verbose
echo "Listo: usuario deploy, Docker y firewall. Directorio $DIR"
