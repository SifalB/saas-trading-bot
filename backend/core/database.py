from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings

# Columns that existed in the old multi-tenant SaaS "users" table but were
# removed when the app became single-user. Dropped idempotently on startup so
# an already-deployed database matches the current model. Safe to delete this
# list (and the migration below) once every environment has been migrated.
_LEGACY_USER_COLUMNS = (
    "first_name", "last_name", "age", "phone",
    "address", "city", "country", "plan",
)

engine = create_async_engine(settings.async_database_url, echo=settings.DEBUG)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create all tables on startup, then drop obsolete legacy columns."""
    from backend.models import user, bot, trade  # noqa: F401 — registers models
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # One-time forward migration: relax the old single-tenant schema.
        for col in _LEGACY_USER_COLUMNS:
            await conn.execute(text(f'ALTER TABLE users DROP COLUMN IF EXISTS "{col}"'))
        # Additive migration for tables that already exist (create_all only
        # creates missing tables, it never alters existing ones).
        await conn.execute(text(
            'ALTER TABLE trades ADD COLUMN IF NOT EXISTS fees_usdt '
            'DOUBLE PRECISION NOT NULL DEFAULT 0'
        ))
