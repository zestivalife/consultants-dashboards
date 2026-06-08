import asyncio
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.base import Base
from app.db.models import Role, User, AuthAuditLog  # noqa: F401
from app.db.models.refresh_token import RefreshToken  # noqa: F401
from app.db.models.otp_verification import OTPVerification  # noqa: F401
from app.db.models.consent import Consent  # noqa: F401
from app.core.security import hash_password


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        yield sess
        await sess.rollback()


@pytest_asyncio.fixture
async def seed_role(session: AsyncSession) -> Role:
    role = Role(id=uuid.uuid4(), name="member", description="Default member role")
    session.add(role)
    await session.flush()
    return role


@pytest_asyncio.fixture
async def seed_user(session: AsyncSession, seed_role: Role) -> User:
    user = User(
        id=uuid.uuid4(),
        email="test@nuetra.com",
        password_hash=hash_password("Correct123!"),
        role_id=seed_role.id,
        is_verified=True,
    )
    session.add(user)
    await session.flush()
    return user
