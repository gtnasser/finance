# repositories/contas_correntes.py
from typing import Optional, Sequence

from models import ContaCorrente
from repositories.base import BaseRepository

class ContaCorrenteRepository(BaseRepository[ContaCorrente]):
    model = ContaCorrente

    def _filtros(self, *, ativo, plano_conta_id, busca) -> list:
        conds: list = []
        if ativo is not None:
            conds.append(ContaCorrente.ativo == ativo)
        if plano_conta_id is not None:
            conds.append(ContaCorrente.plano_conta_id == plano_conta_id)
        if busca:
            like = f"%{busca}%"
            from sqlalchemy import or_

            conds.append(
                or_(
                    ContaCorrente.nome.ilike(like),
                    ContaCorrente.banco.ilike(like),
                )
            )
        return conds

    async def chave_em_uso(
        self,
        banco: str,
        agencia: str,
        numero: str,
        ignorar_id: Optional[int] = None,
    ) -> bool:
        stmt = self._base_stmt().where(
            ContaCorrente.banco == banco,
            ContaCorrente.agencia == agencia,
            ContaCorrente.numero == numero,
        )
        if ignorar_id is not None:
            stmt = stmt.where(ContaCorrente.id != ignorar_id)
        return (await self.session.execute(stmt)).scalars().first() is not None

    async def existe_vinculo_plano(self, plano_conta_id: int) -> bool:
        stmt = self._base_stmt().where(
            ContaCorrente.plano_conta_id == plano_conta_id
        )
        return (await self.session.execute(stmt)).scalars().first() is not None

    async def listar(self, *, limit=50, offset=0, **filtros) -> Sequence[ContaCorrente]:
        return await self.list(
            limit=limit,
            offset=offset,
            order_by=(ContaCorrente.nome,),
            filters=self._filtros(**filtros),
        )

    async def contar(self, **filtros) -> int:
        return await self.count(filters=self._filtros(**filtros))