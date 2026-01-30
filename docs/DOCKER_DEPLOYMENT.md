# Docker Deployment Guide

This guide covers local development and production deployment using Docker and Docker Compose.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Configuration](#configuration)
5. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

```bash
# Docker & Docker Compose
docker --version  # Should be 24.0+
docker compose version  # Should be 2.20+

# Git
git --version
```

### Install Docker

**Windows:**
- Download Docker Desktop from https://www.docker.com/products/docker-desktop

**macOS:**
```bash
brew install --cask docker
```

**Linux (Ubuntu/Debian):**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

---

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/tasktrail.git
cd tasktrail
```

### 2. Environment Configuration

**Create Backend .env:**

```bash
cp backend/.env.example backend/.env
```

**Edit `backend/.env`:**

```env
# Firebase
FIREBASE_SERVICE_ACCOUNT_PATH=serviceAccountKey.json

# OpenAI
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4o-mini

# Frontend
FRONTEND_URL=http://localhost:5173

# Redis
REDIS_URL=redis://redis:6379/0

# Environment
ENVIRONMENT=development
```

**Firebase Service Account:**

1. Download `serviceAccountKey.json` from Firebase Console
2. Place in `backend/` directory
3. **NEVER commit this file to git!**

**Create Frontend .env:**

```bash
cd frontend
cp .env.example .env
```

Edit frontend `.env`:

```env
VITE_API_URL=http://localhost:8000
VITE_FIREBASE_API_KEY=your-firebase-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
```

### 3. Build and Start Services

```bash
# From project root
docker compose up --build
```

This starts:
- **API** (backend): http://localhost:8000
- **Frontend**: http://localhost:5173
- **Admin Dashboard**: http://localhost:3001
- **Redis**: localhost:6379

### 4. Create Super Admin

In a new terminal:

```bash
docker compose exec api python create_super_admin.py admin@yourdomain.com SecurePassword123!
```

### 5. Verify Setup

**Health Check:**
```bash
curl http://localhost:8000/health
```

**API Docs:**
```
http://localhost:8000/docs
```

**Frontend:**
```
http://localhost:5173
```

---

## Production Deployment

### Architecture

```
┌─────────────┐
│   Nginx     │ (Reverse Proxy)
│   :80/:443  │
└──────┬──────┘
       │
   ┌───┴────────────┐
   │                │
┌──▼───────┐  ┌────▼─────┐
│ Frontend │  │   API    │
│  :5173   │  │  :8000   │
└──────────┘  └────┬─────┘
                   │
              ┌────▼─────┐
              │  Redis   │
              │  :6379   │
              └──────────┘
```

### Option 1: Docker Compose (Single Server)

**1. Create `docker-compose.prod.yml`:**

```yaml
version: '3.8'

services:
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: tasktrail-api-prod
    restart: always
    env_file:
      - ./backend/.env.prod
    environment:
      - ENVIRONMENT=production
    ports:
      - "8000:8000"
    depends_on:
      - redis
    networks:
      - tasktrail-prod
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    container_name: tasktrail-redis-prod
    restart: always
    volumes:
      - redis_prod_data:/data
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    networks:
      - tasktrail-prod
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    container_name: tasktrail-frontend-prod
    restart: always
    ports:
      - "3000:80"
    depends_on:
      - api
    networks:
      - tasktrail-prod

  nginx:
    image: nginx:alpine
    container_name: tasktrail-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
      - frontend
    networks:
      - tasktrail-prod

volumes:
  redis_prod_data:

networks:
  tasktrail-prod:
    driver: bridge
```

**2. Create Production Dockerfile for Frontend:**

`frontend/Dockerfile.prod`:

```dockerfile
# Build stage
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

**3. Nginx Configuration:**

`nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream api {
        server api:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=60r/m;
    limit_req_zone $binary_remote_addr zone=general_limit:10m rate=100r/m;

    server {
        listen 80;
        server_name yourdomain.com;

        # Redirect to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;

        # Security headers
        add_header X-Frame-Options "DENY" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # API routes
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # CORS headers
            add_header Access-Control-Allow-Origin "https://yourdomain.com" always;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, PATCH, DELETE, OPTIONS" always;
            add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
        }

        # WebSocket
        location /a2a/v1/ws/ {
            proxy_pass http://api;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
        }

        # Frontend
        location / {
            limit_req zone=general_limit burst=50 nodelay;
            
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

**4. Deploy:**

```bash
# Build images
docker compose -f docker-compose.prod.yml build

# Start services
docker compose -f docker-compose.prod.yml up -d

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Check status
docker compose -f docker-compose.prod.yml ps
```

### Option 2: Cloud Deployment (AWS/GCP/Azure)

**Using Docker + Cloud Services:**

1. **Container Registry:**
   ```bash
   # Build and push images
   docker build -t your-registry/tasktrail-api:latest ./backend
   docker push your-registry/tasktrail-api:latest
   
   docker build -t your-registry/tasktrail-frontend:latest ./frontend
   docker push your-registry/tasktrail-frontend:latest
   ```

2. **Deploy to Cloud Run (GCP) / ECS (AWS) / Container Instances (Azure)**

3. **Managed Redis:**
   - GCP: Cloud Memorystore
   - AWS: ElastiCache
   - Azure: Azure Cache for Redis

4. **Load Balancer:**
   - Set up with SSL/TLS
   - Configure health checks
   - Enable WAF (Web Application Firewall)

---

## Configuration

### Environment Variables

**Backend (`.env.prod`):**

```env
# Environment
ENVIRONMENT=production
LOG_LEVEL=WARNING

# Firebase
FIREBASE_SERVICE_ACCOUNT_PATH=/secrets/serviceAccountKey.json

# OpenAI
OPENAI_API_KEY=<from-secrets-manager>

# Frontend
FRONTEND_URL=https://yourdomain.com

# Redis
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
REDIS_PASSWORD=<strong-password>

# Security
ADMIN_EMAILS=admin@yourdomain.com
RATE_LIMIT_PER_MINUTE=30

# Monitoring
SENTRY_DSN=<your-sentry-dsn>
```

### Secrets Management

**Never store secrets in environment files!**

**Option 1: Docker Secrets (Swarm)**

```bash
echo "your-api-key" | docker secret create openai_api_key -
```

```yaml
services:
  api:
    secrets:
      - openai_api_key
    environment:
      - OPENAI_API_KEY_FILE=/run/secrets/openai_api_key
```

**Option 2: Cloud Secrets Manager**

- AWS: Secrets Manager
- GCP: Secret Manager
- Azure: Key Vault

**Option 3: Environment Variable Injection**

```bash
export OPENAI_API_KEY=$(aws secretsmanager get-secret-value --secret-id openai-key --query SecretString --output text)
docker compose up -d
```

### Resource Limits

**Add to `docker-compose.prod.yml`:**

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## Monitoring & Logging

### Health Checks

**API Health:**
```bash
curl https://yourdomain.com/health
```

**Container Health:**
```bash
docker compose ps
docker inspect --format='{{.State.Health.Status}}' tasktrail-api
```

### Logs

**View logs:**
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api

# Last 100 lines
docker compose logs --tail=100 api

# With timestamps
docker compose logs -f -t api
```

**Log Aggregation (Production):**

Use tools like:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Loki + Grafana
- Cloud provider logging (CloudWatch, Stackdriver)

### Monitoring

**Prometheus + Grafana:**

Add to `docker-compose.prod.yml`:

```yaml
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

---

## Backup & Recovery

### Database Backup (Firestore)

**Automated Backups:**

```bash
# Create backup script
cat > backup_firestore.sh << 'EOF'
#!/bin/bash
gcloud firestore export gs://your-backup-bucket/$(date +%Y%m%d)
EOF

chmod +x backup_firestore.sh

# Schedule with cron
0 2 * * * /path/to/backup_firestore.sh
```

### Redis Backup

**Automatic (RDB):**

Redis automatically creates dumps in `/data`:

```bash
docker compose exec redis redis-cli BGSAVE
```

**Manual Backup:**

```bash
docker compose exec redis redis-cli --rdb /backup/dump.rdb
docker cp tasktrail-redis:/backup/dump.rdb ./backups/
```

### Volume Backup

```bash
# Backup all volumes
docker run --rm \
  -v tasktrail_redis_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/redis-$(date +%Y%m%d).tar.gz /data
```

---

## Troubleshooting

### Common Issues

#### 1. Container Won't Start

```bash
# Check logs
docker compose logs api

# Check for port conflicts
netstat -tuln | grep 8000

# Remove and rebuild
docker compose down
docker compose up --build
```

#### 2. Cannot Connect to Redis

```bash
# Check Redis is running
docker compose ps redis

# Test connection
docker compose exec api python -c "import redis; r = redis.from_url('redis://redis:6379/0'); print(r.ping())"

# Check Redis logs
docker compose logs redis
```

#### 3. Firebase Authentication Errors

```bash
# Verify service account file exists
docker compose exec api ls -l serviceAccountKey.json

# Check Firebase initialization
docker compose exec api python -c "from app.firebase import initialize_firebase; initialize_firebase()"
```

#### 4. High Memory Usage

```bash
# Check container stats
docker stats

# Restart specific service
docker compose restart api

# Prune unused resources
docker system prune -a
```

### Performance Tuning

**Backend:**

```python
# app/main.py
uvicorn.run(
    app,
    host="0.0.0.0",
    port=8000,
    workers=4,  # CPU cores
    limit_concurrency=1000,
    timeout_keep_alive=5
)
```

**Redis:**

```yaml
redis:
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru --save 60 1000
```

---

## Maintenance

### Updates

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker compose down
docker compose up --build -d

# Check logs for errors
docker compose logs -f
```

### Database Migrations

```bash
# Run migrations
docker compose exec api python migrate.py

# Verify
docker compose exec api python verify_db.py
```

### Scaling

**Horizontal Scaling (Multiple API Instances):**

```yaml
services:
  api:
    deploy:
      replicas: 3
    # ... rest of config
```

**With Load Balancer:**

```yaml
  nginx:
    # ... nginx config with upstream pool
    # upstream api {
    #     server api_1:8000;
    #     server api_2:8000;
    #     server api_3:8000;
    # }
```

---

## Security Checklist

- [ ] Use secrets management (not .env files)
- [ ] Enable HTTPS with valid certificates
- [ ] Set resource limits on containers
- [ ] Enable rate limiting
- [ ] Use non-root users in containers
- [ ] Scan images for vulnerabilities
- [ ] Enable firewall rules
- [ ] Set up monitoring and alerts
- [ ] Regular security updates
- [ ] Backup verification

---

## CI/CD Integration

**GitHub Actions Example:**

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build images
        run: |
          docker compose -f docker-compose.prod.yml build
      
      - name: Push to registry
        run: |
          docker push your-registry/tasktrail-api:latest
      
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /app/tasktrail
            git pull
            docker compose -f docker-compose.prod.yml pull
            docker compose -f docker-compose.prod.yml up -d
```

---

*Last Updated: January 30, 2026*
