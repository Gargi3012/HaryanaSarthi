# HaryanaSarthi 🌾

**AI-powered portal to discover Government Opportunities — Schemes, Scholarships, Jobs, Exams, Internships & Colleges — tailored to your profile.**

---

## 📸 Features

- 🧠 **AI Eligibility Engine** — ML-based recommendations using cosine similarity ranking
- 💬 **Gemini-powered Chatbot** — Career Path AI, Life Event AI, and General Guide modes
- 📄 **Next Best Action AI** — Upload a document and get gap analysis for any opportunity
- 🗺️ **Interactive Haryana Map** — District-based opportunity explorer
- 🔐 **User Authentication** — Login, profile, and onboarding preference tracking
- 📊 **Dashboard** — Visual insights on opportunities, users, and regions

---

## 🗂️ Project Structure

```
HaryanaSarthi/
├── .env                        # API keys (Gemini, etc.)
├── .venv/                      # Python virtual environment
│
├── backend/
│   ├── data/
│   │   ├── cleaned/            # CSV datasets used by the app
│   │   │   ├── Colleges_cleaned.csv
│   │   │   ├── Job&Exam_cleaned.csv
│   │   │   ├── internships_cleaned.csv
│   │   │   ├── haryana_scholarships_cleaned.csv
│   │   │   └── schemes_cleaned.csv
│   │   └── raw/                # Original Excel source files
│   ├── routers/                # FastAPI route handlers
│   │   ├── auth.py
│   │   ├── chatbot.py
│   │   ├── eligibility.py
│   │   ├── onboarding.py
│   │   ├── opportunities.py
│   │   ├── stats.py
│   │   └── users.py
│   ├── services/               # Business logic & ML
│   │   ├── dataset_loader.py
│   │   ├── eligibility_service.py
│   │   ├── gemini_service.py
│   │   ├── ml_recommender.py
│   │   ├── onboarding_service.py
│   │   └── opportunity_service.py
│   ├── scripts/
│   │   └── update_nav.py       # Utility script
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── seed_data.py
│   └── requirements.txt
│
├── frontend/
│   ├── index.html              # Landing page
│   ├── home.html               # Home / recommendations
│   ├── opportunities.html      # Browse all categories
│   ├── dashboard.html          # Analytics dashboard
│   ├── auth.html               # Login / Sign up
│   ├── profile.html            # User profile
│   ├── about.html
│   ├── contact.html
│   ├── pages/
│   │   ├── onboarding/         # Onboarding flow (4 steps)
│   │   │   ├── onboarding1.html
│   │   │   ├── onboarding2.html
│   │   │   ├── onboarding3.html
│   │   │   └── onboarding4.html
│   │   └── eligibility/        # AI eligibility checkers
│   │       ├── eligibility_colleges.html
│   │       ├── eligibility_exams.html
│   │       ├── eligibility_internships.html
│   │       ├── eligibility_jobs.html
│   │       ├── eligibility_schemes.html
│   │       └── eligibility_scholarships.html
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   ├── script.js           # Main frontend logic
│   │   └── dashboard.js        # Chart logic
│   └── assets/
│       └── logo.jpeg
│
└── notebooks/                  # Data exploration notebooks
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy |
| AI / ML | Google Gemini API, cosine similarity |
| Database | SQLite (`haryanasarthi.db`) |
| Data | Pandas, CSV datasets |
| Frontend | HTML, CSS, Vanilla JS |
| Charts | Chart.js |

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone <repo-url>
cd HaryanaSarthi
```

### 2. Set Up Environment Variables
Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_google_gemini_api_key
```

### 3. Install Python Dependencies
```bash
# Activate the virtual environment
.venv\Scripts\activate        # Windows
# OR
source .venv/bin/activate     # macOS/Linux

# Install requirements
pip install -r backend/requirements.txt
```

### 4. Run the Backend
```bash
cd backend
python -m uvicorn main:app --reload
```
API runs at: **http://127.0.0.1:8000**  
Swagger docs at: **http://127.0.0.1:8000/docs**

### 5. Open the Frontend
Open `frontend/index.html` in your browser directly, or serve it with any static file server:
```bash
# Example using Python's built-in server (from frontend/ folder)
python -m http.server 5500
```
Then visit **http://localhost:5500**

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/login` | User login |
| POST | `/onboarding/session/create` | Start onboarding session |
| POST | `/onboarding/session/{id}/save-step` | Save onboarding step |
| POST | `/onboarding/session/{id}/complete` | Complete onboarding |
| GET | `/opportunities/recommended` | Get personalized recommendations |
| POST | `/eligibility/colleges` | College eligibility check |
| POST | `/eligibility/jobs` | Job eligibility check |
| POST | `/eligibility/exams` | Exam eligibility check |
| POST | `/eligibility/internships` | Internship eligibility check |
| POST | `/eligibility/scholarships` | Scholarship eligibility check |
| POST | `/eligibility/schemes` | Government scheme eligibility |
| POST | `/chatbot/general` | General chatbot |
| POST | `/chatbot/career` | Career Path AI |
| POST | `/chatbot/life-event` | Life Event AI |
| POST | `/chatbot/analyze-document` | NBA document analysis |

---

## 📊 Datasets

| Dataset | Description |
|---|---|
| `Colleges_cleaned.csv` | Haryana government colleges |
| `Job&Exam_cleaned.csv` | Government jobs & competitive exams |
| `internships_cleaned.csv` | Government internship opportunities |
| `haryana_scholarships_cleaned.csv` | India-wide government scholarships |
| `schemes_cleaned.csv` | Central & state government schemes |

---

## 📝 License

This project is for educational and demonstration purposes.
