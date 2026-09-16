
import pytest

from seed import PLANO_CONTAS_PADRAO, seed_admin, seed_plano_contas


@pytest.mark.asyncio
async def test_seed_plano_contas_cria_todas_as_contas(session):
    criadas = await seed_plano_contas(session)
    assert criadas == len(PLANO_CONTAS_PADRAO)


@pytest.mark.asyncio
async def test_seed_plano_contas_e_idempotente(session):
    assert await seed_plano_contas(session) == len(PLANO_CONTAS_PADRAO)
    assert await seed_plano_contas(session) == 0


@pytest.mark.asyncio
async def test_seed_admin_cria_usuario(session):
    assert await seed_admin(session) is True


@pytest.mark.asyncio
async def test_seed_admin_e_idempotente(session):
    await seed_admin(session)
    assert await seed_admin(session) is False