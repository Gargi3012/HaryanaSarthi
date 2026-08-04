import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from config import settings

DATABASE_URL = settings.DATABASE_URL

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

# Async Configuration
async_connect_args = {}
if "sqlite" in ASYNC_DATABASE_URL:
    async_connect_args = {"check_same_thread": False}
    async_engine = create_async_engine(ASYNC_DATABASE_URL, connect_args=async_connect_args)
else:
    async_engine = create_async_engine(ASYNC_DATABASE_URL, pool_size=10, max_overflow=20)

AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    class_=AsyncSession
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