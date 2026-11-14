# Frontend propio: compila con Node y sirve los estáticos con nginx (SPEC-041).
# ---------- Etapa 1: build ----------
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
# La URL de la API se fija en tiempo de compilación (Vite reemplaza import.meta.env)
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# ---------- Etapa 2: nginx ----------
FROM nginx:1.27-alpine AS runtime
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s CMD wget -qO- http://localhost/ >/dev/null || exit 1
