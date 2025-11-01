ARG VITE_API_BASE_URL=/ops-api

FROM node:20-alpine AS deps
WORKDIR /app
COPY ops-console/package*.json ./
RUN (npm ci --include=dev || npm install --include=dev) --no-audit --no-fund \
 && npm install -D postcss@^8 autoprefixer@^10

FROM node:20-alpine AS build
WORKDIR /app
COPY ops-console/ ./
COPY --from=deps /app/node_modules ./node_modules
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build -- --base=/ops/

FROM nginx:1.27-alpine
COPY --from=build /app/dist/ /usr/share/nginx/html/
RUN printf 'server { \
  listen 80; \
  root /usr/share/nginx/html; \
  index index.html; \
  location / { try_files $uri /index.html; } \
  location /ops/ { \
    alias /usr/share/nginx/html/; \
    try_files $uri /index.html; \
  } \
}' > /etc/nginx/conf.d/default.conf
EXPOSE 80
