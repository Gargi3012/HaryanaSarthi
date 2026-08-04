# HaryanaSarthi 🌾

**AI-powered portal to discover government opportunities — Schemes, Scholarships, Jobs, Exams, Internships & Colleges — personalized to your profile.**

> Built for Haryana citizens. Powered by Groq LLM, Neon PostgreSQL, and Vector Similarity Search.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat&logo=python)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-336791?style=flat&logo=postgresql)](https://neon.tech)
[![Groq](https://img.shields.io/badge/LLM-Groq%20Llama--3.3-F55036?style=flat)](https://groq.com)

---

## Overview

HaryanaSarthi is a full-stack web application that helps Haryana citizens find government opportunities they are eligible for — all in one place. Users complete a short onboarding questionnaire, and the AI engine recommends personalized colleges, jobs, scholarships, internships, and schemes based on their age, category, education, location, and income.

---

## System Architecture

```mermaid
graph TB
    User([🧑 Citizen / User])

    subgraph Frontend ["Frontend  —  Vanilla HTML · CSS · JS"]
        LP[Landing Page]
        OB[Onboarding Flow\n4-Step Questionnaire]
        HOME[Home Dashboard\nPersonalized Cards]
        CHAT[AI Chatbot\nHinglish Support]
        ELIGI[Eligibility Checker\n6 Categories]
        DASH[Analytics Dashboard\nLive Charts]
    end

    subgraph Backend ["Backend  —  FastAPI + Python 3.13"]
        AUTH[Auth Router\n/auth/login]
        ONB[Onboarding Router\n/onboarding/...]
        OPP[Opportunities Router\n/opportunities/recommended]
        CB[Chatbot Router\n/chatbot/...]
        EL[Eligibility Router\n/eligibility/...]
        STATS[Stats Router\n/stats]
    end

    subgraph Services ["Service Layer"]
        VS[Vector Similarity\nml_recommender.py]
        ES[Eligibility Filters\neligibility_service.py]
        LS[Groq LLM Service\ngemini_service.py]
        RS[Rate Limiter\nredis_service.py]
        DS[Dataset Loader\ndataset_loader.py]
    end

    subgraph Database ["Database  —  Neon PostgreSQL"]
        UT[(Users)]
        CL[(Colleges\n100 records)]
        JE[(Jobs & Exams\n50,000 records)]
        SC[(Scholarships\n1,652 records)]
        IN[(Internships\n1,000 records)]
        SM[(Schemes\n115 records)]
        OD[(Onboarding\nSessions)]
    end

    subgraph External ["External APIs"]
        GROQ[Groq API\nLlama-3.3-70b\nLlama-3.2-Vision]
        HF[HuggingFace\nEmbeddings API]
        REDIS[(Redis\nRate Limiting)]
    end

    User --> Frontend
    Frontend -->|HTTP + JWT| Backend
    Backend --> Services
    Services --> Database
    Services --> External
```

---

## Request Flow — Personalized Recommendations

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant API as FastAPI
    participant OB as Onboarding Service
    participant ML as ML Recommender
    participant DB as Neon PostgreSQL
    participant HF as HuggingFace Embeddings

    User->>FE: Completes 4-step onboarding
    FE->>API: POST /onboarding/session/{id}/save-step
    API->>OB: save_step(session_id, payload)
    OB->>DB: UPDATE onboarding_data SET ...
    DB-->>OB: OK

    User->>FE: Navigates to Home
    FE->>API: GET /opportunities/recommended?user_type=...&category=...
    API->>ML: get_recommended_opportunities(db, profile)
    ML->>HF: embed("Student SC Hisar Scholarships")
    HF-->>ML: [0.12, 0.87, ...]  embedding vector
    ML->>DB: SELECT * FROM scholarships, colleges...
    DB-->>ML: All records with stored embeddings
    ML-->>API: Top-12 results (cosine similarity ranked)
    API-->>FE: JSON {colleges:[], scholarships:[], ...}
    FE-->>User: Renders personalized opportunity cards
```

---

## Authentication Flow

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant API as FastAPI
    participant AUTH as Auth Service
    participant DB as Neon PostgreSQL

    User->>FE: Enter user_id + password
    FE->>API: POST /auth/login {user_id, password}
    API->>DB: SELECT * FROM users WHERE user_id=?
    DB-->>API: User record (hashed password)
    API->>AUTH: verify_password(plain, bcrypt_hash)
    AUTH-->>API: True / False

    alt Valid Credentials
        API->>AUTH: create_access_token(user_id)
        AUTH-->>API: JWT token (HS256)
        API-->>FE: {access_token, name, ...}
        FE->>FE: localStorage.setItem("access_token", token)
        FE-->>User: Redirect to /home.html
    else Invalid Credentials
        API-->>FE: 401 Unauthorized
        FE-->>User: Show error message
    end

    Note over FE,API: All subsequent requests include Authorization: Bearer <token>
```

---

## AI Chatbot Pipeline

```mermaid
flowchart LR
    MSG([User Message]) --> RL{Rate Limit\nCheck}
    RL -->|Exceeded| E429[429 Too Many Requests]
    RL -->|OK| PROFILE[Fetch User Profile\nfrom DB]
    PROFILE --> CTX[Build Context\nname + category + state\n+ income + education]
    CTX --> GROQ[Groq API\nllama-3.3-70b-versatile]
    GROQ --> REPLY[Hinglish Response]
    REPLY --> USER([User sees reply])

    DOCMSG([Upload Document]) --> VISION[Groq Vision\nllama-3.2-vision]
    VISION --> ANALYSIS[Document Gap Analysis\nagainst opportunity]
    ANALYSIS --> USER
```

---

## Database Schema

```mermaid
erDiagram
    USERS {
        string user_id PK
        string name
        int age
        string category
        float income
        string state
        string location_preference
        string hashed_password
        float percentage
        string education_level
    }

    ONBOARDING_DATA {
        string session_id PK
        string user_type
        string looking_for
        string category
        string location_preference
        bool step1_completed
        bool step2_completed
        bool step3_completed
        bool step4_completed
        bool step1_skipped
        bool step2_skipped
    }

    COLLEGES {
        int id PK
        string college_name
        string location
        string courses_offered
        float tuition_fees
        float min_percentage_required
        string embedding
    }

    JOB_EXAMS {
        int id PK
        string post_name
        string department
        int min_age
        int max_age
        string candidate_category
        string education_required
        string embedding
    }

    SCHOLARSHIPS {
        int id PK
        string scholarship_name
        float income_limit
        int min_marks_required
        string eligible_category
        float annual_scholarship_amount
        string embedding
    }

    SCHEMES {
        int id PK
        string scheme_name
        string ministry
        string benefits
        string category
        string embedding
    }

    INTERNSHIPS {
        int id PK
        string internship_role
        string sector
        int stipend_per_month_inr
        string mode
        string embedding
    }

    USERS ||--o{ ONBOARDING_DATA : "has sessions"
```

---

## Features

| Feature | Description |
|---|---|
| 🧠 **AI Recommendations** | Vector cosine similarity matching across 52,867 records |
| 💬 **Groq Chatbot** | Hinglish LLM responses using Llama-3.3-70b |
| 📄 **Document Analysis** | Upload documents for gap analysis (Llama-3.2-Vision) |
| 🗺️ **Haryana Map** | District-based opportunity filtering |
| 🔐 **JWT Authentication** | Secure login with bcrypt + BOLA protection |
| 🎯 **Eligibility Checker** | Rule-based filters for all 6 opportunity categories |
| 📊 **Live Dashboard** | Real-time database counts and category charts |
| 🌙 **Dark Mode** | Full dark/light theme toggle |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.13, FastAPI, SQLAlchemy 2.x (async) |
| Database | Neon PostgreSQL (asyncpg driver) |
| AI / LLM | Groq API — `llama-3.3-70b` (chat), `llama-3.2-vision` (docs) |
| Embeddings | HuggingFace Inference API → local hash fallback |
| Auth | JWT (HS256) + bcrypt (native, no passlib) |
| Cache / Rate Limiting | Redis → in-memory fallback |
| Frontend | Vanilla HTML, CSS, JavaScript |
| Charts | Chart.js |

---

## Dataset Summary

| Dataset | Records | Description |
|---|---|---|
| `Colleges_cleaned.csv` | 100 | Haryana colleges with admission criteria |
| `Job&Exam_cleaned.csv` | 50,000 | HSSC, SSC, and competitive exams |
| `internships_cleaned.csv` | 1,000 | Government internship programs |
| `haryana_scholarships_cleaned.csv` | 1,652 | NSP + Haryana state scholarships |
| `schemes_cleaned.csv` | 115 | Central and state welfare schemes |
| **Total** | **52,867** | |

---

## Project Structure

```
HaryanaSarthi/
│
├── .env                              # Environment variables (git-ignored)
├── .gitignore
├── DEVLOG.md                         # Full project development log
├── README.md
│
├── backend/
│   ├── main.py                       # FastAPI entry point + static mount
│   ├── config.py                     # .env settings loader
│   ├── database.py                   # Sync + Async SQLAlchemy engines (SSL)
│   ├── models.py                     # ORM table definitions
│   ├── schemas.py                    # Pydantic request/response models
│   ├── seed_data.py                  # Development user seeding
│   ├── requirements.txt
│   │
│   ├── routers/
│   │   ├── auth.py                   # Login + JWT issuance
│   │   ├── users.py                  # Profile + BOLA enforcement
│   │   ├── onboarding.py             # Session management
│   │   ├── opportunities.py          # AI recommendations
│   │   ├── eligibility.py            # Category eligibility checks
│   │   ├── chatbot.py                # Groq LLM + Vision
│   │   └── stats.py                  # Live database counters
│   │
│   ├── services/
│   │   ├── auth_service.py           # bcrypt + JWT
│   │   ├── gemini_service.py         # Groq LLM, Vision, Embeddings
│   │   ├── redis_service.py          # Cache + rate limiting
│   │   ├── ml_recommender.py         # Cosine similarity vector search
│   │   ├── opportunity_service.py    # Recommendation orchestration
│   │   ├── eligibility_service.py    # SQL + vector hybrid filtering
│   │   ├── onboarding_service.py     # Session CRUD
│   │   └── dataset_loader.py         # CSV → database migration
│   │
│   ├── scripts/
│   │   └── generate_embeddings.py    # Batch embedding backfill
│   │
│   └── data/
│       └── cleaned/                  # Source CSV datasets
│
├── frontend/
│   ├── index.html                    # Landing page
│   ├── auth.html                     # Login
│   ├── home.html                     # Recommendations dashboard
│   ├── dashboard.html                # Live stats + charts
│   ├── profile.html                  # User profile
│   ├── opportunities.html            # Browse all categories
│   ├── about.html
│   ├── contact.html
│   ├── pages/
│   │   ├── onboarding/               # 4-step onboarding flow
│   │   └── eligibility/              # 6 eligibility checker pages
│   ├── css/style.css                 # Dark theme design system
│   └── js/script.js                  # All frontend logic
│
└── notebooks/                        # Data cleaning and exploration
```

---

## Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/Gargi3012/HaryanaSarthi.git
cd HaryanaSarthi
```

### 2. Create a Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux
```

### 3. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:
```env
DATABASE_URL=postgresql://<user>:<password>@<host>/neondb?sslmode=require
GROQ_API_KEY=gsk_...
JWT_SECRET_KEY=<generate a random 64-character hex string>
REDIS_URL=                    # optional — leave blank to use in-memory fallback
```

### 5. Start the Server
```bash
# Run from the backend/ directory
cd backend
uvicorn main:app --port 8000
```

- App: **http://localhost:8000/**
- API Docs: **http://localhost:8000/docs**

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/` | — | Landing page (frontend) |
| GET | `/stats` | — | Live database record counts |
| POST | `/auth/login` | — | Login and receive JWT token |
| GET | `/user/{user_id}` | ✅ JWT | Fetch user profile (BOLA protected) |
| POST | `/onboarding/session/create` | — | Create onboarding session |
| POST | `/onboarding/session/{id}/save-step` | — | Save onboarding step fields |
| GET | `/onboarding/session/{id}` | — | Read session state |
| POST | `/onboarding/session/{id}/complete` | — | Mark onboarding complete |
| GET | `/opportunities/recommended` | — | AI-ranked recommendations |
| POST | `/eligibility/colleges` | — | College eligibility check |
| POST | `/eligibility/jobs` | — | Job eligibility check |
| POST | `/eligibility/exams` | — | Exam eligibility check |
| POST | `/eligibility/internships` | — | Internship eligibility check |
| POST | `/eligibility/scholarships` | — | Scholarship eligibility check |
| POST | `/eligibility/schemes` | — | Government scheme eligibility |
| POST | `/chatbot/general` | — | General AI chatbot (Hinglish) |
| POST | `/chatbot/analyze-document` | — | Document gap analysis (Vision) |
| GET | `/docs` | — | Swagger API documentation |

---

## Test Users (Development)

| user_id | Password | Name | Category |
|---|---|---|---|
| `user1` | `gargi123` | Gargi Sharma | General, Student |
| `user2` | `gargi123` | Dev Rohilla | OBC, Job Seeker |
| `user3` | `gargi123` | Aditi Khasa | SC, Student |

---

## Running Tests

```bash
# Comprehensive live server test (19 tests — server must be running)
python backend/scratch/full_project_test.py

# Integration tests (no live server required)
python backend/scratch/test_endpoints.py
```

**Latest test result: 19/19 PASSED ✅**

---

## License

This project is built for educational and demonstration purposes.
