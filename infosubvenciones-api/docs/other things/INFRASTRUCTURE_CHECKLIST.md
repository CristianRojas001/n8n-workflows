# Infrastructure Checklist - InfoSubvenciones

> Purpose: Track all external services, credentials, and infrastructure setup. Complete this checklist before starting implementation.

**Last Updated**: 2025-12-01
**Status**: 🟡 In Progress - Day 2 of Foundation Week

---

## 🚨 CRITICAL: Run These Commands FIRST

**Before any coding or planning, run these 4 commands and report results:**

```bash
# 1. Check Redis
redis-cli ping
# Expected: PONG

# 2. Check Python version
python --version
# Expected: Python 3.11.x or higher

# 3. Check disk space (Windows)
powershell "Get-PSDrive D | Select-Object Used,Free"
# Expected: 60GB+ free space

# 4. Check PostgreSQL version
psql --version
# Expected: psql (PostgreSQL) 15.x or higher
```

**⚠️ STOP HERE**: Do not proceed until you paste the output of these 4 commands. Based on results, we'll know exactly what needs to be installed/fixed before any code is written.

---

## Quick Status Overview

| Component | Status | Owner | Notes |
|-----------|--------|-------|-------|
| PostgreSQL + pgvector | ✅ Ready | You | Confirmed available |
| Redis | ⚠️ Unknown | You | Need to verify Day 2 |
| Gemini API Key | ✅ Ready | You | Confirmed available |
| OpenAI API Key | ⏳ Pending | You | Need to obtain |
| Python 3.11+ | ⏳ Pending | You | Need to verify |
| Disk Space (60GB+) | ⏳ Pending | You | Need to check |
| .env file | ⏳ Pending | Claude | Create Day 2 |

---

## 1. Environments

| Environment | Purpose | URL / Access | Status | Notes |
|-------------|---------|--------------|--------|-------|
| **Local Dev** | Development & testing | `http://localhost:3000` (frontend)<br>`http://localhost:8000` (API) | ⏳ Setup in progress | Your Windows machine |
| **Production** | Public grant search | TBD (domain undecided) | ⏳ Week 6 | Deploy separately or with ARTISTING |

**Notes**:
- MVP is local dev only (Week 1-5)
- No staging environment for now (can add later)
- Production deployment location TBD (same server as ARTISTING or separate)

---

## 2. Core Services

### Database: PostgreSQL 15+ with pgvector

| Aspect | Details | Status |
|--------|---------|--------|
| **Provider** | Self-hosted PostgreSQL | ✅ |
| **Version Required** | 15+ | ⏳ Verify |
| **Extension** | pgvector 0.5.1+ | ✅ Confirmed |
| **Database Name** | `infosubvenciones` | ⏳ Create Day 2 |
| **Credentials** | Fill in below ↓ | ⏳ Pending |
| **Connection String** | `postgresql://[user]:[pass]@[host]:5432/infosubvenciones` | ⏳ Pending |

**Credentials** (fill in):
- Host: `localhost` or `___________`
- Port: `5432` or `___________`
- Username: `postgres` or `___________`
- Password: `___________` (keep secure!)

**Verification Steps**:
```bash
# 1. Check version
psql --version  # Need 15+

# 2. Verify pgvector
psql -U postgres -c "SELECT * FROM pg_available_extensions WHERE name = 'vector';"

# 3. Create database
psql -U postgres -c "CREATE DATABASE infosubvenciones;"

# 4. Enable pgvector
psql -U postgres -d infosubvenciones -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

---

### Cache/Broker: Redis 7+

| Aspect | Details | Status |
|--------|---------|--------|
| **Provider** | Self-hosted Redis | ⚠️ Unknown |
| **Version Required** | 7+ | ⚠️ Verify |
| **Purpose** | Celery broker for task queue | Critical |
| **Connection String** | `redis://localhost:6379/0` | ⏳ Pending |

**Installation Options** (choose one if not installed):

1. **Windows (Chocolatey)**:
   ```bash
   choco install redis-64
   redis-server --service-start
   ```

2. **Windows (WSL2)**:
   ```bash
   sudo apt install redis-server
   sudo service redis-server start
   ```

3. **Docker** (easiest):
   ```bash
   docker run -d --name infosubvenciones-redis -p 6379:6379 redis:7-alpine
   ```

**Verification Steps**:
```bash
# Test Redis
redis-cli ping  # Should return "PONG"

# Test set/get
redis-cli SET test_key "hello"
redis-cli GET test_key  # Should return "hello"
```

**Status**: ⚠️ **TO-DO Day 2**: You need to run `redis-cli ping` and confirm

---

### LLM Provider: Google Gemini

| Aspect | Details | Status |
|--------|---------|--------|
| **Model** | Value of `GEMINI_MODEL` (default `gemini-2.5-flash-lite`) | ✅ |
| **Purpose** | PDF summarization (200-250 words) + field extraction | Core feature |
| **API Key** | `GEMINI_API_KEY=AIza...` | ✅ Confirmed |
| **Free Tier** | 2M tokens/min | Available |
| **Estimated Cost** | ~$70 for 136k PDFs (if exceeds free tier) | Acceptable |
| **Rate Limits** | 2M tokens/min | Monitor usage |

**API Key Location**: Store in `.env` file (Day 2)

**Test Command**:
```bash
curl -H "Content-Type: application/json" \
     -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
     "https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent?key=YOUR_KEY"
```

---

### Embedding Service: OpenAI

| Aspect | Details | Status |
|--------|---------|--------|
| **Model** | text-embedding-3-small | Chosen |
| **Dimensions** | 1536 | Standard |
| **Purpose** | Embed summaries for semantic search | Core feature |
| **API Key** | `OPENAI_API_KEY=sk-...` | ⏳ **PENDING - You need to obtain** |
| **Estimated Cost** | ~$1.23 for 136k summaries | Very cheap |
| **Rate Limits** | 3M tokens/min | Won't hit limit |

**Obtain API Key**:
1. Visit: https://platform.openai.com/api-keys
2. Create new secret key
3. Copy and store securely

**Test Command**:
```bash
curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer YOUR_KEY"
```

**Status**: ⚠️ **TO-DO**: You need to get this key for Week 2 (embeddings)

---

### Object Storage: Local Filesystem

| Aspect | Details | Status |
|--------|---------|--------|
| **Provider** | Local disk (not cloud) | Chosen for MVP |
| **PDF Storage** | `D:\IT workspace\infosubvenciones-api\Ingestion\data\pdfs\` | ⏳ Confirm path |
| **Markdown Storage** | `D:\IT workspace\infosubvenciones-api\Ingestion\data\markdown\` | ⏳ Auto-create |
| **Estimated Size** | 50GB PDFs + 5GB markdown = 55GB | Check disk space |
| **Future** | Consider S3/GCS for backup (optional) | Week 6+ |

**Disk Space Check**:
```bash
# Windows
dir "D:\IT workspace"

# Or check via File Explorer: Right-click drive > Properties
```

**Status**: ⏳ **TO-DO Day 2**: Confirm 60GB+ available

---

## 3. Supporting Systems

### CI/CD
- **Status**: Not implemented yet (MVP focus)
- **Future**: GitHub Actions for linting, testing, deployment (Week 6+)

### Monitoring/Logging
- **Ingestion Progress**: PostgreSQL queries (scripts/export_stats.py)
- **Celery Tasks**: Celery Flower (optional web UI)
- **Logs**: Structured JSON logs in `Ingestion/logs/ingestion.log`
- **Search API**: Django admin + log files
- **Future**: Grafana + Prometheus (optional)

### Secrets Management
- **Local Dev**: `.env` file (gitignored)
- **Rotation**: Manual for now
- **Production**: Move to Vault/AWS Secrets Manager (Week 6+)

### Access Control
- **Local Dev**: You only
- **Production**: TBD (add authentication when merging with ARTISTING)

---

## 4. Automation Scripts

### Foundation Week Scripts

| Script | Purpose | Prerequisites | Command |
|--------|---------|---------------|---------|
| `scripts/init_db.py` | Create database schema (4 tables + indexes) | PostgreSQL + pgvector ready | `python scripts/init_db.py` |
| `scripts/test_api.py` | Test InfoSubvenciones API with 10 items | .env file with API keys | `python scripts/test_api.py` |
| `scripts/test_pipeline.py` | End-to-end test with N items | All services ready | `python scripts/test_pipeline.py --limit 10` |
| `scripts/export_stats.py` | Show ingestion progress | Database populated | `python scripts/export_stats.py` |
| `scripts/run_ingestion.py` | Main orchestrator (full 136k) | Week 2-3 | `python scripts/run_ingestion.py` |

### Setup Scripts (to be created Day 2-3)

| Script | Purpose | Status |
|--------|---------|--------|
| `scripts/install_dependencies.sh` | Install system packages (PostgreSQL, Redis, Python, Node) | ⏳ Create |
| `scripts/setup_ingestion.sh` | Python venv, pip install, init DB | ⏳ Create |
| `scripts/start_celery.sh` | Start Celery workers (3 queues) | ⏳ Create |

---

## 5. Environment Variables Overview

### .env File Location
- **Path**: `D:\IT workspace\infosubvenciones-api\Ingestion\.env`
- **Template**: `.env.example` (to be created Day 2)
- **Status**: ⏳ Pending - Create Day 2

### Required Variables Checklist

**Database**:
- [ ] `DATABASE_URL` = `postgresql://[user]:[pass]@[host]:5432/infosubvenciones`

**Redis**:
- [ ] `REDIS_URL` = `redis://localhost:6379/0`

**API Keys**:
- [ ] `GEMINI_API_KEY` = `AIza...` ✅
- [ ] `OPENAI_API_KEY` = `sk-...` ⏳

**InfoSubvenciones API**:
- [ ] `API_BASE_URL` = `https://www.infosubvenciones.es/bdnstrans/api`
- [ ] `API_TIMEOUT` = `30`
- [ ] `API_MAX_RETRIES` = `3`

**Processing**:
- [ ] `BATCH_SIZE` = `100`
- [ ] `MAX_WORKERS` = `10`
- [ ] `PDF_STORAGE_PATH` = `./data/pdfs`
- [ ] `MARKDOWN_STORAGE_PATH` = `./data/markdown`

**LLM Settings**:
- [ ] `GEMINI_MODEL` = `gemini-2.5-flash-lite` (override in `.env` as needed)
- [ ] `GEMINI_TEMPERATURE` = `0.1`
- [ ] `SUMMARY_MIN_WORDS` = `200`
- [ ] `SUMMARY_MAX_WORDS` = `250`

**Embedding Settings**:
- [ ] `EMBEDDING_MODEL` = `text-embedding-3-small`
- [ ] `EMBEDDING_DIMENSION` = `1536`

**Retry Logic**:
- [ ] `MAX_RETRIES` = `3`
- [ ] `LOG_LEVEL` = `INFO`

---

## 6. Security & Compliance

### Data Classification
- **Source**: Public government data (InfoSubvenciones API)
- **Stored**: Grant metadata, PDFs, AI summaries
- **User Data**: None for MVP (public access, no login)
- **Sensitive**: API keys only (stored in .env, not committed to Git)

### Backups/DR
- **Database**: Manual PostgreSQL dumps (weekly recommended)
- **PDFs**: InfoSubvenciones API is source of truth (can re-download)
- **Restoration**: Re-run ingestion pipeline if needed
- **Future**: Automated backups to S3/GCS (Week 6+)

### Network Rules
- **Local Dev**: No firewall rules needed
- **Production**: TBD (HTTPS, rate limiting)

---

## 7. Outstanding Tasks

### Critical (Day 2 - Infrastructure Verification)
- [ ] **Verify Redis**: Run `redis-cli ping` → Install if needed
- [ ] **Verify PostgreSQL**: Check version >= 15, pgvector installed
- [ ] **Obtain OpenAI API Key**: Visit platform.openai.com
- [ ] **Create .env file**: Copy from .env.example (after created)
- [ ] **Check disk space**: Confirm 60GB+ available

### High Priority (Day 3 - Database Setup)
- [ ] **Create database**: `CREATE DATABASE infosubvenciones;`
- [ ] **Enable pgvector**: `CREATE EXTENSION vector;`
- [ ] **Run init_db.py**: Create 4 tables + indexes

### Medium Priority (Day 4-5)
- [ ] **Test API client**: Fetch 10 grants successfully
- [ ] **Set up Python venv**: Install requirements.txt
- [ ] **Start Celery workers**: Test with simple task

### Low Priority (Week 2+)
- [ ] Document manual backup process
- [ ] Set up Celery Flower for monitoring
- [ ] Consider S3 backup for PDFs

---

## Pre-Implementation Checklist

Before writing code, confirm:

- [ ] PostgreSQL 15+ installed with pgvector ✅ (confirmed)
- [ ] Redis installed and running ⏳ (verify Day 2)
- [ ] Gemini API key available ✅ (confirmed)
- [ ] OpenAI API key obtained ⏳ (pending)
- [ ] 60GB+ disk space available ⏳ (verify Day 2)
- [ ] Python 3.11+ installed ⏳ (verify Day 2)
- [ ] .env file created with all variables ⏳ (Day 2)

**Overall Status**: 🟡 **2/7 Complete** - Proceed to Day 2 verification

---

**Reference**: See [SPRINT_PLAN.md](SPRINT_PLAN.md) for detailed daily tasks
**Next Step**: Day 2 - Infrastructure Verification (you run Redis check, Claude creates .env template)
