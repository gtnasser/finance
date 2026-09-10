from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# SQLite:
DATABASE_URL = "sqlite+aiosqlite:///./contas_pagar.db"
# PostgreSQL: "postgresql+asyncpg://usuario:senha@localhost:5432/nome_banco"
# DATABASE_URL = "postgresql+asyncpg://usuario:senha@localhost:5432/nome_banco"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Altere para True se quiser ver o SQL gerado no terminal
    future=True
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
    """Cria todas as tabelas no banco de dados se não existirem."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)