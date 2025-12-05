# Day 7 Deployment Preparation Checklist

**Date**: 2025-12-04
**Status**: 🚧 **IN PROGRESS**
**Goal**: Production-ready deployment preparation

---

## 📋 Pre-Deployment Checklist

### 🔒 Security Hardening

#### Backend Security
- [ ] **Switch to paid Gemini API**
  - Current: Free tier (limited quota)
  - Action: Upgrade to paid API key
  - File: `.env` → Update `GEMINI_API_KEY`

- [ ] **Disable anonymous API access**
  - Current: `ALLOW_ANONYMOUS_API=true` (dev mode)
  - Action: Set to `false` in production
  - File: `.env` → `ALLOW_ANONYMOUS_API=false`

- [ ] **Rotate database credentials**
  - Current: Read-only user `grants_readonly.vtbvcabetythqrdedgee`
  - Action: Rotate password via Supabase
  - Store in secrets manager (AWS Secrets Manager, Azure Key Vault, etc.)
  - Update: `.env` → `GRANTS_DB_PASSWORD`

- [ ] **Configure CORS for production domain**
  - Current: Likely open for development
  - Action: Restrict to production frontend domain only
  - File: `ovra_backend/settings.py` → `CORS_ALLOWED_ORIGINS`
  ```python
  CORS_ALLOWED_ORIGINS = [
      "https://yourdomain.com",
      "https://www.yourdomain.com",
  ]
  ```

- [ ] **Enable CSRF protection**
  - Verify Django CSRF middleware enabled
  - Configure CSRF trusted origins
  ```python
  CSRF_TRUSTED_ORIGINS = [
      "https://yourdomain.com",
  ]
  ```

- [ ] **Set secure cookie settings**
  ```python
  SESSION_COOKIE_SECURE = True
  CSRF_COOKIE_SECURE = True
  SESSION_COOKIE_HTTPONLY = True
  CSRF_COOKIE_HTTPONLY = True
  SESSION_COOKIE_SAMESITE = 'Lax'
  CSRF_COOKIE_SAMESITE = 'Lax'
  ```

- [ ] **Configure allowed hosts**
  ```python
  ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
  # Remove: ALLOWED_HOSTS = ['*']
  ```

- [ ] **Disable DEBUG mode**
  ```python
  DEBUG = False
  ```

#### API Security
- [ ] **Add rate limiting**
  - Install: `django-ratelimit` or `django-throttle`
  - Configure per-user and per-IP limits
  - Suggested limits:
    - Search: 60 requests/minute per user
    - Chat: 30 requests/minute per user (due to LLM cost)
    - Details: 120 requests/minute per user

- [ ] **Add API authentication**
  - Re-enable JWT authentication (currently disabled for testing)
  - Verify all endpoints require authentication except health check

- [ ] **Input validation strengthening**
  - Verify all serializers have proper validation
  - Add max length limits on text inputs
  - Validate date ranges
  - Sanitize organismo and finalidad filters

#### Database Security
- [ ] **Verify read-only access**
  - Confirm `grants_readonly` user has only SELECT permission
  - Test: Try INSERT/UPDATE/DELETE (should fail)

- [ ] **Enable connection pooling limits**
  - Current: 15 connections max
  - Monitor usage and adjust if needed

- [ ] **Enable SSL for database connections**
  - Supabase should have SSL by default
  - Verify: `GRANTS_DB_OPTIONS = {'sslmode': 'require'}`

---

### 🔧 Configuration Management

#### Environment Variables
Create production `.env` file with:

```bash
# Django
SECRET_KEY=<generate-new-secure-key>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database (Main)
DATABASE_URL=<production-digitalocean-url>

# Database (Grants - Supabase)
GRANTS_DB_USER=grants_readonly.<new-project-id>
GRANTS_DB_PASSWORD=<rotated-password>
GRANTS_DB_HOST=aws-1-eu-central-2.pooler.supabase.com
GRANTS_DB_PORT=6543

# LLM APIs
GEMINI_API_KEY=<paid-tier-api-key>
OPENAI_API_KEY=<production-api-key>

# Redis
REDIS_URL=redis://<production-redis-host>:6379/0

# Security
ALLOW_ANONYMOUS_API=false
CORS_ALLOWED_ORIGINS=https://yourdomain.com

# Monitoring (optional)
SENTRY_DSN=<sentry-dsn>
```

#### Secrets Management
- [ ] **Use secrets manager**
  - AWS Secrets Manager
  - Azure Key Vault
  - HashiCorp Vault
  - Or encrypted environment variables

- [ ] **Never commit secrets to git**
  - Verify `.env` is in `.gitignore`
  - Check git history for leaked secrets
  - Rotate any previously committed keys

---

### 📊 Monitoring & Logging

#### Application Monitoring
- [ ] **Setup error tracking**
  - Recommended: Sentry
  - Install: `pip install sentry-sdk`
  - Configure in `settings.py`:
  ```python
  import sentry_sdk
  from sentry_sdk.integrations.django import DjangoIntegration

  sentry_sdk.init(
      dsn=os.getenv("SENTRY_DSN"),
      integrations=[DjangoIntegration()],
      traces_sample_rate=0.1,
      send_default_pii=False,
  )
  ```

- [ ] **Add health check endpoint**
  - Create: `/health/` endpoint
  - Returns: Database status, Redis status, API status
  - Example:
  ```python
  @api_view(['GET'])
  @permission_classes([AllowAny])
  def health_check(request):
      return Response({
          "status": "healthy",
          "database": "connected",
          "redis": "connected",
          "timestamp": datetime.now().isoformat()
      })
  ```

- [ ] **Setup performance monitoring**
  - Options: New Relic, Datadog, AWS CloudWatch
  - Monitor: Response times, error rates, throughput

#### Logging Configuration
- [ ] **Configure structured logging**
  ```python
  LOGGING = {
      'version': 1,
      'disable_existing_loggers': False,
      'formatters': {
          'json': {
              '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
          },
      },
      'handlers': {
          'console': {
              'class': 'logging.StreamHandler',
              'formatter': 'json',
          },
          'file': {
              'class': 'logging.handlers.RotatingFileHandler',
              'filename': '/var/log/django/grants.log',
              'maxBytes': 10485760,  # 10MB
              'backupCount': 5,
              'formatter': 'json',
          },
      },
      'loggers': {
          'django': {
              'handlers': ['console', 'file'],
              'level': 'INFO',
          },
          'apps.grants': {
              'handlers': ['console', 'file'],
              'level': 'INFO',
          },
      },
  }
  ```

- [ ] **Log important events**
  - Search queries (for analytics)
  - Chat queries and responses
  - LLM model selection decisions
  - Failed authentication attempts
  - Rate limit violations
  - Database connection errors

---

### 🚀 Performance Optimization

#### Caching Strategy
- [ ] **Verify Redis configuration**
  - Production Redis instance (not Docker)
  - Enable persistence (RDB + AOF)
  - Configure eviction policy: `allkeys-lru`
  - Set memory limit appropriately

- [ ] **Configure cache timeouts**
  - Embeddings: 1 hour (current ✅)
  - Search results: 15 minutes
  - Grant details: 30 minutes
  - Session data: 1 hour (current ✅)

#### Database Optimization
- [ ] **Add database indexes** (if not already present)
  ```sql
  -- On Supabase grants database
  CREATE INDEX IF NOT EXISTS idx_convocatorias_abierto ON convocatorias(abierto);
  CREATE INDEX IF NOT EXISTS idx_convocatorias_fecha_publicacion ON convocatorias(fecha_publicacion);
  CREATE INDEX IF NOT EXISTS idx_convocatorias_organismo ON convocatorias(organismo);
  ```

- [ ] **Install pgvector extension** (optional, for faster semantic search)
  ```sql
  -- On Supabase
  CREATE EXTENSION IF NOT EXISTS vector;
  ```
  Note: NumPy fallback is working, but pgvector is faster

#### Frontend Optimization
- [ ] **Build optimized production bundle**
  ```bash
  cd frontend
  npm run build
  ```

- [ ] **Enable image optimization**
  - Configure Next.js image domains
  - Use next/image for all images

- [ ] **Add compression**
  - Enable gzip/brotli in production server

---

### 📱 Frontend Deployment

#### Next.js Configuration
- [ ] **Update environment variables**
  ```bash
  # .env.production
  NEXT_PUBLIC_API_URL=https://api.yourdomain.com
  ```

- [ ] **Re-enable authentication**
  - Restore `ProtectedLayout` in `/app/grants/page.tsx`
  - File location: Line 139 and 288

- [ ] **Configure production build**
  ```javascript
  // next.config.js
  module.exports = {
    output: 'standalone',  // For Docker deployment
    images: {
      domains: ['yourdomain.com'],
    },
  }
  ```

#### Deployment Options
- [ ] **Option 1: Vercel** (Easiest for Next.js)
  - Connect GitHub repo
  - Auto-deploys on push
  - Configure environment variables in Vercel dashboard

- [ ] **Option 2: Docker + Cloud**
  - Build Docker image
  - Deploy to AWS ECS, Google Cloud Run, or Azure Container Instances

- [ ] **Option 3: Static hosting + API**
  - Build static export: `next build && next export`
  - Host on Netlify/Cloudflare Pages
  - Separate backend deployment

---

### 🌐 Infrastructure Setup

#### Backend Deployment
- [ ] **Choose hosting platform**
  - AWS Elastic Beanstalk
  - Google Cloud App Engine
  - Azure App Service
  - DigitalOcean App Platform
  - Heroku (easiest but more expensive)

- [ ] **Configure web server**
  - Gunicorn workers: 2-4 per CPU core
  - Nginx reverse proxy
  - SSL certificate (Let's Encrypt)

- [ ] **Setup auto-scaling** (optional)
  - Min: 2 instances (high availability)
  - Max: 10 instances (cost control)
  - Scale on: CPU > 70% or memory > 80%

#### Database Backup
- [ ] **Configure automated backups**
  - Supabase: Enable automatic backups (should be default)
  - Retention: 30 days minimum
  - Test restore procedure

#### CDN Setup (optional)
- [ ] **Add CDN for static assets**
  - CloudFlare (free)
  - AWS CloudFront
  - Reduces latency for global users

---

### 📈 Analytics & Metrics

#### User Analytics
- [ ] **Add analytics tracking**
  - Google Analytics 4
  - Mixpanel
  - Posthog (self-hosted option)

- [ ] **Track key events**
  - Search queries
  - Filters used
  - Grants viewed
  - PDF downloads
  - Chat interactions
  - Page views

#### Business Metrics
- [ ] **Create dashboard for**
  - Total searches per day
  - Most popular search terms
  - Average results per search
  - Chat usage (simple vs complex queries)
  - LLM cost tracking (Gemini vs GPT-4o usage)
  - Top viewed grants
  - Conversion metrics (if applicable)

---

### 🧪 Pre-Production Testing

#### Load Testing
- [ ] **Test with realistic load**
  - Tools: Apache JMeter, Locust, k6
  - Simulate: 100 concurrent users
  - Test: Search, chat, and details endpoints
  - Verify: Response times under load

#### Security Testing
- [ ] **Run security scan**
  - OWASP ZAP
  - Burp Suite
  - Test for: SQL injection, XSS, CSRF, auth bypass

#### Browser Testing
- [ ] **Test on multiple browsers**
  - Chrome ✅
  - Firefox
  - Safari
  - Edge
  - Mobile Safari (iOS)
  - Mobile Chrome (Android)

---

### 📚 Documentation

#### API Documentation
- [ ] **Create API docs**
  - Use Django REST Framework's built-in docs
  - Or Swagger/OpenAPI
  - Document all endpoints, parameters, responses

#### User Documentation
- [ ] **Create user guide**
  - How to search for grants
  - How to use filters
  - How to use chat interface
  - How to interpret results

#### Admin Documentation
- [ ] **Create operations manual**
  - Deployment procedure
  - Rollback procedure
  - How to rotate secrets
  - How to scale services
  - Troubleshooting common issues

---

## ✅ Go-Live Checklist

### 24 Hours Before Launch
- [ ] Backup all databases
- [ ] Test rollback procedure
- [ ] Notify team of deployment window
- [ ] Prepare monitoring dashboards
- [ ] Review logs for any pre-existing errors

### Launch Day
- [ ] Deploy backend to production
- [ ] Deploy frontend to production
- [ ] Update DNS records (if needed)
- [ ] Verify SSL certificates
- [ ] Test all critical user flows
- [ ] Monitor error rates
- [ ] Monitor performance metrics
- [ ] Monitor LLM API costs

### Post-Launch (First Week)
- [ ] Daily monitoring of error rates
- [ ] Review user feedback
- [ ] Monitor LLM costs (should be ~$0.50/1M tokens)
- [ ] Check database performance
- [ ] Verify backup success
- [ ] Address any issues immediately

---

## 🎯 Success Criteria for Production

### Performance Targets
- ✅ Search response time: < 2s (current: 1.14s)
- ✅ Chat response time: < 5s (current: 2.95s)
- ✅ Details response time: < 1s (current: 0.45s)
- ✅ Page load time: < 3s
- ✅ Uptime: > 99.9% (3.65 days downtime/year max)

### Cost Targets
- LLM costs: < $100/month (based on 80% Gemini Flash usage)
- Infrastructure: < $200/month (depending on traffic)
- Total: < $300/month for moderate usage

### User Experience
- No critical bugs
- Intuitive search interface
- Fast response times
- Accurate results
- Mobile responsive

---

## 📊 Monitoring Checklist

### Daily Checks
- [ ] Error rate < 1%
- [ ] Average response time within targets
- [ ] No 5xx errors
- [ ] LLM API costs tracking as expected

### Weekly Checks
- [ ] Review top search queries
- [ ] Analyze failed searches
- [ ] Check database performance
- [ ] Review user feedback
- [ ] Update documentation if needed

### Monthly Checks
- [ ] Rotate credentials
- [ ] Review access logs
- [ ] Update dependencies
- [ ] Cost optimization review
- [ ] Backup restoration test

---

## 🚨 Incident Response Plan

### Severity Levels
- **P0 (Critical)**: Site down, no access - Fix immediately
- **P1 (High)**: Major feature broken - Fix within 4 hours
- **P2 (Medium)**: Minor feature broken - Fix within 24 hours
- **P3 (Low)**: Cosmetic issues - Fix within 1 week

### Response Procedure
1. Acknowledge incident
2. Assess severity
3. Notify stakeholders
4. Investigate root cause
5. Implement fix
6. Verify fix in production
7. Post-mortem review
8. Update documentation

---

## 📝 Deployment Commands Reference

### Backend Deployment
```bash
# 1. Activate virtual environment
cd backend
source .venv/bin/activate  # Linux/Mac
.\.venv\Scripts\activate   # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run migrations (if any)
python manage.py migrate

# 4. Collect static files
python manage.py collectstatic --noinput

# 5. Test configuration
python manage.py check --deploy

# 6. Start with Gunicorn
gunicorn ovra_backend.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### Frontend Deployment
```bash
# 1. Install dependencies
cd frontend
npm install

# 2. Build production bundle
npm run build

# 3. Start production server
npm start

# Or export static files
npm run build && npm run export
```

---

**Status**: Ready for production deployment after completing checklist
**Estimated Time**: 4-8 hours for full deployment setup
**Priority**: Complete security items first, then monitoring, then optimizations
