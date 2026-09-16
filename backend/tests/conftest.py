import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database import Base, get_db_session
from main import app
import models  # noqa: F401  # registra as tabelas no metadata


@pytest_asyncio.fixture
async def session():
    """Sessão async isolada por teste, com schema criado do zero."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # mesma conexão para o banco em memória
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def client(session):
    """Cliente HTTP contra a app FastAPI, com o banco em memória do teste."""
    async def override_get_db():
        yield session

    app.dependency_overrides[get_db_session] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
