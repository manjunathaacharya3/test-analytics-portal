import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from database.base import Base

# Import all models so they are registered with Base

# Load environment variables
load_dotenv()

# DB URLs
POSTGRES_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:password@localhost:5432/test_portal"
)
SQLITE_URL = "sqlite+aiosqlite:///./test_portal.db"

# Global engine + session
engine = None
async_session = None


async def create_engine_with_fallback():
    """Try Postgres, fallback to SQLite if connection fails."""
    try:
        engine = create_async_engine(POSTGRES_URL, echo=True, future=True)
        # Test connection
        async with engine.begin() as conn:
            await conn.run_sync(lambda _: None)
        print("✅ Connected to Postgres")
        return engine
    except Exception as e:
        print(f"⚠️ Could not connect to Postgres, falling back to SQLite. Error: {e}")
        return create_async_engine(SQLITE_URL, echo=True, future=True)


async def init_engine():
    """Initialize engine and session globally"""
    global engine, async_session
    engine = await create_engine_with_fallback()
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    """Dependency injection for DB sessions"""
    async with async_session() as session:
        yield session


async def init_db():
    """Create all tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created successfully!")
