from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load env variables before other imports
load_dotenv(dotenv_path="../.env")

from database import Base, engine, SessionLocal
from seed_data import create_dummy_users
from services.dataset_loader import dataset_loader

from routers import auth, users, onboarding, opportunities, eligibility, stats, chatbot

app = FastAPI(title="HaryanaSarthi API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        create_dummy_users(db)
        dataset_loader.load_all()
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "HaryanaSarthi backend is running"}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(onboarding.router)
app.include_router(opportunities.router)
app.include_router(eligibility.router)
app.include_router(stats.router)
app.include_router(chatbot.router)