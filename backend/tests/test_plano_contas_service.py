import pytest

from exceptions import BusinessRuleError, ConflictError, NotFoundError
from schemas import PlanoContasCreate, PlanoContasUpdate
from services.plano_contas import PlanoContasService


def _payload(**kwargs):
    defaults = dict(
        codigo="1",
        descricao="Ativo",
        tipo="ATIVO",
        natureza="DEVEDORA",
        sintetica=True,
        parent_id=None,
        ativo=True,
    )
    defaults.update(kwargs)
    return PlanoContasCreate(**defaults)


async def _criar(session, **kwargs):
    return await PlanoContasService(session).criar(_payload(**kwargs))


# ----- Ciclo: hierarquia não pode criar loop -----

@pytest.mark.asyncio
async def test_conta_nao_pode_ser_superior_de_si_mesma(session):
    conta = await _criar(session, codigo="1", descricao="Ativo")

    with pytest.raises(BusinessRuleError):
        await PlanoContasService(session).atualizar(
            conta.id, PlanoContasUpdate(parent_id=conta.id)
        )


@pytest.mark.asyncio
async def test_reparentar_para_descendente_gera_ciclo(session):
    raiz = await _criar(session, codigo="1", descricao="Ativo")
    filho = await _criar(
        session, codigo="1.1", descricao="Ativo Circulante", parent_id=raiz.id
    )
    neto = await _criar(
        session, codigo="1.1.1", descricao="Caixa", parent_id=filho.id
    )

    with pytest.raises(BusinessRuleError):
        await PlanoContasService(session).atualizar(
            raiz.id, PlanoContasUpdate(parent_id=neto.id)
        )


@pytest.mark.asyncio
async def test_reparentar_valido_sem_ciclo(session):
    raiz = await _criar(session, codigo="1", descricao="Ativo")
    filho = await _criar(
        session, codigo="1.1", descricao="Ativo Circulante", parent_id=raiz.id
    )
    neto = await _criar(
        session, codigo="1.1.1", descricao="Caixa", parent_id=filho.id
    )

    atualizada = await PlanoContasService(session).atualizar(
        neto.id, PlanoContasUpdate(parent_id=raiz.id)
    )
    assert atualizada.parent_id == raiz.id


@pytest.mark.asyncio
async def test_superior_inexistente_gera_not_found(session):
    with pytest.raises(NotFoundError):
        await _criar(session, codigo="1", descricao="Ativo", parent_id=9999)


@pytest.mark.asyncio
async def test_superior_precisa_ser_sintetica(session):
    analitica = await _criar(
        session, codigo="1", descricao="Ativo", sintetica=False
    )
    with pytest.raises(BusinessRuleError):
        await _criar(
            session, codigo="1.1", descricao="Filho", parent_id=analitica.id
        )


# ----- Vínculo: exclusão e conversão bloqueadas -----

@pytest.mark.asyncio
async def test_nao_excluir_conta_com_filhos(session):
    raiz = await _criar(session, codigo="1", descricao="Ativo")
    await _criar(
        session, codigo="1.1", descricao="Ativo Circulante", parent_id=raiz.id
    )

    with pytest.raises(BusinessRuleError):
        await PlanoContasService(session).excluir(raiz.id)


@pytest.mark.asyncio
async def test_nao_converter_conta_com_filhos_em_analitica(session):
    raiz = await _criar(session, codigo="1", descricao="Ativo")
    await _criar(
        session, codigo="1.1", descricao="Ativo Circulante", parent_id=raiz.id
    )

    with pytest.raises(BusinessRuleError):
        await PlanoContasService(session).atualizar(
            raiz.id, PlanoContasUpdate(sintetica=False)
        )


@pytest.mark.asyncio
async def test_excluir_conta_sem_filhos_aplica_soft_delete(session):
    conta = await _criar(session, codigo="1", descricao="Ativo")

    await PlanoContasService(session).excluir(conta.id)

    from repositories.plano_contas import PlanoContasRepository

    repo = PlanoContasRepository(session)
    assert await repo.get(conta.id) is None


@pytest.mark.asyncio
async def test_codigo_duplicado_gera_conflito(session):
    await _criar(session, codigo="1", descricao="Ativo")

    with pytest.raises(ConflictError):
        await _criar(session, codigo="1", descricao="Outro Ativo")
        