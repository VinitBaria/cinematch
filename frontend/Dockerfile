# ==========================================
# Stage 1: Build React + Vite Web Application
# ==========================================
FROM node:20-alpine AS builder

WORKDIR /app

# Cache package dependencies
COPY package*.json ./
RUN npm ci || npm install

# Copy source files and compile static production bundle
COPY . .
RUN npm run build

# ==========================================
# Stage 2: High-Performance Static Web Server
# ==========================================
FROM nginx:alpine

# Copy compiled assets from build stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Configure SPA fallback and built-in reverse proxy to backend container
RUN printf 'server {\n\
    listen 80;\n\
    location /api/ {\n\
        proxy_pass http://backend:8000/api/;\n\
        proxy_http_version 1.1;\n\
        proxy_set_header Host $host;\n\
        proxy_set_header X-Real-IP $remote_addr;\n\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n\
        proxy_set_header X-Forwarded-Proto $scheme;\n\
    }\n\
    location / {\n\
        root /usr/share/nginx/html;\n\
        index index.html index.htm;\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
