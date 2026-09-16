old="""
from typing import Annotated
import jwt

from dependencies import get_current_user, oauth2_scheme
""" 
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db_session
from dependencies import get_current_user
from models import Usuario
from schemas import Token, UsuarioCreate, UsuarioResponse
from security import (
    create_access_token,
    get_password_hash,
    validate_password_policy,
    verify_password,
)
router = APIRouter(prefix="/api/v1/auth", tags=["Autenticação"])

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUser = Annotated[Usuario, Depends(get_current_user)]

# ----- Rate limiting simples em memória (por e-mail) -----
LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 300  # 5 minutos
_login_attempts: dict[str, deque[datetime]] = defaultdict(deque)

def _checar_rate_limit(email: str) -> None:
    agora = datetime.now(timezone.utc)
    fila = _login_attempts[email]
    # Remove tentativas fora da janela
    while fila and (agora - fila[0]).total_seconds() > LOGIN_WINDOW_SECONDS:
        fila.popleft()
    if len(fila) >= LOGIN_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas de login. Aguarde alguns minutos.",
        )
    fila.append(agora)

# ---------- ----------


@router.post(
    "/register",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(payload: UsuarioCreate, db: SessionDep):
    """Endpoint utilitário para registrar um novo usuário no sistema."""

    # Em produção o registro aberto é desabilitado (404 esconde o endpoint)
    if settings.is_production:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurso não encontrado.",
        )

    try:
        validate_password_policy(payload.senha)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    existe = await db.scalar(select(Usuario).where(Usuario.email == payload.email))
    if existe:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado.",
        )

    usuario = Usuario(
        nome=payload.nome,
        email=payload.email,
        senha_hash=get_password_hash(payload.senha),
        ativo=True,
    )
    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)
    return usuario

@router.post("/token", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: SessionDep,
):
    """Gera o token de acesso OAuth2/JWT para o formulário de login."""
    
    _checar_rate_limit(form_data.username)

    usuario = await db.scalar(
        select(Usuario).where(Usuario.email == form_data.username)
    )

    # Padronizado em 401: inexistente, inativo OU senha errada
    if (
        usuario is None
        or not usuario.ativo
        or not verify_password(form_data.password, usuario.senha_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": usuario.email})
    return Token(access_token=token)

@router.get("/me", response_model=UsuarioResponse)
async def me(current_user: CurrentUser):
    """Retorna os dados do usuário autenticado no momento."""
    return current_user

