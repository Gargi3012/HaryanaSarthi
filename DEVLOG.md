# DEVLOG — HaryanaSarthi

> Developer log tracking all major changes, bug fixes, and milestones across the project lifecycle.

---

## [2026-08-04] — Full Pipeline Audit & Bug Fix Session

### Summary
Performed a complete end-to-end audit of the entire codebase acting as Developer + Backend Developer + QA Tester. Found and fixed **9 critical/high bugs** that were blocking the project from running correctly against the live Neon PostgreSQL database.

---

### Bugs Fixed

#### 🔴 CRITICAL

**BUG-001 — `user_id` mismatch in seed data**
- **File**: `backend/seed_data.py`
- **Problem**: Seeded users had `user_id = "user_id1"` but frontend/tests used `"user1"`
- **Fix**: Changed to `"user1"`, `"user2"`, `"user3"`
- **Effect**: Login always returned `401 Invalid credentials`

**BUG-003 — Wrong route for recommendations**
- **File**: `backend/scratch/test_endpoints.py`
- **Problem**: Test called `POST /opportunities/recommend` — real route is `GET /opportunities/recommended`
- **Fix**: Updated test to use correct GET endpoint

**BUG-018 — `generate_embeddings.py` called non-existent Groq embeddings endpoint**
- **File**: `backend/scripts/generate_embeddings.py`
- **Problem**: Script blocked on missing `GROQ_API_KEY` + called `https://api.groq.com/openai/v1/embeddings` (404 — Groq has no embeddings API)
- **Fix**: Removed Groq API key gate; embeddings now use HuggingFace → local hash fallback

---

#### 🟠 HIGH

**BUG-004 — Onboarding `save_step()` dropped 3 out of 4 fields**
- **File**: `backend/services/onboarding_service.py`
- **Problem**: Used `elif` branches — Step 1 only saved `user_type`, steps 2/3/4 saved remaining fields one each. Frontend sends all 4 in one request.
- **Fix**: Rewrote to update all provided fields regardless of step number

**BUG-005 — `aiosqlite` got invalid `check_same_thread` arg**
- **File**: `backend/database.py`
- **Problem**: `connect_args={"check_same_thread": False}` passed to async SQLite engine — `aiosqlite` doesn't support this arg
- **Fix**: Removed invalid `connect_args` block for async engine

**BUG-006 — `file_name` missing from document analysis test**
- **File**: `backend/scratch/test_endpoints.py`
- **Problem**: `DocumentAnalysisRequest` schema requires `file_name: str` but test didn't send it → `422 Unprocessable Entity`
- **Fix**: Added `file_name` to test payload

---

#### 🟡 MEDIUM

**BUG-009 — CORS `allow_origins=["*"]` + `allow_credentials=True`**
- **File**: `backend/main.py`
- **Problem**: Invalid combination per CORS spec — browsers reject this
- **Fix**: Set `allow_credentials=False`

**BUG-010 — `async_sessionmaker` used deprecated `bind=` kwarg**
- **File**: `backend/database.py`
- **Problem**: SQLAlchemy 2.x `async_sessionmaker` does not accept `bind=` — causes silent misconfiguration
- **Fix**: Changed to `async_sessionmaker(async_engine, class_=AsyncSession, ...)`

---

### Infrastructure Fixes

**asyncpg `sslmode` parameter crash**
- **File**: `backend/database.py`
- **Problem**: Neon DB URL contains `?sslmode=require&channel_binding=require` — `asyncpg` does not accept these as query params, requires `connect_args={"ssl": ssl_ctx}`
- **Fix**: Added `_strip_ssl_params()` helper that strips `sslmode`/`channel_binding` from URL and passes `ssl=ssl.create_default_context()` via `connect_args`
- **Effect**: All async DB endpoints (stats, login, onboarding, chatbot) were returning `500 TypeError: connect() got an unexpected keyword argument 'sslmode'`

**Neon DB idle connection drops**
- **File**: `backend/database.py`
- **Problem**: Neon serverless PostgreSQL drops idle connections silently — `asyncpg.InterfaceError: connection is closed`
- **Fix**: Added `pool_pre_ping=True` + `pool_recycle=300` (5 minutes) to async engine
- **Effect**: `GET /stats` was returning 500 after first successful batch of requests

---

### Auth Service Migration

**`passlib` incompatibility with Python 3.13**
- **File**: `backend/services/auth_service.py`
- **Problem**: `passlib`'s bcrypt wrapper has a version detection bug on `bcrypt >= 5.0.0` / Python 3.13, raising `ValueError: Invalid salt`
- **Fix**: Replaced `passlib.context.CryptContext` with direct `bcrypt.hashpw()` / `bcrypt.checkpw()` calls
- **Result**: Password hashing and verification now works correctly on Python 3.13

---

### Test Infrastructure

Created two test scripts:

**`backend/scratch/test_endpoints.py`** — TestClient integration tests (no live server needed)
- Tests stats, auth, profile, onboarding, recommendations, chatbot, vision

**`backend/scratch/live_server_test.py`** — 8 live server HTTP tests
- Requires server running on port 8000

**`backend/scratch/full_project_test.py`** — 19 comprehensive live server tests
- Section 1: Core Infrastructure (3 tests)
- Section 2: Database & Stats (1 test)
- Section 3: Authentication (4 tests)
- Section 4: User Profile (2 tests)
- Section 5: Onboarding Flow (3 tests)
- Section 6: Vector Recommendations (3 tests)
- Section 7: AI Chatbot (3 tests)

**Final Result: 19/19 TESTS PASSED ✅**

---

### Commits This Session

| Hash | Message |
|---|---|
| `1b57105` | fix(bugs): fix critical pipeline bugs — user_id mismatch, aiosqlite connect_args, CORS credentials, async_sessionmaker bind, onboarding multi-field save, generate_embeddings Groq endpoint |
| `998698c` | fix(database): strip sslmode/channel_binding from Neon DB async URL, use ssl=True connect_args for asyncpg compatibility |
| `5f030d5` | fix(database): add pool_pre_ping=True + pool_recycle=300 to prevent Neon DB idle connection drops on stats endpoint |
| `5db58da` | test: add comprehensive 19-test full project test suite covering all features |

---

## Stack Reference

| Layer | Technology |
|---|---|
| Backend | FastAPI + Python 3.13 |
| Database | Neon PostgreSQL (async via asyncpg + SQLAlchemy 2.x) |
| Auth | JWT (HS256) + bcrypt (native, no passlib) |
| AI/LLM | Groq API — `llama-3.3-70b` (chat) + `llama-3.2-vision` (doc analysis) |
| Embeddings | HuggingFace Inference API → local hash fallback |
| Cache/Rate Limit | Redis → in-memory fallback |
| Frontend | Vanilla HTML + CSS + JS |

## Login Credentials (Seeded Users)

| user_id | Password |
|---|---|
| `user1` | `gargi123` |
| `user2` | `gargi123` |
| `user3` | `gargi123` |

## Run Commands

```bash
# Start server (from backend/ directory)
D:\HaryanaSarthi\.venv\Scripts\uvicorn.exe main:app --port 8000

# Run full test suite (from project root, server must be running)
D:\HaryanaSarthi\.venv\Scripts\python.exe backend\scratch\full_project_test.py

# Run TestClient tests (no live server needed)
D:\HaryanaSarthi\.venv\Scripts\python.exe backend\scratch\test_endpoints.py
```
