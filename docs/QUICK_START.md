# TaskTrail Quick Start Guide

Get TaskTrail running locally in 5 minutes with Docker.

---

## Prerequisites

- **Docker** 24.0+ and **Docker Compose** 2.20+
- **Git**
- **Firebase Project** with:
  - Authentication enabled (Email/Password)
  - Firestore database created
  - Service account key downloaded

---

## Step 1: Clone & Setup Environment

```bash
# Clone repository
git clone <your-repo-url>
cd TaskTrail

# Copy environment template
cp backend/.env.example backend/.env
```

## Step 2: Configure Environment Variables

Edit [backend/.env](backend/.env) with your credentials:

```bash
# Required - Firebase Configuration
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id

# Required - OpenAI API
OPENAI_API_KEY=sk-proj-your-api-key-here
OPENAI_MODEL=gpt-4o-mini

# Required - Frontend CORS
FRONTEND_URL=http://localhost:5173

# Optional - Advanced Features
ENABLE_VECTOR_MEMORY=false
REDIS_URL=redis://redis:6379/0
```

**Quick Firebase Setup:**
1. Go to [Firebase Console](https://console.firebase.google.com)
2. Create/select your project
3. Navigate to **Project Settings** → **Service Accounts**
4. Click **Generate New Private Key**
5. Extract values from downloaded JSON file to [backend/.env](backend/.env)

**Get OpenAI API Key:**
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create new secret key
3. Copy to `OPENAI_API_KEY` in [backend/.env](backend/.env)

---

## Step 3: Start with Docker Compose

```bash
# Build and start all services
docker compose up --build

# Or run in background
docker compose up -d --build
```

**Services Started:**
- ✅ Backend API → http://localhost:8000
- ✅ API Docs (Swagger) → http://localhost:8000/docs
- ✅ Frontend → http://localhost:5173
- ✅ Admin Dashboard → http://localhost:3001
- ✅ Redis → localhost:6379

---

## Step 4: Create Super Admin

In a new terminal:

```bash
# Create first admin account
docker compose exec api python create_super_admin.py admin@yourdomain.com SecurePassword123!
```

**Output:**
```
✅ Super admin created successfully!
Email: admin@yourdomain.com
Role: super_admin
UID: xyz123abc456
```

---

## Step 5: Verify Installation

### Test Backend API

```bash
# Health check
curl http://localhost:8000/health

# Expected: {"status": "healthy"}
```

### Test Frontend

Open browser to http://localhost:5173
- Sign up with email/password
- Create your first task
- Chat with AI assistant

### Test Admin Dashboard

Open browser to http://localhost:3001
- Login with super admin credentials
- View users, analytics, configuration
- Track token usage

---

## Common Issues & Solutions

### Issue: "Firebase credentials not found"

**Solution:** Verify [backend/.env](backend/.env) has all Firebase fields populated. Check for:
- Extra quotes or spaces
- Newlines in `FIREBASE_PRIVATE_KEY` (should be `\n` not actual newlines)
- Correct path to `serviceAccountKey.json`

### Issue: "OpenAI API key invalid"

**Solution:**
```bash
# Test your API key directly
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

If failed, generate new key at https://platform.openai.com/api-keys

### Issue: Port already in use

**Solution:**
```bash
# Find process using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Mac/Linux

# Kill the process or change port in docker-compose.yml
```

### Issue: "Cannot connect to Docker daemon"

**Solution:**
- Start Docker Desktop
- Verify: `docker ps`
- On Linux: `sudo systemctl start docker`

---

## Development Workflow

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api
docker compose logs -f frontend
```

### Restart Service

```bash
# Restart backend only
docker compose restart api

# Rebuild after code changes
docker compose up --build api
```

### Stop Services

```bash
# Stop all services
docker compose down

# Stop and remove volumes (fresh start)
docker compose down -v
```

### Run Tests

```bash
# Inside backend container
docker compose exec api pytest tests/ -v

# With coverage
docker compose exec api pytest tests/ --cov=app --cov-report=html
```

---

## Next Steps

### 1. Configure Admin Features

See [Admin Dashboard Guide](docs/ADMIN_DASHBOARD_GUIDE.md) for:
- User management
- Token usage tracking
- System configuration
- Audit logging

### 2. Production Deployment

See [Docker Deployment Guide](docs/DOCKER_DEPLOYMENT.md) for:
- Production docker-compose setup
- SSL/TLS configuration
- Secrets management
- Monitoring & backups

### 3. API Integration

See [API Reference](docs/API_REFERENCE.md) for:
- Complete endpoint documentation
- Request/response examples
- Authentication flow
- Admin API endpoints

### 4. Security Hardening

Before production:
- [ ] Change default admin password
- [ ] Set strong `SECRET_KEY` in [backend/.env](backend/.env)
- [ ] Enable MFA for admin accounts
- [ ] Configure firewall rules
- [ ] Set up backup automation
- [ ] Review [Production Readiness Audit](PRODUCTION_READINESS_AUDIT.md)

---

## Getting Help

**Documentation:**
- [Documentation Index](docs/README.md)
- [Admin System Design](docs/ADMIN_SYSTEM_DESIGN.md)
- [Admin Dashboard Guide](docs/ADMIN_DASHBOARD_GUIDE.md)
- [Docker Deployment](docs/DOCKER_DEPLOYMENT.md)
- [API Reference](docs/API_REFERENCE.md)
- [Backend Overview](docs/BACKEND_OVERVIEW.md)

**API Docs:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

*Last Updated: January 30, 2026*