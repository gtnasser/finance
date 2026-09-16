import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database import Base
import models  # noqa: F401  # registra as tabelas no metadata

@pytest_asyncio.fixture
async def session():
    """Sessão async isolada por teste, com schema criado do zero."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # mantém a mesma conexão para o banco em memória
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as session:
        yield session

    await engine.dispose()