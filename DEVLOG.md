# DEVLOG — HaryanaSarthi

> **Project**: HaryanaSarthi — AI-powered government opportunity discovery platform for Haryana citizens  
> **Stack**: FastAPI · PostgreSQL (Neon) · Groq LLM · Vanilla HTML/CSS/JS  
> **Repository**: [github.com/Gargi3012/HaryanaSarthi](https://github.com/Gargi3012/HaryanaSarthi)

---

## Project Journey Overview

```
MILESTONE 1  →  Project Setup & Data Collection
MILESTONE 2  →  Database Design & Data Migration
MILESTONE 3  →  Backend API Foundation
MILESTONE 4  →  Security Layer (Auth + JWT + BOLA)
MILESTONE 5  →  AI/LLM Integration (Groq)
MILESTONE 6  →  Vector Recommendations Engine
MILESTONE 7  →  Frontend Development
MILESTONE 8  →  Single Port Architecture & Deployment
MILESTONE 9  →  Bug Audit & Production Hardening
MILESTONE 10 →  Full Testing & Sign-off
```

---

## MILESTONE 1 — Project Setup & Data Collection

**Goal:** Finalize the project idea, collect datasets, and initialize the repository.

### What Was Done

- Project concept defined: A single platform for Haryana citizens to discover colleges, jobs, scholarships, internships, and government schemes based on their profile.
- Git repository initialized with an initial commit.
- Raw datasets collected and cleaned in CSV format:

| Dataset | Records | Description |
|---|---|---|
| `Colleges_cleaned.csv` | 100 | Haryana colleges with admission details |
| `Job&Exam_cleaned.csv` | 50,000 | HSSC, SSC, and competitive exam listings |
| `internships_cleaned.csv` | 1,000 | Government internship opportunities |
| `haryana_scholarships_cleaned.csv` | 1,652 | NSP + Haryana scholarship schemes |
| `schemes_cleaned.csv` | 115 | PM and state-level welfare schemes |

- Data cleaning notebooks created under `notebooks/` folder.
- `.gitignore` configured to exclude `.env`, `__pycache__`, `.db` files, and virtual environments.

### Commits
```
bad22e7  initial commit
f3d90b0  security: untrack .env and add comprehensive .gitignore
```

---

## MILESTONE 2 — Database Design & Data Migration

**Goal:** Define SQLAlchemy ORM models and migrate all CSV data into the database.

### What Was Done

**ORM Models defined in `backend/models.py`:**

| Model | Purpose | Key Fields |
|---|---|---|
| `User` | Authenticated citizen profile | user_id, age, category, income, state, percentage |
| `College` | Haryana college records | college_name, location, courses, min_percentage, embedding |
| `JobExam` | Job and exam listings | post_name, department, min/max_age, candidate_category |
| `Internship` | Internship opportunities | sector, duration, stipend, mode, embedding |
| `Scholarship` | Scholarship schemes | min_marks, income_limit, eligible_category, embedding |
| `Scheme` | Government welfare schemes | ministry, benefits, max_age, states, embedding |
| `OnboardingData` | Session-based user onboarding state | step1–4 completed/skipped flags |

**Dataset Loader (`backend/services/dataset_loader.py`):**
- Reads CSV files using pandas and performs bulk inserts into the database.
- Idempotent — already migrated records are skipped on re-run.

**Dual-engine database architecture:**
- **Sync engine** — used by seed scripts and one-off admin operations.
- **Async engine** — used by all FastAPI request handlers.

**`seed_data.py`** — Creates 3 dummy users for development and testing.

### Files Created
```
backend/models.py
backend/database.py
backend/seed_data.py
backend/services/dataset_loader.py
backend/data/cleaned/*.csv
```

### Commit
```
c4d1d49  feat(database): migrate opportunity CSVs into relational tables
```

---

## MILESTONE 3 — Backend API Foundation

**Goal:** Set up the FastAPI application and implement all core API endpoints.

### What Was Done

**`backend/main.py`** — Application entry point:
- Registers all routers with appropriate prefixes.
- Mounts the frontend static files directory.
- Startup event handler creates database tables and seeds dummy users.

**Routers implemented:**

| Router | Prefix | Responsibility |
|---|---|---|
| `stats.py` | `/stats` | Returns live record counts per table |
| `auth.py` | `/auth` | Login endpoint with JWT token issuance |
| `users.py` | `/user` | Profile read and update |
| `onboarding.py` | `/onboarding` | Session creation, step saving, completion |
| `opportunities.py` | `/opportunities` | AI-powered recommendations |
| `eligibility.py` | `/eligibility` | Category-specific eligibility checks |
| `chatbot.py` | `/chatbot` | LLM chat and document analysis |

**`backend/schemas.py`** — Pydantic request and response models:
- `LoginRequest`, `SaveStepRequest`, `ChatRequest`, `DocumentAnalysisRequest`
- `CollegeEligibilityRequest`, `JobEligibilityRequest`, `ScholarshipEligibilityRequest`, etc.

**`backend/config.py`** — Settings loader via `pydantic-settings`:
- Reads `DATABASE_URL`, `GROQ_API_KEY`, `REDIS_URL`, and `JWT_SECRET_KEY` from `.env`.

### Files Created
```
backend/main.py
backend/config.py
backend/schemas.py
backend/routers/stats.py
backend/routers/auth.py
backend/routers/users.py
backend/routers/onboarding.py
backend/routers/opportunities.py
backend/routers/eligibility.py
backend/routers/chatbot.py
```

### Commits
```
7695a0c  feat(stats): convert stats route to async with live SQL counters
5b91b31  feat(onboarding): convert onboarding service and endpoints to async
```

---

## MILESTONE 4 — Security Layer (Auth + JWT + BOLA)

**Goal:** Implement secure authentication, token-based access, and object-level authorization.

### What Was Done

**Password Hashing (`backend/services/auth_service.py`):**
- `bcrypt` library used for industry-standard password hashing.
- `hash_password(plain_text)` → stores bcrypt hash in the database.
- `verify_password(plain_text, stored_hash)` → validates login credentials.

**JWT Token Issuance:**
- On successful login, an `access_token` is generated using HS256 algorithm.
- Token payload includes `user_id` and an expiry timestamp.
- `JWT_SECRET_KEY` is loaded from `.env` — never hardcoded in source.

**BOLA Protection (Broken Object Level Authorization):**
- `GET /user/{user_id}` endpoint extracts the requesting user from the JWT token.
- If the requested `user_id` does not match the authenticated user → `403 Forbidden`.
- Prevents users from accessing or modifying other users' profiles.

**Frontend Token Handling:**
- On login, `access_token` is stored in `localStorage`.
- All subsequent API requests attach `Authorization: Bearer <token>` header automatically via the `apiRequest()` helper.

### Files Modified
```
backend/services/auth_service.py    ← bcrypt hashing + JWT generation
backend/routers/auth.py             ← Login endpoint
backend/routers/users.py            ← BOLA enforcement
frontend/js/script.js               ← Token storage and header injection
```

### Commit
```
51250d9  feat(security): implement bcrypt password hashing, JWT tokens, BOLA user routes
```

---

## MILESTONE 5 — AI/LLM Integration (Groq)

**Goal:** Integrate Groq-powered language models for conversational AI and document verification.

### What Was Done

**LLM Service (`backend/services/gemini_service.py`):**

- **Chat Completions** using `llama-3.3-70b-versatile`:
  - User profile context (name, category, state, education) is automatically injected into every prompt.
  - Responds in Hinglish by default to serve rural Haryana citizens effectively.
  - Answers questions about scholarships, jobs, colleges, and government schemes.

- **Document Analysis** using `llama-3.2-11b-vision-preview`:
  - Accepts Base64-encoded images or PDFs.
  - Validates document authenticity against a given scholarship or job opportunity.
  - Returns a structured assessment of document eligibility.

- **Embeddings** using HuggingFace Inference API:
  - Model: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
  - Supports multilingual queries including Hindi.
  - Falls back to a deterministic hash vector if HuggingFace API is unavailable.
  - Note: Groq does not provide an embeddings API endpoint.

**Rate Limiting (`backend/services/redis_service.py`):**
- Tracks request counts per client IP using Redis.
- Falls back to an in-memory dictionary if Redis is not configured.
- Default limit: 10 requests per 60 seconds per IP.

**Earlier Change:**
- Project initially integrated Google Gemini API.
- Fully replaced with Groq API following a user decision to switch providers.

### Files Created/Modified
```
backend/services/gemini_service.py   ← Groq LLM + Vision + Embeddings
backend/services/redis_service.py    ← Rate limiting (Redis + fallback)
backend/routers/chatbot.py           ← Async chat routing + background tasks
```

### Commits
```
c16f685  feat(ai): replace Google Gemini with Groq API, vision, and embeddings
f364ec9  feat(cache): add Redis service with local in-memory fallback
b596cbf  feat(chatbot): implement async Groq routing and BackgroundTasks for document analysis
```

---

## MILESTONE 6 — Vector Recommendations Engine

**Goal:** Build an AI-powered recommendation system that matches users to relevant opportunities.

### What Was Done

**Vector Similarity Search (`backend/services/ml_recommender.py`):**
1. Convert user onboarding data to a text description.
2. Generate an embedding vector for that description.
3. Compare against pre-computed embedding vectors stored in each database record.
4. Return top-12 results ranked by cosine similarity score.

**Opportunity Service (`backend/services/opportunity_service.py`):**
- Reads the user's onboarding session (user_type, looking_for, category, location).
- Determines which opportunity categories are relevant.
- Runs vector search across colleges, scholarships, internships, and schemes.
- Returns categorized results in a single API response.

**Eligibility Service (`backend/services/eligibility_service.py`):**
Implements a hybrid approach — strict SQL filters first, then vector ranking:

| Category | Filter Logic |
|---|---|
| Colleges | Percentage threshold, entrance exam type, mode of study |
| Jobs | Age range, candidate category, education requirement |
| Scholarships | Income limit, minimum marks, class level, category |
| Schemes | Max age, gender, state, category |
| Internships | Sector, mode, duration, percentage |
| Exams | Education required, state, candidate category |

**Embedding Backfill (`backend/scripts/generate_embeddings.py`):**
- Generates embeddings for all existing database records that lack them.
- Processes in batches of 20 and commits progressively.
- Uses HuggingFace API with local hash fallback.

### Files Created
```
backend/services/ml_recommender.py
backend/services/opportunity_service.py
backend/services/eligibility_service.py
backend/scripts/generate_embeddings.py
```

---

## MILESTONE 7 — Frontend Development

**Goal:** Build a clean, responsive, and visually polished frontend using only HTML, CSS, and JavaScript.

### What Was Done

**Pages implemented (`frontend/`):**

| Page | File | Purpose |
|---|---|---|
| Landing | `index.html` | Entry point with "Get Started" button |
| Onboarding Step 1–4 | `pages/onboarding/` | 4-step user profile questionnaire |
| Home | `home.html` | Personalized opportunity dashboard |
| Login | `auth.html` | User authentication form |
| Profile | `profile.html` | View and edit user profile |
| Dashboard | `dashboard.html` | Live stats charts and opportunity overview |
| Opportunities | `opportunities.html` | Filtered opportunity listing with cards |
| About / Contact | `about.html`, `contact.html` | Informational pages |

**`frontend/js/script.js`** — All frontend logic in one file:
- `apiRequest(url, options)` — Centralized API call wrapper with automatic JWT header injection.
- `startOnboarding()` — Creates a backend session and redirects to the first onboarding step.
- `loginUser()` — Submits credentials, stores the JWT token, and redirects to home.
- `loadStats()` — Fetches live database counts and renders them on the dashboard.
- `loadRecommendations()` — Fetches personalized opportunity cards and renders them.

**`frontend/css/style.css`** — Design system:
- Dark theme with glassmorphism card effects.
- CSS custom properties for consistent color tokens.
- Responsive grid layouts for all screen sizes.
- Smooth hover transitions and micro-animations.
- Dark mode toggle support via a secondary set of CSS variables.

### Commits
```
832a1ea  feat(frontend): navbar dark mode toggle, map click filtering, chatbot suggestion chips
f0146e3  style(theme): dark mode CSS variable overrides
da236bd  feat(frontend): JWT token storage and automatic header injection
e6744ab  feat(frontend): live database counts on dashboard charts
```

---

## MILESTONE 8 — Single Port Architecture & Deployment

**Goal:** Serve the frontend and backend from a single port to simplify deployment.

### What Was Done

**Single Port Setup:**
- FastAPI `StaticFiles` mounts the `frontend/` directory at the application root.
- `GET /` serves `index.html` directly.
- All API routes remain at their respective prefixes (`/auth`, `/stats`, `/chatbot`, etc.).
- Frontend JavaScript uses `window.location.origin` to dynamically resolve the API base URL — no hardcoded hostnames.

**Neon PostgreSQL Configuration:**
- Neon serverless PostgreSQL database created and provisioned.
- Connection URL added to `.env` in the format:
  ```
  DATABASE_URL=postgresql://<user>:<pass>@<host>/neondb?sslmode=require
  ```
- SSL connection is mandatory for Neon — handled at the database layer.

**`.env` Variables Required:**
```env
DATABASE_URL=postgresql://...neon.tech/neondb?sslmode=require
GROQ_API_KEY=gsk_...
JWT_SECRET_KEY=<random 64-char hex string>
REDIS_URL=                  # optional
```

### Commit
```
c5c217c  feat(deployment): mount static frontend files and resolve API origin dynamically
```

---

## MILESTONE 9 — Bug Audit & Production Hardening

**Goal:** Perform a complete pipeline audit, identify all bugs, and make the application production-ready.

### Bugs Identified and Fixed

| # | Severity | Bug | Root Cause | Fix Applied |
|---|---|---|---|---|
| 1 | Critical | Login always returns 401 | Seed data had `user_id = "user_id1"` but login used `"user1"` | Fixed `seed_data.py` to use `"user1"`, `"user2"`, `"user3"` |
| 2 | Critical | Recommendations route 404 | Test called `POST /opportunities/recommend` — correct route is `GET /opportunities/recommended` | Updated all callers to use the correct route |
| 3 | Critical | Groq embeddings returning 404 | Script called `https://api.groq.com/openai/v1/embeddings` — Groq has no embeddings API | Removed Groq gate; use HuggingFace embeddings only |
| 4 | High | Onboarding saves only 1 of 4 fields | `save_step()` used `elif` branches — only the step-matching branch ran | Rewrote to update all provided fields regardless of step number |
| 5 | High | `aiosqlite` engine crashes on startup | `connect_args={"check_same_thread": False}` passed to async engine — not supported by `aiosqlite` | Removed invalid `connect_args` from the async engine block |
| 6 | High | Document analysis returns 422 | `DocumentAnalysisRequest` requires `file_name` field — test payload omitted it | Added `file_name` to the test and frontend payload |
| 7 | Medium | CORS policy error in browsers | `allow_origins=["*"]` combined with `allow_credentials=True` is invalid per CORS spec | Set `allow_credentials=False` |
| 8 | Medium | `async_sessionmaker` misconfiguration | `bind=` keyword argument removed in SQLAlchemy 2.x | Changed to positional `async_sessionmaker(async_engine, class_=AsyncSession, ...)` |
| 9 | Medium | `passlib` incompatibility on Python 3.13 | `passlib`'s bcrypt wrapper raises `ValueError` with `bcrypt >= 5.0.0` | Replaced `passlib.CryptContext` with direct `bcrypt.hashpw()` / `bcrypt.checkpw()` calls |

### Infrastructure Bug — asyncpg SSL Parameter Crash

**Error:** `TypeError: connect() got an unexpected keyword argument 'sslmode'`

**Root Cause:** The Neon DB connection URL contains `?sslmode=require&channel_binding=require`. The `asyncpg` driver does not accept these as URL query parameters — it requires SSL to be passed via `connect_args`.

**Fix — `_strip_ssl_params()` helper in `database.py`:**
```python
def _strip_ssl_params(url: str) -> tuple[str, bool]:
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    needs_ssl = params.pop("sslmode", ["disable"])[0] in ("require", "verify-ca", "verify-full", "prefer")
    params.pop("channel_binding", None)
    clean_url = urlunparse(...)
    return clean_url, needs_ssl
```

SSL context is then passed via:
```python
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    connect_args={"ssl": ssl.create_default_context()},
    pool_pre_ping=True,
    pool_recycle=300,
)
```

### Infrastructure Bug — Neon Idle Connection Drops

**Error:** `asyncpg.InterfaceError: connection is closed`

**Root Cause:** Neon's serverless PostgreSQL silently drops idle TCP connections. When a previously idle connection was reused (e.g., on `GET /stats` after a period of inactivity), SQLAlchemy returned the dead connection from the pool.

**Fix:** Added `pool_pre_ping=True` and `pool_recycle=300` to the async engine configuration. This ensures every connection is health-checked before use and recycled every 5 minutes.

### Commits
```
eea95e4  fix(security): native bcrypt directly to avoid passlib Python 3.13 incompatibility
1b57105  fix(bugs): 6 critical pipeline bugs fixed in one pass
998698c  fix(database): strip sslmode/channel_binding for asyncpg, pass ssl via connect_args
5f030d5  fix(database): add pool_pre_ping=True + pool_recycle=300 for Neon idle connection drops
```

---

## MILESTONE 10 — Full Testing & Sign-off

**Goal:** Verify that every feature works correctly on the live server against the production database.

### Test Infrastructure

Three test scripts were created:

| Script | Description |
|---|---|
| `test_endpoints.py` | TestClient-based integration tests — no live server required |
| `live_server_test.py` | 8 end-to-end HTTP tests against the running server |
| `full_project_test.py` | 19 comprehensive live server tests across all features |

### Final Results — 19/19 Tests Passed

| Section | Tests | Result |
|---|---|---|
| Core Infrastructure | Landing page, Swagger docs, OpenAPI schema | 3/3 |
| Database & Stats | All 5 table counts verified against expected minimums | 1/1 |
| Authentication | Valid login, wrong password, unknown user, unauthenticated block | 4/4 |
| User Profile | Own profile fetch with JWT, BOLA 403 cross-user access | 2/2 |
| Onboarding Flow | Session creation, multi-field save, step skip | 3/3 |
| Vector Recommendations | SC student, General student, OBC job seeker | 3/3 |
| AI Chatbot | Hinglish query, English query, rate limit check | 3/3 |
| **Total** | | **19/19** |

### Production Data Verified

```
Colleges      :     100
Jobs / Exams  :  50,000
Scholarships  :   1,652
Internships   :   1,000
Schemes       :     115
─────────────────────────
Total Records :  52,867
```

### Commits
```
5db58da  test: add comprehensive 19-test full project test suite
ed93e7b  docs: initial DEVLOG.md
```

---

## Final Architecture

```
HaryanaSarthi/
│
├── frontend/                        ← Vanilla HTML + CSS + JavaScript
│   ├── index.html                   ← Landing page
│   ├── auth.html                    ← Login form
│   ├── home.html                    ← Personalized opportunity home
│   ├── dashboard.html               ← Live stats and charts
│   ├── profile.html                 ← User profile view/edit
│   ├── opportunities.html           ← Filtered opportunity listing
│   ├── pages/onboarding/            ← 4-step onboarding questionnaire
│   ├── css/style.css                ← Dark theme design system
│   └── js/script.js                 ← All frontend logic
│
└── backend/                         ← FastAPI application
    ├── main.py                      ← App entry point + static file mount
    ├── config.py                    ← Environment variable loader
    ├── database.py                  ← Sync + Async SQLAlchemy engines
    ├── models.py                    ← ORM table definitions
    ├── schemas.py                   ← Pydantic request/response models
    ├── seed_data.py                 ← Development user seeding
    ├── routers/
    │   ├── auth.py                  ← Login + JWT issuance
    │   ├── users.py                 ← Profile + BOLA enforcement
    │   ├── onboarding.py            ← Session management
    │   ├── opportunities.py         ← AI recommendations
    │   ├── eligibility.py           ← Category eligibility checks
    │   ├── chatbot.py               ← Groq LLM + Vision analysis
    │   └── stats.py                 ← Live database counters
    ├── services/
    │   ├── auth_service.py          ← bcrypt hashing + JWT creation
    │   ├── gemini_service.py        ← Groq LLM, Vision, Embeddings
    │   ├── redis_service.py         ← Cache and rate limiting
    │   ├── ml_recommender.py        ← Cosine similarity vector search
    │   ├── opportunity_service.py   ← Recommendation orchestration
    │   ├── eligibility_service.py   ← SQL + vector hybrid filtering
    │   ├── onboarding_service.py    ← Session CRUD operations
    │   └── dataset_loader.py        ← CSV to database migration
    ├── scripts/
    │   └── generate_embeddings.py   ← Batch embedding backfill
    └── data/cleaned/                ← Source CSV datasets
```

---

## Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `DATABASE_URL` | Yes | Neon PostgreSQL connection string |
| `GROQ_API_KEY` | Yes | Groq API key for LLM and Vision |
| `JWT_SECRET_KEY` | Yes | Secret key for JWT token signing |
| `REDIS_URL` | No | Redis URL for rate limiting (in-memory fallback if absent) |

---

## Seeded Test Users

| user_id | Password | Name | Category | Role |
|---|---|---|---|---|
| `user1` | `gargi123` | Gargi Sharma | General | Student, Age 20 |
| `user2` | `gargi123` | Dev Rohilla | OBC | Job Seeker, Age 22 |
| `user3` | `gargi123` | Aditi Khasa | SC | Student, Age 24 |

---

## Run Commands

```bash
# First-time setup
cd d:\HaryanaSarthi
python -m venv .venv
.venv\Scripts\pip install -r backend\requirements.txt

# Start the server (run from the backend/ directory)
D:\HaryanaSarthi\.venv\Scripts\uvicorn.exe main:app --port 8000

# Open in browser
http://localhost:8000/

# Run the comprehensive test suite (server must be running)
D:\HaryanaSarthi\.venv\Scripts\python.exe backend\scratch\full_project_test.py

# Run integration tests (no live server required)
D:\HaryanaSarthi\.venv\Scripts\python.exe backend\scratch\test_endpoints.py
```

---

## Complete Commit History

| # | Hash | Type | Description |
|---|---|---|---|
| 1 | `bad22e7` | chore | Initial commit |
| 2 | `ad6c773` | fix | Remove GEMINI_API_KEY from .env |
| 3 | `51250d9` | feat | bcrypt hashing, JWT tokens, BOLA user routes |
| 4 | `c4d1d49` | feat | CSV migration to database + vector similarity ranking |
| 5 | `f364ec9` | feat | Redis service with in-memory fallback |
| 6 | `b596cbf` | feat | Async Groq chatbot + BackgroundTasks for document analysis |
| 7 | `5b91b31` | feat | Async onboarding service and endpoints |
| 8 | `7695a0c` | feat | Async stats route with live SQL counters |
| 9 | `da236bd` | feat | JWT token storage in frontend |
| 10 | `e6744ab` | feat | Live database counts on dashboard |
| 11 | `c5c217c` | feat | Single port static file mount |
| 12 | `f0146e3` | style | Dark mode CSS variable overrides |
| 13 | `832a1ea` | feat | Dark mode toggle, map filtering, chatbot chips |
| 14 | `c16f685` | feat | Replace Google Gemini with Groq API |
| 15 | `da74409` | fix | Use GROQ_API_KEY check in embedding script |
| 16 | `f3d90b0` | security | Add .gitignore and untrack .env |
| 17 | `e3cbf12` | fix | Call load_dotenv on script startup |
| 18 | `30c4b72` | fix | Auto-initialize tables in embedding script |
| 19 | `5fabae4` | fix | Validate DATABASE_URL scheme on startup |
| 20 | `245bf3f` | fix | Remove invalid field from Scheme model |
| 21 | `eea95e4` | fix | Native bcrypt for Python 3.13 compatibility |
| 22 | `1b57105` | fix | 6 critical pipeline bugs resolved |
| 23 | `998698c` | fix | asyncpg SSL parameter handling for Neon DB |
| 24 | `5f030d5` | fix | Connection pool pre-ping and recycle |
| 25 | `5db58da` | test | 19-test comprehensive project test suite |
| 26 | `ed93e7b` | docs | DEVLOG.md (initial version) |
| 27 | `latest` | docs | DEVLOG.md rewritten in English, milestone format |
