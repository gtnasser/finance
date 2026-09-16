from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from config import settings
from database import engine, init_db, AsyncSessionLocal
from exceptions import BusinessRuleError, ConflictError, NotFoundError
from logger import setup_logger
from routers import auth, conta_corrente, plano_contas
from seed import seed_all

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ----- Startup -----
    setup_logger()
    if not settings.is_production:

        # O Schema vem do Alembic (alembic upgrade head). 
        # Os dados vem do seed.
        async with AsyncSessionLocal() as session:
            resultado = await seed_all(session)
            logger.info(
                f"Seed: admin_criado={resultado['admin_criado']}, "
                f"plano_contas={resultado['plano_contas_criadas']}"
            )

    yield
    # ----- Shutdown -----
    await engine.dispose()

app = FastAPI(
    title="FINANCING API",
    version="0.1.0",
    lifespan=lifespan,
)

# ----- CORS (permite o Streamlit consumir a API) -----
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- Handlers de exceções de domínio -----
@app.exception_handler(NotFoundError)
async def not_found_handler(_: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.exception_handler(ConflictError)
async def conflict_handler(_: Request, exc: ConflictError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})

@app.exception_handler(BusinessRuleError)
async def business_rule_handler(_: Request, exc: BusinessRuleError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})

# ----- Routers -----
app.include_router(auth.router)
app.include_router(plano_contas.router)
app.include_router(conta_corrente.router)
