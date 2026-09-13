from logger import setup_logger, logger

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from database import init_db, AsyncSessionLocal
from models import Usuario
from security import get_password_hash
from routers import auth

# Inicializa as configurações do Loguru
setup_logger()

# Parametriza usuario inicial
ADMIN_INITIAL_USER="Administrador"
ADMIN_INITIAL_EMAIL="admin@admin.com"
ADMIN_INITIAL_PASSWORD="admin123"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializa as tabelas do banco no startup
    logger.info("Iniciando a API...")
    await init_db()

    # Cria o usuário admin padrão caso não exista
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Usuario))
        if not result.scalars().first():
            user_admin = Usuario(
                nome=ADMIN_INITIAL_USER,
                email=ADMIN_INITIAL_EMAIL,
                senha_hash=get_password_hash(ADMIN_INITIAL_PASSWORD)
            )
            session.add(user_admin)
            await session.commit()
            logger.info(f"👤 Usuário inicial criado: {ADMIN_INITIAL_USER}")
        logger.info("Banco de dados verificado/inicializado.")

    yield  # <--- A aplicação RODA enquanto fica pausada neste ponto
    logger.info("Encerrando a API")
    

# Instância principal acessada pelo Uvicorn
app = FastAPI(
    title="Financing API",
    version="1.0.0",
    lifespan=lifespan
)

# Habilita CORS para o Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui os roteadores
app.include_router(auth.router)

# rotas

@app.get("/")
async def root():
    logger.debug("Endpoint raiz '/' foi acessado.")
    return {"message": "Financing API is running"}


