# services/plano_contas.py
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions import BusinessRuleError, ConflictError, NotFoundError
from models import PlanoContas
from repositories.conta_corrente import ContaCorrenteRepository
from repositories.plano_contas import PlanoContasRepository
from schemas import PlanoContasCreate, PlanoContasUpdate

class PlanoContasService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = PlanoContasRepository(session)
        self.contas_repo = ContaCorrenteRepository(session)

    async def criar(self, dados: PlanoContasCreate) -> PlanoContas:
        if await self.repo.codigo_em_uso(dados.codigo):
            raise ConflictError(f"Já existe uma conta com o código '{dados.codigo}'.")
        if dados.parent_id is not None:
            await self._validar_superior(dados.parent_id)

        conta = PlanoContas(**dados.model_dump())
        await self.repo.add(conta)
        await self.session.commit()
        await self.session.refresh(conta)
        return conta

    async def obter(self, conta_id: int) -> PlanoContas:
        conta = await self.repo.get(conta_id)
        if conta is None:
            raise NotFoundError("Conta do plano de contas", conta_id)
        return conta

    async def listar(self, *, limit: int = 50, offset: int = 0, **filtros):
        itens: Sequence[PlanoContas] = await self.repo.listar(
            limit=limit, offset=offset, **filtros
        )
        total = await self.repo.contar(**filtros)
        return itens, total

    async def atualizar(self, conta_id: int, dados: PlanoContasUpdate) -> PlanoContas:
        conta = await self.obter(conta_id)
        valores = dados.model_dump(exclude_unset=True)

        if "codigo" in valores and valores["codigo"] != conta.codigo:
            if await self.repo.codigo_em_uso(valores["codigo"], ignorar_id=conta_id):
                raise ConflictError(
                    f"Já existe uma conta com o código '{valores['codigo']}'."
                )

        if "parent_id" in valores and valores["parent_id"] != conta.parent_id:
            novo_superior = valores["parent_id"]
            if novo_superior is not None:
                if novo_superior == conta_id:
                    raise BusinessRuleError(
                        "Uma conta não pode ser superior de si mesma."
                    )
                await self._validar_superior(novo_superior)
                if await self._descende_de(novo_superior, conta_id):
                    raise BusinessRuleError(
                        "Hierarquia inválida: a alteração criaria um ciclo."
                    )

        if valores.get("sintetica") is False and conta.sintetica:
            if await self.repo.tem_filhos(conta_id):
                raise BusinessRuleError(
                    "Conta com contas filhas não pode ser convertida em analítica."
                )

        for campo, valor in valores.items():
            setattr(conta, campo, valor)

        await self.session.commit()
        await self.session.refresh(conta)
        return conta

    async def excluir(self, conta_id: int) -> None:
        conta = await self.obter(conta_id)
        if await self.repo.tem_filhos(conta_id):
            raise BusinessRuleError(
                "Não é possível excluir uma conta que possui contas filhas."
            )
        if await self.contas_repo.existe_vinculo_plano(conta_id):
            raise BusinessRuleError(
                "Não é possível excluir uma conta vinculada a contas correntes."
            )
        await self.repo.soft_delete(conta)
        await self.session.commit()

    async def _validar_superior(self, parent_id: int) -> PlanoContas:
        parent = await self.repo.get(parent_id)
        if parent is None:
            raise NotFoundError("Conta superior", parent_id)
        if not parent.sintetica:
            raise BusinessRuleError(
                "A conta superior precisa ser sintética (agrupadora)."
            )
        return parent

    async def _descende_de(self, node_id: int, ancestor_id: int) -> bool:
        """True se `node_id` estiver abaixo de `ancestor_id` na hierarquia."""
        atual: int | None = node_id
        visitados: set[int] = set()
        while atual is not None and atual not in visitados:
            if atual == ancestor_id:
                return True
            visitados.add(atual)
            conta = await self.repo.get(atual)
            if conta is None:
                return False
            atual = conta.parent_id
        return False