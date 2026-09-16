# services/conta_corrente.py
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions import BusinessRuleError, ConflictError, NotFoundError
from models import ContaCorrente
from repositories.conta_corrente import ContaCorrenteRepository
from repositories.plano_contas import PlanoContasRepository
from schemas import ContaCorrenteCreate, ContaCorrenteUpdate

class ContaCorrenteService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ContaCorrenteRepository(session)
        self.plano_repo = PlanoContasRepository(session)

    async def criar(self, dados: ContaCorrenteCreate) -> ContaCorrente:
        await self._validar_plano(dados.plano_conta_id)
        if await self.repo.chave_em_uso(dados.banco, dados.agencia, dados.numero):
            raise ConflictError(
                "Já existe uma conta com este banco, agência e número."
            )

        conta = ContaCorrente(**dados.model_dump())
        await self.repo.add(conta)
        await self.session.commit()
        await self.session.refresh(conta)
        return conta

    async def obter(self, conta_id: int) -> ContaCorrente:
        conta = await self.repo.get(conta_id)
        if conta is None:
            raise NotFoundError("Conta corrente", conta_id)
        return conta

    async def listar(self, *, limit: int = 50, offset: int = 0, **filtros):
        itens: Sequence[ContaCorrente] = await self.repo.listar(
            limit=limit, offset=offset, **filtros
        )
        total = await self.repo.contar(**filtros)
        return itens, total

    async def atualizar(
        self, conta_id: int, dados: ContaCorrenteUpdate
    ) -> ContaCorrente:
        conta = await self.obter(conta_id)
        valores = dados.model_dump(exclude_unset=True)

        if (
            "plano_conta_id" in valores
            and valores["plano_conta_id"] != conta.plano_conta_id
        ):
            await self._validar_plano(valores["plano_conta_id"])

        banco = valores.get("banco", conta.banco)
        agencia = valores.get("agencia", conta.agencia)
        numero = valores.get("numero", conta.numero)
        if (banco, agencia, numero) != (conta.banco, conta.agencia, conta.numero):
            if await self.repo.chave_em_uso(
                banco, agencia, numero, ignorar_id=conta_id
            ):
                raise ConflictError(
                    "Já existe uma conta com este banco, agência e número."
                )

        for campo, valor in valores.items():
            setattr(conta, campo, valor)

        await self.session.commit()
        await self.session.refresh(conta)
        return conta

    async def excluir(self, conta_id: int) -> None:
        conta = await self.obter(conta_id)
        await self.repo.soft_delete(conta)
        await self.session.commit()

    async def _validar_plano(self, plano_conta_id: int) -> None:
        plano = await self.plano_repo.get(plano_conta_id)
        if plano is None:
            raise NotFoundError("Conta do plano de contas", plano_conta_id)
        if plano.sintetica:
            raise BusinessRuleError(
                "A conta do plano vinculada precisa ser analítica."
            )