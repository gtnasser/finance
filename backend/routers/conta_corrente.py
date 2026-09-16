# routers/contas.py
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db_session
from dependencies import get_current_user
from models import Usuario
from schemas import (
    ContaCorrenteCreate,
    ContaCorrenteRead,
    ContaCorrenteUpdate,
    Page,
)
from services.conta_corrente import ContaCorrenteService

router = APIRouter(prefix="/api/v1/contas", tags=["Contas Correntes"])

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUser = Annotated[Usuario, Depends(get_current_user)]

@router.post("", response_model=ContaCorrenteRead, status_code=status.HTTP_201_CREATED)
async def criar_conta(payload: ContaCorrenteCreate, db: SessionDep, _: CurrentUser):
    return await ContaCorrenteService(db).criar(payload)

@router.get("", response_model=Page[ContaCorrenteRead])
async def listar_contas(
    db: SessionDep,
    _: CurrentUser,
    ativo: Optional[bool] = None,
    plano_conta_id: Optional[int] = None,
    busca: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    itens, total = await ContaCorrenteService(db).listar(
        limit=limit,
        offset=offset,
        ativo=ativo,
        plano_conta_id=plano_conta_id,
        busca=busca,
    )
    return {"items": itens, "total": total, "limit": limit, "offset": offset}

@router.get("/{conta_id}", response_model=ContaCorrenteRead)
async def obter_conta(conta_id: int, db: SessionDep, _: CurrentUser):
    return await ContaCorrenteService(db).obter(conta_id)

@router.put("/{conta_id}", response_model=ContaCorrenteRead)
async def atualizar_conta(
    conta_id: int, payload: ContaCorrenteUpdate, db: SessionDep, _: CurrentUser
):
    return await ContaCorrenteService(db).atualizar(conta_id, payload)

@router.delete("/{conta_id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_conta(conta_id: int, db: SessionDep, _: CurrentUser):
    await ContaCorrenteService(db).excluir(conta_id)
