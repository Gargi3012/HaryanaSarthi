import os
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from config import settings

DATABASE_URL = settings.DATABASE_URL

# Validate if DATABASE_URL is a valid SQL URI scheme to prevent environment collisions
if not (DATABASE_URL.startswith("sqlite://") or DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://")):
    print(f"[DATABASE WARNING] DATABASE_URL '{DATABASE_URL}' is not a valid SQL URI. Falling back to local SQLite.")
    DATABASE_URL = "sqlite:///./haryanasarthi.db"

def _strip_ssl_params(url: str) -> tuple[str, bool]:
    """
    asyncpg does NOT accept sslmode= or channel_binding= as query params.
    Strip them and return (clean_url, needs_ssl).
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    needs_ssl = params.pop("sslmode", ["disable"])[0] in ("require", "verify-ca", "verify-full", "prefer")
    params.pop("channel_binding", None)
    new_query = urlencode({k: v[0] for k, v in params.items()})
    clean = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
    return clean, needs_ssl

# Normalize PostgreSQL URLs for SQLAlchemy + asyncpg
_needs_asyncpg_ssl = False
if DATABASE_URL.startswith("postgres://"):
    _clean, _needs_asyncpg_ssl = _strip_ssl_params(DATABASE_URL)
    ASYNC_DATABASE_URL = _clean.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    _clean, _needs_asyncpg_ssl = _strip_ssl_params(DATABASE_URL)
    ASYNC_DATABASE_URL = _clean.replace("postgresql://", "postgresql+asyncpg://", 1)
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
elif _needs_asyncpg_ssl:
    # asyncpg requires ssl= connect_arg, NOT sslmode= query param
    import ssl as _ssl
    _ssl_ctx = _ssl.create_default_context()
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL,
        connect_args={"ssl": _ssl_ctx},
        pool_size=10,
        max_overflow=20
    )
    print("[DATABASE] Async PostgreSQL engine configured with SSL (asyncpg).")
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