import os

from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    pass


# Default to a local SQLite file so `uvicorn` works on a clean machine with no
# database server. Set DATABASE_URL to a postgresql+asyncpg:// URL in any
# environment that has one.
DEFAULT_SQLITE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "orca.db",
)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{DEFAULT_SQLITE_PATH}")

# Supabase often adds ?pgbouncer=true, which asyncpg does not support as a kwarg
if "pgbouncer=true" in DATABASE_URL.lower():
    DATABASE_URL = DATABASE_URL.replace("?pgbouncer=true", "").replace("&pgbouncer=true", "")

IS_SQLITE = DATABASE_URL.startswith("sqlite")

engine_kwargs = {"echo": False, "future": True}
if not IS_SQLITE:
    # Disable prepared statement caching which crashes Supabase PgBouncer transaction poolers
    engine_kwargs["connect_args"] = {
        "statement_cache_size": 0,
    }

engine = create_async_engine(DATABASE_URL, **engine_kwargs)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db():
    async with async_session() as session:
        yield session
