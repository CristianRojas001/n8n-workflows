# READ THIS FIRST - InfoSubvenciones Project

**Status**: 🟡 Day 1 Complete - Infrastructure Verification Required

---

## 🎯 What We've Done (Day 1 - Planning)

✅ **All planning documentation complete**:
- [PROJECT_PLAN.md](PROJECT_PLAN.md) - Vision, 6-week roadmap, scope
- [APP_STRUCTURE.md](APP_STRUCTURE.md) - Technical architecture
- [RAG_PIPELINE.md](RAG_PIPELINE.md) - Ingestion pipeline specs
- [UX_SURFACES.md](UX_SURFACES.md) - UI design
- [SPRINT_PLAN.md](SPRINT_PLAN.md) - Week 1 daily breakdown
- [INFRASTRUCTURE_CHECKLIST.md](INFRASTRUCTURE_CHECKLIST.md) - Infrastructure guide
- [PROGRESS_LOG.md](PROGRESS_LOG.md) - Session journal

---

## 🚨 CRITICAL: What You Must Do Before Next Session

**DO NOT SKIP THIS STEP**

Run these 4 commands and report the results:

```bash
# 1. Check Redis
redis-cli ping

# 2. Check Python version
python --version

# 3. Check disk space (Windows)
powershell "Get-PSDrive D | Select-Object Used,Free"

# 4. Check PostgreSQL version
psql --version
```

### Why This Matters

The second opinion was correct: we have **complete documentation but ZERO code and unverified infrastructure**. Starting to code without verifying these 4 things would be inefficient because:

1. **No Redis** = Celery workers won't start = ingestion can't run
2. **Wrong Python version** = Dependencies won't install
3. **No disk space** = Can't store 50GB of PDFs
4. **Wrong PostgreSQL** = pgvector won't work

---

## 📊 Current Status

| Component | Status | Next Action |
|-----------|--------|-------------|
| **Documentation** | ✅ Complete | None - done |
| **PostgreSQL + pgvector** | ✅ Confirmed | Create database Day 2 |
| **Gemini API Key** | ✅ Confirmed | Add to .env Day 2 |
| **Redis** | ⚠️ Unknown | **YOU: Run `redis-cli ping`** |
| **Python 3.11+** | ⚠️ Unknown | **YOU: Run `python --version`** |
| **Disk Space (60GB+)** | ⚠️ Unknown | **YOU: Check free space** |
| **OpenAI API Key** | ⚠️ Pending | **YOU: Get from platform.openai.com** |
| **Code** | ❌ None | Blocked until infra verified |

---

## 🔄 What Happens Next

### If All 4 Commands Succeed

Claude will:
1. Create `Ingestion/` project structure
2. Create `.env.example` template
3. Create `requirements.txt`
4. Write database init script
5. Test with 10 grants (smoke test)

### If Any Command Fails

We'll install/fix the missing component first, THEN proceed to coding.

---

## 📋 Project Overview (Quick Reference)

**Goal**: Build TWO integrated RAG systems within ARTISTING platform

### System 1: InfoSubvenciones RAG
- 136k Spanish government grants
- Semantic search + filters
- Chat interface integration

### System 2: Legal RAG
- BOE, CENDOJ, PETETE legal documents
- Legal/fiscal/labor advice
- Separate database, same chat UI

**Tech Stack**:
- **Backend**: Python + Django REST + Celery + PostgreSQL + pgvector
- **Integration**: Existing ARTISTING (auth, CRM, chat UI)
- **AI**: Gemini 2.0 Flash (summaries) + OpenAI embeddings (search)

**Timeline**: 2 Milestones (42 days / 6 weeks)
- **Milestone 1 (21 days)**: Prototype with 10→100→1,000 grants + Legal RAG subset (€1,500)
- **Milestone 2 (21 days)**: Full 136k grants + Full Legal corpus (€2,000)

**Cost**: ~$75 total for ingestion

---

## 📖 Document Guide

**Start here**:
1. [INFRASTRUCTURE_CHECKLIST.md](INFRASTRUCTURE_CHECKLIST.md) - Run the 4 commands at the top
2. [SPRINT_PLAN.md](SPRINT_PLAN.md) - See daily tasks for Week 1

**For understanding architecture**:
3. [PROJECT_PLAN.md](PROJECT_PLAN.md) - Overall vision and scope
4. [APP_STRUCTURE.md](APP_STRUCTURE.md) - Technical details
5. [RAG_PIPELINE.md](RAG_PIPELINE.md) - How ingestion works

**For UI design**:
6. [UX_SURFACES.md](UX_SURFACES.md) - Pages, components, flows

**For tracking progress**:
7. [PROGRESS_LOG.md](PROGRESS_LOG.md) - Session notes (updated after each session)

---

## ⚡ Quick Commands (For Reference)

```bash
# Check all infrastructure at once
redis-cli ping && python --version && psql --version && powershell "Get-PSDrive D | Select-Object Used,Free"

# When infrastructure is ready (Day 3+):
cd "D:\IT workspace\infosubvenciones-api\Ingestion"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python scripts/init_db.py
python scripts/test_pipeline.py --limit 10
```

---

## 🎯 Success Criteria for Day 2

- [ ] All 4 infrastructure commands succeed
- [ ] Redis installed and running (if wasn't already)
- [ ] Database `infosubvenciones` created
- [ ] pgvector extension enabled
- [ ] `.env` file created with all keys
- [ ] OpenAI API key obtained

**Only then** can we proceed to Day 3 (coding).

---

## 🆘 If You Get Stuck

**Redis not installed?** See [INFRASTRUCTURE_CHECKLIST.md](INFRASTRUCTURE_CHECKLIST.md) section 2.2 for 3 installation options (Chocolatey, WSL, Docker)

**Wrong Python version?** Download 3.11+ from <https://www.python.org/downloads/>

**No disk space?** Free up 60GB or choose different storage location

**PostgreSQL issues?** Check [INFRASTRUCTURE_CHECKLIST.md](INFRASTRUCTURE_CHECKLIST.md) section 2.1 troubleshooting

---

**Last Updated**: 2025-12-01
**Next Step**: Run the 4 critical commands above and report results
