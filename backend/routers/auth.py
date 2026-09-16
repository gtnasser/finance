from typing import Annotated
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db_session
from models import Usuario
from schemas import Token, UsuarioCreate, UsuarioResponse
from config import settings

from security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from dependencies import get_current_user, oauth2_scheme

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticação"])

@router.post("/register", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UsuarioCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    """Endpoint utilitário para registrar um novo usuário no sistema."""
    stmt = select(Usuario).where(Usuario.email == user_in.email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-mail já cadastrado no sistema."
        )

    novo_usuario = Usuario(
        nome=user_in.nome,
        email=user_in.email,
        senha_hash=get_password_hash(user_in.senha)
    )
    db.add(novo_usuario)
    await db.commit()
    await db.refresh(novo_usuario)
    return novo_usuario


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    """Gera o token de acesso OAuth2/JWT para o formulário de login."""
    # O campo 'username' do OAuth2PasswordRequestForm recebe o e-mail
    stmt = select(Usuario).where(Usuario.email == form_data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário inativo."
        )

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UsuarioResponse)
async def read_users_me(
    current_user: Annotated[Usuario, Depends(get_current_user)]
):
    """Retorna os dados do usuário autenticado no momento."""
    return current_user