# routers/plano_contas.py
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db_session
from dependencies import get_current_user
from models import Usuario
from schemas import (
    Page,
    PlanoContasCreate,
    PlanoContasRead,
    PlanoContasUpdate,
)
from services.plano_contas import PlanoContasService

router = APIRouter(prefix="/api/v1/plano-contas", tags=["Plano de Contas"])

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUser = Annotated[Usuario, Depends(get_current_user)]

@router.post("", response_model=PlanoContasRead, status_code=status.HTTP_201_CREATED)
async def criar_conta(payload: PlanoContasCreate, db: SessionDep, _: CurrentUser):
    return await PlanoContasService(db).criar(payload)

@router.get("", response_model=Page[PlanoContasRead])
async def listar_contas(
    db: SessionDep,
    _: CurrentUser,
    tipo: Optional[str] = None,
    natureza: Optional[str] = None,
    sintetica: Optional[bool] = None,
    parent_id: Optional[int] = None,
    ativo: Optional[bool] = None,
    busca: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    filtros = dict(
        tipo=tipo,
        natureza=natureza,
        sintetica=sintetica,
        parent_id=parent_id,
        ativo=ativo,
        busca=busca,
    )
    itens, total = await PlanoContasService(db).listar(
        limit=limit, offset=offset, **filtros
    )
    return {"items": itens, "total": total, "limit": limit, "offset": offset}

@router.get("/{conta_id}", response_model=PlanoContasRead)
async def obter_conta(conta_id: int, db: SessionDep, _: CurrentUser):
    return await PlanoContasService(db).obter(conta_id)

@router.put("/{conta_id}", response_model=PlanoContasRead)
async def atualizar_conta(
    conta_id: int, payload: PlanoContasUpdate, db: SessionDep, _: CurrentUser
):
    return await PlanoContasService(db).atualizar(conta_id, payload)

@router.delete("/{conta_id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_conta(conta_id: int, db: SessionDep, _: CurrentUser):
    await PlanoContasService(db).excluir(conta_id)
