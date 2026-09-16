# Testes — Escopo e Cobertura

Documentação da suíte de testes do backend FINANCING. Define o que é testado, como rodar e o que cada arquivo cobre.

## Estrutura final da suíte

```text
backend/
├── pytest.ini                          # configuração do pytest
└── tests/
    ├── conftest.py                     # fixtures: session + client HTTP
    ├── test_plano_contas_service.py    # ciclo + vínculo (9 testes)
    ├── test_conta_corrente_service.py  # vínculo + duplicidade (7 testes)
    ├── test_auth_security.py           # segurança da API (13 testes)
    └── test_seed.py                    # seed admin + plano (4 testes)
```

**Total: 33 testes.**


## Como executar

```bash
cd backend
python -m pytest tests/ -v        # suíte completa (33 testes)
python -m pytest tests/test_plano_contas_service.py -v   # só plano de contas
python -m pytest tests/test_auth_security.py -v          # só segurança
```

Pré-requisitos: `pytest`, `pytest-asyncio` e `httpx` instalados.

## Infraestrutura de teste

| Arquivo | Papel |
| --- | --- |
| `pytest.ini` | `pythonpath = .` resolve os imports dos módulos do backend; `testpaths = tests` limita a busca |
| `tests/conftest.py` | Fixtures `session` (banco SQLite em memória, isolado por teste) e `client` (HTTP contra a app via ASGITransport, sem abrir porta e sem rodar o seed) |

O banco em memória usa `StaticPool` para manter a mesma conexão durante o teste. O schema é recriado do zero a cada teste, garantindo isolamento total.

## Escopo por arquivo

### `test_plano_contas_service.py` — regras de hierarquia (9 testes)

Cobre a camada de serviço do plano de contas:

- **Ciclo (loop na hierarquia)**: conta não pode ser superior de si mesma; não pode ser movida para baixo de um descendente; reparentar para um ancestral válido é permitido.
- **Integridade do parentesco**: superior inexistente gera `NotFoundError`; superior precisa ser conta sintética (agrupadora).
- **Exclusão e conversão**: conta com filhos não pode ser excluída; conta com filhos não pode ser convertida em analítica; conta sem filhos é excluída via soft delete (some do repositório).
- **Unicidade**: código duplicado gera `ConflictError`.

### `test_conta_corrente_service.py` — vínculo com o plano (7 testes)

Cobre a camada de serviço de contas correntes:

- **Vínculo com o plano**: conta corrente só pode apontar para conta analítica; plano inexistente gera `NotFoundError`; criação válida em plano analítico.
- **Duplicidade bancária**: banco + agência + número não podem se repetir (criação e atualização geram `ConflictError`).
- **Proteção do plano vinculado**: plano com conta corrente vinculada não pode ser excluído; trocar a conta para um plano sintético gera erro.

### `test_auth_security.py` — segurança da API (13 testes)

Cobre autenticação e proteções implementadas no `auth.py` e `logger.py`:

- **401 padronizado**: usuário inexistente, senha errada ou usuário inativo retornam sempre 401 (não revelam qual é o caso).
- **Login válido**: retorna `access_token`.
- **Rate limiting**: após 5 tentativas falhas em 5 minutos, a 6ª retorna 429.
- **`/register` protegido**: em produção retorna 404 (endpoint oculto); em dev cria usuário (201); senha curta retorna 422; e-mail duplicado retorna 409.
- **`/me`**: sem token retorna 401; com token válido retorna o usuário.
- **Logger**: `setup_logger()` executa sem erro em produção e em dev (smoke test — a verificação fina de `diagnose`/`backtrace` fica para revisão de código).

### `test_seed.py` — seed do ambiente (4 testes)

Cobre o seed idempotente:

- **Plano de contas**: cria todas as contas do padrão (`PLANO_CONTAS_PADRAO`) e é idempotente (segunda execução cria 0).
- **Usuário admin**: cria o administrador e é idempotente (segunda execução não duplica).

## Resumo da cobertura

| Área | Arquivo | Testes |
| --- | --- | --- |
| Hierarquia do plano de contas (ciclo) | `test_plano_contas_service.py` | 9 |
| Vínculo plano ↔ conta corrente | `test_conta_corrente_service.py` | 7 |
| Segurança (auth + logger) | `test_auth_security.py` | 13 |
| Seed (admin + plano) | `test_seed.py` | 4 |
| **Total** | | **33** |

## O que ainda não é testado

- Endpoints de CRUD via HTTP (`GET/POST/PUT/DELETE` de plano de contas e contas correntes) — hoje os testes cobrem os serviços diretamente.
- Títulos a pagar, movimentações, transferências e conciliação — funcionalidades ainda não implementadas.
- Rate limiting distribuído (Redis) — o atual é em memória, por processo.
````

---

**Resumindo**
- A suíte organizada tem **4 arquivos de teste + conftest + pytest.ini**, totalizando **33 testes**.
- Cobre: ciclo na hierarquia do plano, vínculo plano↔conta corrente, segurança da autenticação e seed idempotente.
- O `test.md` documenta o escopo, como rodar, o que cada arquivo cobre e o que ainda falta testar.
