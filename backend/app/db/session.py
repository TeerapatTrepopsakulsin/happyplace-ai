import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Import all models to ensure they are registered with SQLAlchemy
import app.models  # noqa: F401

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://localhost/happyplaceai")

engine = create_async_engine(DATABASE_URL, future=True, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
