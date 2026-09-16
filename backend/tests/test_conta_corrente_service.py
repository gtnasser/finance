
import pytest

from exceptions import BusinessRuleError, ConflictError, NotFoundError
from schemas import (
    ContaCorrenteCreate,
    ContaCorrenteUpdate,
    PlanoContasCreate,
    PlanoContasUpdate,
)
from services.plano_contas import PlanoContasService


async def _criar_plano(session, **kwargs):
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
    return await PlanoContasService(session).criar(PlanoContasCreate(**defaults))


async def _criar_conta(session, **kwargs):
    defaults = dict(
        nome="Conta Principal",
        banco="001",
        agencia="1234",
        numero="56789-0",
        tipo="CORRENTE",
        moeda="BRL",
        saldo_inicial="0.00",
        data_saldo_inicial="2026-01-01",
        plano_conta_id=None,
        ativo=True,
    )
    defaults.update(kwargs)
    return await ContaCorrenteService(session).criar(
        ContaCorrenteCreate(**defaults)
    )


# ----- Vínculo: conta corrente só aceita plano analítico -----

@pytest.mark.asyncio
async def test_nao_permitir_conta_corrente_em_plano_sintetico(session):
    plano = await _criar_plano(session, codigo="1", descricao="Ativo")

    with pytest.raises(BusinessRuleError):
        await _criar_conta(session, plano_conta_id=plano.id)


@pytest.mark.asyncio
async def test_nao_permitir_conta_corrente_em_plano_inexistente(session):
    with pytest.raises(NotFoundError):
        await _criar_conta(session, plano_conta_id=9999)


@pytest.mark.asyncio
async def test_criar_conta_corrente_em_plano_analitico(session):
    plano = await _criar_plano(
        session, codigo="1", descricao="Ativo", sintetica=False
    )

    conta = await _criar_conta(session, plano_conta_id=plano.id)

    assert conta.id is not None
    assert conta.banco == "001"
    assert conta.plano_conta_id == plano.id


# ----- Vínculo: duplicidade de chave bancária -----

@pytest.mark.asyncio
async def test_nao_permitir_duplicar_banco_agencia_numero(session):
    plano = await _criar_plano(
        session, codigo="1", descricao="Ativo", sintetica=False
    )
    await _criar_conta(session, plano_conta_id=plano.id)

    with pytest.raises(ConflictError):
        await _criar_conta(session, plano_conta_id=plano.id)


@pytest.mark.asyncio
async def test_atualizar_para_chave_bancaria_duplicada(session):
    plano = await _criar_plano(
        session, codigo="1", descricao="Ativo", sintetica=False
    )
    conta_a = await _criar_conta(session, plano_conta_id=plano.id)
    conta_b = await _criar_conta(
        session,
        plano_conta_id=plano.id,
        banco="341",
        agencia="0001",
        numero="12345-6",
    )

    with pytest.raises(ConflictError):
        await ContaCorrenteService(session).atualizar(
            conta_b.id,
            ContaCorrenteUpdate(
                banco="001", agencia="1234", numero="56789-0"
            ),
        )


# ----- Vínculo: plano vinculado não pode ser excluído -----

@pytest.mark.asyncio
async def test_nao_excluir_plano_vinculado_a_conta_corrente(session):
    plano = await _criar_plano(
        session, codigo="1", descricao="Ativo", sintetica=False
    )
    await _criar_conta(session, plano_conta_id=plano.id)

    with pytest.raises(BusinessRuleError):
        await PlanoContasService(session).excluir(plano.id)


@pytest.mark.asyncio
async def test_atualizar_plano_da_conta_para_sintetico_gera_erro(session):
    plano_analitico = await _criar_plano(
        session, codigo="1", descricao="Ativo", sintetica=False
    )
    plano_sintetico = await _criar_plano(
        session, codigo="2", descricao="Passivo", sintetica=True
    )
    conta = await _criar_conta(session, plano_conta_id=plano_analitico.id)

    with pytest.raises(BusinessRuleError):
        await ContaCorrenteService(session).atualizar(
            conta.id,
            ContaCorrenteUpdate(plano_conta_id=plano_sintetico.id),
        )
```