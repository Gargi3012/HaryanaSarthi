import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from config import settings

DATABASE_URL = settings.DATABASE_URL

# Validate if DATABASE_URL is a valid SQL URI scheme to prevent environment collisions
if not (DATABASE_URL.startswith("sqlite://") or DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://")):
    print(f"[DATABASE WARNING] DATABASE_URL '{DATABASE_URL}' is not a valid SQL URI. Falling back to local SQLite.")
    DATABASE_URL = "sqlite:///./haryanasarthi.db"

# Normalize PostgreSQL URLs for SQLAlchemy + asyncpg
if DATABASE_URL.startswith("postgres://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("sqlite:///"):
    # Async SQLite uses sqlite+aiosqlite
    ASYNC_DATABASE_URL = DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
else:
    ASYNC_DATABASE_URL = DATABASE_URL

# Sync url resolving
SYNC_DATABASE_URL = DATABASE_URL
if SYNC_DATABASE_URL.startswith("postgres://"):
    SYNC_DATABASE_URL = SYNC_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Sync Configuration
connect_args = {}
if "sqlite" in SYNC_DATABASE_URL:
    connect_args = {"check_same_thread": False}
    engine = create_engine(SYNC_DATABASE_URL, connect_args=connect_args)
else:
    engine = create_engine(SYNC_DATABASE_URL, pool_size=10, max_overflow=20)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Async Configuration — aiosqlite does NOT support check_same_thread
if "sqlite" in ASYNC_DATABASE_URL:
    async_engine = create_async_engine(ASYNC_DATABASE_URL)
else:
    async_engine = create_async_engine(ASYNC_DATABASE_URL, pool_size=10, max_overflow=20)

# SQLAlchemy 2.x async_sessionmaker takes engine as first positional arg, no bind= kwarg
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

# Sync DB Dependency (for legacy routers)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Async DB Dependency (for new routers)
async def get_async_db():
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()