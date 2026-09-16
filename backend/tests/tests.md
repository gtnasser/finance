testes.md

Estrutura de testes da camada de serviço com banco SQLite em memória, cobrindo os cenários de **ciclo** (hierarquia) e **vínculo** (plano ↔ conta corrente).

## Estrutura de testes

```text
backend/
└── tests/
    ├── conftest.py                      # fixture da sessão async em memória
    ├── test_plano_contas_service.py     # ciclo + vínculo (filhos)
    └── test_conta_corrente_service.py   # vínculo (plano analítico, duplicidade)
```

## 📄 `tests/conftest.py`

```python
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database import Base
import models  # noqa: F401  # registra as tabelas no metadata


@pytest_asyncio.fixture
async def session():
    """Sessão async isolada por teste, com schema criado do zero."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # mantém a mesma conexão para o banco em memória
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as session:
        yield session

    await engine.dispose()
```

O `StaticPool` é essencial aqui: sem ele, cada conexão do SQLite em memória criaria um banco novo e vazio. Com ele, todas usam a mesma conexão e os dados persistem durante o teste.

## 📄 `tests/test_plano_contas_service.py`

```python
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
    # 1 -> 1.1 -> 1.1.1
    raiz = await _criar(session, codigo="1", descricao="Ativo")
    filho = await _criar(
        session, codigo="1.1", descricao="Ativo Circulante", parent_id=raiz.id
    )
    neto = await _criar(
        session, codigo="1.1.1", descricao="Caixa", parent_id=filho.id
    )

    # Mover a raiz para baixo do neto criaria um ciclo
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

    # Mover o neto para baixo da raiz é válido (não cria ciclo)
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

    # Repositório filtra deleted_at — a conta não deve aparecer mais
    from repositories.plano_contas import PlanoContasRepository

    repo = PlanoContasRepository(session)
    assert await repo.get(conta.id) is None


@pytest.mark.asyncio
async def test_codigo_duplicado_gera_conflito(session):
    await _criar(session, codigo="1", descricao="Ativo")

    with pytest.raises(ConflictError):
        await _criar(session, codigo="1", descricao="Outro Ativo")
```

## 📄 `tests/test_conta_corrente_service.py`

```python
import pytest

from exceptions import BusinessRuleError, ConflictError, NotFoundError
from schemas import ContaCorrenteCreate, PlanoContasCreate, PlanoContasUpdate
from services.contas_correntes import ContaCorrenteService
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
            ContaCorrenteUpdate(banco="001", agencia="1234", numero="56789-0"),
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
            conta.id, ContaCorrenteUpdate(plano_conta_id=plano_sintetico.id)
        )
```

## Como rodar

```bash
cd backend
pip install pytest pytest-asyncio   # já previstos no dev.txt
pytest tests/ -v
```

Se algum schema de `Create` tiver campos obrigatórios que eu não listei (ex.: algum campo com `Field(...)` sem default), o teste acusa `ValidationError` na construção do payload — me avisa o nome do campo que eu ajusto o helper.

## Resumindo

- `conftest.py` cria uma sessão async isolada por teste, com SQLite em memória e `StaticPool`.
- **Ciclo**: conta não pode ser superior de si mesma, nem ser movida para baixo de um descendente; superior precisa existir e ser sintética.
- **Vínculo**: plano com filhos não é excluído nem convertido em analítico; plano vinculado a conta corrente não é excluído; conta corrente só aceita plano analítico e chave bancária única.

## Caminho de Importação

Quando o pytest roda, ele insere no sys.path a pasta onde estão os testes (tests/) — mas os módulos (database.py, models.py, etc.) estão na pasta acima (backend/). Por isso from database import Base falha: o Python procura em tests/ e não acha.

Solução recomendada: 

Crie `pytest.ini` na raiz do backend:
```
[pytest]
pythonpath = .
testpaths = tests
```

O pythonpath = . (disponível desde o pytest 7) adiciona a pasta backend/ ao sys.path — exatamente onde estão database.py, models.py, services/, repositories/. O testpaths = tests evita que o pytest procure testes em pastas erradas.

Depois é só rodar normalmente:
```bash
cd backend
pytest tests/ -v
```

ou 

```bash
cd backend
python -m pytest tests/ -v
```

