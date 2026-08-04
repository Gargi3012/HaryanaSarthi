import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from database import Base, engine, SessionLocal
from seed_data import create_dummy_users
from services.dataset_loader import dataset_loader

from routers import auth, users, onboarding, opportunities, eligibility, stats, chatbot

app = FastAPI(title="HaryanaSarthi API")

# Configure CORS (still helpful for external developers testing APIs)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Cannot use True with wildcard origins per CORS spec
    allow_methods=["*"],
    allow_headers=["*"],
)

# Synchronously ensure tables are created during startup
Base.metadata.create_all(bind=engine)


@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        create_dummy_users(db)
        dataset_loader.load_all()
        dataset_loader.migrate_to_db(db)
    finally:
        db.close()


# Include API routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(onboarding.router)
app.include_router(opportunities.router)
app.include_router(eligibility.router)
app.include_router(stats.router)
app.include_router(chatbot.router)

# Mount frontend static files on the same port at the root path '/'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")