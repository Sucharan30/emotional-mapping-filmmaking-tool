"""
db.py — Async SQLAlchemy 2.0 engine and session dependency.

Connection choice: Supabase TRANSACTION POOLER (port 6543, pgBouncer).
  - Reason: Render's network may not reliably reach Supabase's direct
    connection (port 5432) due to IPv6-only addressing.
  - pgBouncer in transaction mode does NOT support prepared statements,
    so we set prepared_statement_cache_size=0 in asyncpg connect_args.

DATABASE_URL must be the Supabase transaction pooler URI:
  postgresql+asyncpg://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres

Find this URL in:
  Supabase Dashboard -> Project Settings -> Database
  -> Connection pooling -> Transaction -> URI
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)

from config import settings

# asyncpg connect_args:
#   prepared_statement_cache_size=0 is required for pgBouncer
#   transaction pooler (Supabase's default pooling mode).
_CONNECT_ARGS: dict = {"prepared_statement_cache_size": 0}

engine = create_async_engine(
    settings.async_database_url,
    pool_pre_ping=True,           # verify connections before use
    connect_args=_CONNECT_ARGS,
    echo=(settings.env == "development"),  # log SQL in dev only
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # keep objects usable after commit
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency: yields an async database session.
    Rolls back automatically if an unhandled exception is raised.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
