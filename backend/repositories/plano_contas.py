# repositories/plano_contas.py
from typing import Optional, Sequence

from sqlalchemy import or_

from models import PlanoContas
from repositories.base import BaseRepository

class PlanoContasRepository(BaseRepository[PlanoContas]):
    model = PlanoContas

    def _filtros(self, *, tipo, natureza, sintetica, parent_id, ativo, busca) -> list:
        conds: list = []
        if tipo is not None:
            conds.append(PlanoContas.tipo == tipo)
        if natureza is not None:
            conds.append(PlanoContas.natureza == natureza)
        if sintetica is not None:
            conds.append(PlanoContas.sintetica == sintetica)
        if parent_id is not None:
            conds.append(PlanoContas.parent_id == parent_id)
        if ativo is not None:
            conds.append(PlanoContas.ativo == ativo)
        if busca:
            like = f"%{busca}%"
            conds.append(
                or_(
                    PlanoContas.codigo.ilike(like),
                    PlanoContas.descricao.ilike(like),
                )
            )
        return conds

    async def get_by_codigo(self, codigo: str) -> Optional[PlanoContas]:
        stmt = self._base_stmt().where(PlanoContas.codigo == codigo)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def codigo_em_uso(self, codigo: str, ignorar_id: Optional[int] = None) -> bool:
        stmt = self._base_stmt().where(PlanoContas.codigo == codigo)
        if ignorar_id is not None:
            stmt = stmt.where(PlanoContas.id != ignorar_id)
        return (await self.session.execute(stmt)).scalars().first() is not None

    async def tem_filhos(self, conta_id: int) -> bool:
        stmt = self._base_stmt().where(PlanoContas.parent_id == conta_id)
        return (await self.session.execute(stmt)).scalars().first() is not None

    async def listar(self, *, limit=50, offset=0, **filtros) -> Sequence[PlanoContas]:
        return await self.list(
            limit=limit,
            offset=offset,
            order_by=(PlanoContas.codigo,),
            filters=self._filtros(**filtros),
        )

    async def contar(self, **filtros) -> int:
        return await self.count(filters=self._filtros(**filtros))