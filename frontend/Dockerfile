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

# Configure SPA fallback so client-side routing (React Router) works seamlessly
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
