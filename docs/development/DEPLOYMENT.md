# 🚀 Production Deployment Guide

This guide describes deploying LiteraX to Linux/Cloud environments using **Docker Compose**, **PostgreSQL with pgvector**, **Redis**, and an **Nginx** reverse proxy.

---

## 🐳 Docker Architecture

LiteraX is divided into modular containers:
- `api`: FastAPI application serving REST endpoints.
- `bot`: aiogram worker handling Telegram polling or webhook updates.
- `postgres`: PostgreSQL 16 database with the `pgvector` extension.
- `redis`: In-memory cache and session store.
- `nginx`: Reverse proxy handling TLS/SSL termination and rate limits.

---

## 📄 Docker Compose Configuration (`docker-compose.yml`)

```yaml
version: "3.9"

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: literax_postgres
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-literax}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-literax_secret}
      POSTGRES_DB: ${POSTGRES_DB:-literax_db}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U literax -d literax_db"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: literax_redis
    restart: always
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: literax_api
    restart: always
    command: uvicorn literax.api.main:app --host 0.0.0.0 --port 8000 --workers 4
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER:-literax}:${POSTGRES_PASSWORD:-literax_secret}@postgres:5432/${POSTGRES_DB:-literax_db}
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    ports:
      - "8000:8000"

  bot:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: literax_bot
    restart: always
    command: python -m literax.bot.main
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER:-literax}:${POSTGRES_PASSWORD:-literax_secret}@postgres:5432/${POSTGRES_DB:-literax_db}
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env
    depends_on:
      - api
      - redis
      - postgres

volumes:
  postgres_data:
  redis_data:
```

---

## 🐳 Application Dockerfile

```dockerfile
FROM python:3.12-slim-bookworm

WORKDIR /app

# Install system dependencies for PyMuPDF and C++ RapidFuzz compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
```

---

## 🔒 Nginx Reverse Proxy & SSL Configuration

```nginx
server {
    listen 80;
    server_name api.literax.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.literax.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.literax.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.literax.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 🛡️ Health Check Endpoints

LiteraX exposes a health check route:
- `GET /health`
  - Returns `{"status": "healthy", "service": "LiteraX API Gateway", "version": "0.1.0"}`
- Suitable for uptime monitors (UptimeRobot, AWS ALB Health Checks, local Nginx health checks).

---

## 🖥️ Bare-Metal / Ubuntu Server Deployment (Systemd)

If deploying directly on an Ubuntu/Debian server or Ubuntu in WSL2 without Docker:

### 1. Prerequisites
```bash
sudo apt update && sudo apt install -y python3-venv python3-pip nginx
```

### 2. Clone and Setup Environment
```bash
git clone https://github.com/FatirGibran/LiteraX.git /home/fatir/LiteraX
cd /home/fatir/LiteraX
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e .
cp .env.example .env
```

### 3. Systemd Service
Copy the template service file:
```bash
sudo cp deploy/systemd/literax-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now literax-api.service
sudo systemctl status literax-api.service
```

### 4. Nginx Reverse Proxy
Configure Nginx to proxy port 80 to port 8080:
```bash
sudo cp deploy/nginx/literax.conf /etc/nginx/sites-available/literax
sudo ln -s /etc/nginx/sites-available/literax /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

