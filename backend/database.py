from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings

# Parâmetros de pool só fazem sentido para bancos remotos (Postgres)
engine_kwargs: dict = {}
if settings.is_production:
    engine_kwargs.update(
        pool_pre_ping=True,   # descarta conexões mortas antes de usar
        pool_size=5,
        max_overflow=10,
    )


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Altere para True se quiser ver o SQL gerado no terminal
    **engine_kwargs,
)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

class Base(DeclarativeBase):
    """Classe base declarativa para os modelos ORM."""
    pass

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection para sessões no FastAPI ou rotinas async."""
    async with AsyncSessionLocal() as session:
        yield session

async def init_db() -> None:
    """
    Bootstrap do schema. Uso exclusivo em desenvolvimento (produção usa Alembic).
    Cria todas as tabelas no banco de dados se não existirem.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)