from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.config import get_settings

_engine = None
_factory = None


def engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
    return _engine


def factory():
    global _factory
    if _factory is None:
        _factory = async_sessionmaker(engine(), expire_on_commit=False)
    return _factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
