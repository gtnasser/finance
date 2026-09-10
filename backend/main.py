from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from database import init_db, AsyncSessionLocal
from models import Usuario
from security import get_password_hash
from routers import auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializa as tabelas do banco no startup
    await init_db()
    
    # Cria o usuário admin padrão caso não exista
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Usuario))
        if not result.scalars().first():
            user_admin = Usuario(
                nome="Administrador",
                email="admin@admin.com",
                senha_hash=get_password_hash("admin123")
            )
            session.add(user_admin)
            await session.commit()
            print("👤 Usuário inicial criado: admin@admin.com / admin123")
            
    yield

# Instância principal acessada pelo Uvicorn
app = FastAPI(
    title="API de Gestão Financeira",
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

@app.get("/")
def root():
    return {"message": "API Financeira Operacional"}

