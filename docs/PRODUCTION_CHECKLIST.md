# Production Deployment Checklist

Complete checklist for deploying TaskTrail to production safely and securely.

---

## Pre-Deployment

### Security Audit
- [ ] Review [PRODUCTION_READINESS_AUDIT.md](../PRODUCTION_READINESS_AUDIT.md) findings
- [ ] All P0 (critical) issues resolved
- [ ] All P1 (high priority) issues addressed
- [ ] Security scan completed (no known vulnerabilities)

### Code Quality
- [ ] All tests passing (`pytest tests/ -v`)
- [ ] Code coverage > 80%
- [ ] No critical linting errors
- [ ] Type checking passes (if using mypy)
- [ ] Dead code removed

### Secrets Management
- [ ] **CRITICAL:** Revoke all exposed API keys from git history
- [ ] Remove `.env` from git history using git-filter-repo
- [ ] Generate new production API keys
- [ ] Store secrets in vault (AWS Secrets Manager, Azure Key Vault, etc.)
- [ ] Update deployment to pull from secrets manager
- [ ] `.env.example` updated with all required variables
- [ ] No hardcoded credentials anywhere in code

### Configuration
- [ ] `SECRET_KEY` set to strong random value (not default)
- [ ] `ENVIRONMENT=production` in production env
- [ ] `DEBUG=False` in production
- [ ] `ALLOWED_HOSTS` configured correctly
- [ ] CORS origins limited to production domains only
- [ ] Rate limiting configured
- [ ] Session timeout configured appropriately

---

## Infrastructure Setup

### Domain & DNS
- [ ] Domain registered
- [ ] DNS records configured:
  - [ ] A record for main domain
  - [ ] A record for API subdomain (optional)
  - [ ] A record for admin subdomain
- [ ] SSL/TLS certificates obtained
- [ ] Auto-renewal configured for certificates

### Server/Cloud Resources
- [ ] Production server provisioned (minimum specs met)
- [ ] Firewall rules configured:
  - [ ] Allow 80 (HTTP redirect)
  - [ ] Allow 443 (HTTPS)
  - [ ] Allow 22 (SSH) from specific IPs only
  - [ ] Block all other inbound traffic
- [ ] SSH keys configured (password auth disabled)
- [ ] Monitoring agent installed
- [ ] Backup agent installed

### Database (Firebase)
- [ ] Production Firebase project created
- [ ] Firestore in production mode
- [ ] Security rules configured
- [ ] Firestore indexes created
- [ ] Backup schedule configured
- [ ] Firebase Authentication configured
  - [ ] Email/password enabled
  - [ ] Authorized domains configured
  - [ ] Email templates customized

### Docker Setup
- [ ] Docker 24.0+ installed
- [ ] Docker Compose 2.20+ installed
- [ ] Production docker-compose.yml configured
- [ ] Health checks configured for all services
- [ ] Resource limits set (CPU, memory)
- [ ] Restart policies configured
- [ ] Log rotation configured

---

## Deployment Configuration

### Backend API
- [ ] Environment variables set in production
- [ ] OpenAI API key configured
- [ ] Firebase credentials configured
- [ ] Redis configured (if using vector memory)
- [ ] Gunicorn/Uvicorn workers configured
- [ ] Worker count = (2 × CPU cores) + 1
- [ ] Request timeout configured
- [ ] Max request size configured

### Frontend
- [ ] Build optimized for production (`npm run build`)
- [ ] API endpoint URLs configured
- [ ] Firebase config set for production
- [ ] Environment variables set
- [ ] Service worker configured (if using)
- [ ] Static assets minified
- [ ] Images optimized

### Admin Dashboard
- [ ] Separate subdomain configured
- [ ] Admin Firebase config set
- [ ] Super admin account created
- [ ] MFA enabled for all admins
- [ ] IP whitelist configured (if required)

### Reverse Proxy (Nginx)
- [ ] Nginx installed and configured
- [ ] SSL/TLS certificates configured
- [ ] HTTP → HTTPS redirect configured
- [ ] Proxy headers set correctly
- [ ] Rate limiting configured
- [ ] DDoS protection configured
- [ ] Security headers configured:
  - [ ] X-Frame-Options
  - [ ] X-Content-Type-Options
  - [ ] X-XSS-Protection
  - [ ] Strict-Transport-Security (HSTS)
  - [ ] Content-Security-Policy
- [ ] Gzip compression enabled
- [ ] Static file caching configured

---

## Monitoring & Logging

### Application Monitoring
- [ ] Sentry (or similar) configured for error tracking
- [ ] Logging configured (file + cloud)
- [ ] Log levels set appropriately (INFO in production)
- [ ] Sensitive data not logged
- [ ] Structured logging implemented

### Infrastructure Monitoring
- [ ] Uptime monitoring configured
- [ ] Performance monitoring (APM) configured
- [ ] Resource usage monitoring:
  - [ ] CPU
  - [ ] Memory
  - [ ] Disk space
  - [ ] Network
- [ ] Alerts configured:
  - [ ] Service down
  - [ ] High error rate
  - [ ] High resource usage
  - [ ] Disk space low
  - [ ] SSL certificate expiring

### Analytics
- [ ] Token usage tracking enabled
- [ ] User analytics configured
- [ ] API usage tracked
- [ ] Cost monitoring configured

---

## Backup & Recovery

### Backup Configuration
- [ ] Firestore automated backups enabled
- [ ] Backup retention policy configured
- [ ] Redis persistence configured (if used)
- [ ] Application code backed up
- [ ] Environment configuration backed up (securely)

### Disaster Recovery
- [ ] Disaster recovery plan documented
- [ ] Recovery Time Objective (RTO) defined
- [ ] Recovery Point Objective (RPO) defined
- [ ] Backup restoration tested
- [ ] Runbook created for common issues

---

## Testing

### Pre-Production Testing
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] End-to-end tests passing
- [ ] Load testing completed
- [ ] Performance benchmarks met:
  - [ ] API response time < 200ms (p95)
  - [ ] Page load time < 2s
  - [ ] Time to interactive < 3s

### Staging Environment
- [ ] Staging environment matches production
- [ ] Full deployment tested in staging
- [ ] Smoke tests passing in staging
- [ ] Security scan completed on staging
- [ ] Performance test completed on staging

### User Acceptance Testing
- [ ] UAT completed by stakeholders
- [ ] Critical user flows tested
- [ ] Admin features tested
- [ ] Authentication flows tested
- [ ] Payment flows tested (if applicable)

---

## Security Hardening

### Application Security
- [ ] Rate limiting enabled on all endpoints
- [ ] Input validation on all endpoints
- [ ] SQL injection protection (N/A - using Firestore)
- [ ] XSS protection enabled
- [ ] CSRF protection enabled
- [ ] Authentication required where appropriate
- [ ] Authorization checked on all protected routes
- [ ] Secrets not in environment variables (use secrets manager)

### Admin Security
- [ ] Super admin MFA required
- [ ] Admin session timeout configured (15 minutes)
- [ ] Admin IP whitelist enabled (if required)
- [ ] Audit logging enabled
- [ ] Strong password policy enforced
- [ ] Admin actions require confirmation
- [ ] Principle of least privilege applied

### Network Security
- [ ] Firewall configured
- [ ] DDoS protection enabled
- [ ] WAF configured (if using)
- [ ] VPN for admin access (optional)
- [ ] Intrusion detection system configured

### Compliance
- [ ] GDPR compliance reviewed (if applicable)
- [ ] Data retention policy configured
- [ ] Privacy policy published
- [ ] Terms of service published
- [ ] Cookie consent implemented (if applicable)
- [ ] User data export implemented
- [ ] User data deletion implemented

---

## Performance Optimization

### Backend
- [ ] Database queries optimized
- [ ] Indexes created for common queries
- [ ] Response caching configured
- [ ] Connection pooling configured
- [ ] Async operations used where appropriate
- [ ] N+1 queries eliminated

### Frontend
- [ ] Code splitting implemented
- [ ] Lazy loading configured
- [ ] Images lazy loaded
- [ ] Bundle size optimized
- [ ] CDN configured for static assets
- [ ] Service worker for offline support (optional)

### Caching
- [ ] Redis configured for caching
- [ ] Cache invalidation strategy defined
- [ ] CDN caching configured
- [ ] Browser caching headers set
- [ ] API response caching configured

---

## Documentation

### Internal Documentation
- [ ] Architecture diagram created
- [ ] API documentation up to date
- [ ] Deployment documentation complete
- [ ] Runbook created
- [ ] Incident response plan documented
- [ ] On-call rotation defined

### External Documentation
- [ ] User guide published
- [ ] API documentation published (if public API)
- [ ] Status page configured
- [ ] Support channels configured
- [ ] FAQ published

---

## Go-Live Preparation

### Communication
- [ ] Stakeholders notified of go-live date
- [ ] Support team trained
- [ ] On-call schedule published
- [ ] Incident escalation path defined
- [ ] Status page updated

### Launch Plan
- [ ] Deployment window scheduled
- [ ] Rollback plan documented
- [ ] Go/no-go checklist created
- [ ] Post-launch monitoring plan created
- [ ] Success criteria defined

### Post-Launch
- [ ] Monitor error rates for 24 hours
- [ ] Monitor performance metrics
- [ ] Check all critical user flows
- [ ] Verify backups working
- [ ] Verify monitoring/alerts working
- [ ] Review logs for errors
- [ ] User feedback collection configured

---

## Production Deployment Steps

### 1. Final Verification (Day Before)
```bash
# Run full test suite
pytest tests/ -v --cov

# Check for security issues
pip-audit

# Verify environment config
python -c "from app.config import settings; print('Config OK')"
```

### 2. Deploy Backend (Deployment Day)
```bash
# SSH to production server
ssh production-server

# Pull latest code
cd /opt/tasktrail
git pull origin main

# Rebuild containers
docker compose -f docker-compose.prod.yml build

# Stop services (brief downtime)
docker compose -f docker-compose.prod.yml down

# Start with new version
docker compose -f docker-compose.prod.yml up -d

# Verify health
curl https://api.yourdomain.com/health

# Check logs
docker compose -f docker-compose.prod.yml logs -f
```

### 3. Deploy Frontend
```bash
# Build locally or in CI/CD
npm run build

# Deploy to CDN/hosting
# (specific commands depend on hosting provider)

# Verify
curl https://yourdomain.com
```

### 4. Post-Deployment Verification
```bash
# Test critical endpoints
python backend/test_admin_api.py

# Check error rates
# (check Sentry/monitoring dashboard)

# Verify backups
# (check backup system)

# Test user flows manually
# - Sign up
# - Create task
# - Chat with AI
# - Admin login
```

---

## Rollback Procedure

If issues detected after deployment:

```bash
# 1. Stop current version
docker compose -f docker-compose.prod.yml down

# 2. Checkout previous version
git checkout <previous-tag>

# 3. Rebuild and restart
docker compose -f docker-compose.prod.yml up -d --build

# 4. Verify rollback successful
curl https://api.yourdomain.com/health

# 5. Notify stakeholders
# Send notification about rollback

# 6. Investigate issue
# Review logs, fix issue, prepare hotfix
```

---

## Post-Production Checklist

### Week 1
- [ ] Daily monitoring of error rates
- [ ] Daily review of performance metrics
- [ ] Daily backup verification
- [ ] User feedback reviewed
- [ ] Support tickets reviewed
- [ ] Hot fixes deployed if needed

### Week 2-4
- [ ] Weekly performance review
- [ ] Weekly security review
- [ ] Cost analysis completed
- [ ] Optimization opportunities identified
- [ ] Feature requests prioritized

### Month 1
- [ ] Post-launch retrospective completed
- [ ] Lessons learned documented
- [ ] Process improvements identified
- [ ] Production runbook updated
- [ ] Monitoring thresholds tuned

---

## Critical Contacts

**Technical Team:**
- DevOps Lead: _____________
- Backend Lead: _____________
- Frontend Lead: _____________
- On-Call: _____________

**Business:**
- Product Owner: _____________
- Stakeholder: _____________

**Vendors:**
- OpenAI Support: https://help.openai.com
- Firebase Support: https://firebase.google.com/support
- Hosting Support: _____________

---

## Success Metrics

Define and track these metrics post-launch:

**Reliability:**
- [ ] Uptime > 99.9%
- [ ] Error rate < 0.1%
- [ ] API response time p95 < 200ms

**Performance:**
- [ ] Page load time < 2s
- [ ] Time to interactive < 3s
- [ ] Backend throughput > 100 req/s

**Business:**
- [ ] User sign-ups tracking
- [ ] Task creation rate
- [ ] AI usage rate
- [ ] User retention > 40% (Day 7)

**Cost:**
- [ ] OpenAI costs within budget
- [ ] Infrastructure costs within budget
- [ ] Cost per user < $X

---

**Deployment Authorization:**

- [ ] Technical Lead Sign-off: _____________ Date: _______
- [ ] Security Review Sign-off: _____________ Date: _______
- [ ] Product Owner Sign-off: _____________ Date: _______

---

*Last Updated: January 30, 2026*
