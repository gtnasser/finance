# Testes — Escopo e Cobertura

Documentação da suíte de testes do backend FINANCING. Define o que é testado, como rodar e o que cada arquivo cobre.

## Como executar
```bash
cd backend
python -m pytest tests/ -v        # suíte completa (46 testes)
python -m pytest tests/test_plano_contas_service.py -v   # só plano de contas
python -m pytest tests/test_auth_security.py -v          # só segurança
python -m pytest tests/test_crud_http.py -v              # só CRUD via HTTP
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

### `test_crud_http.py` — endpoints reais via HTTP (13 testes)

Cobre o CRUD completo de plano de contas e contas correntes pela API:

- **Autenticação obrigatória**: sem token, os endpoints de CRUD retornam 401.
- **Plano de contas**: criar (201), duplicado (409), payload inválido (422), listar (vazio e com itens), obter por id (200/404), atualizar (200), ciclo na hierarquia via HTTP (422), excluir (204 + some da listagem), excluir com filhos (422).
- **Conta corrente**: criar em plano analítico (201), criar em plano sintético (422), duplicada (409), listar, obter por id, atualizar.

### Contrato das listagens (envelope paginado)

Os endpoints `GET /api/v1/plano-contas` e `GET /api/v1/contas` não retornam uma lista direta — devolvem um envelope paginado:
```json
{
  "items": [...],
  "total": 2,
  "limit": 50,
  "offset": 0
}
```

- `items`: registros da página atual.
- `total`: quantidade total de registros (ignorando `limit`/`offset`).
- `limit` e `offset`: parâmetros de paginação aplicados (defaults: `limit=50`, `offset=0`).

Os testes de CRUD validam esse contrato lendo `items` e `total`, não o tamanho da resposta.

## Resumo da cobertura

| Área | Arquivo | Testes |
| --- | --- | --- |
| Hierarquia do plano de contas (ciclo) | `test_plano_contas_service.py` | 9 |
| Vínculo plano ↔ conta corrente | `test_conta_corrente_service.py` | 7 |
| Segurança (auth + logger) | `test_auth_security.py` | 13 |
| Seed (admin + plano) | `test_seed.py` | 4 |
| CRUD via HTTP (endpoints reais) | `test_crud_http.py` | 13 |
| **Total** | | **46** |

## O que ainda não é testado

- Títulos a pagar, movimentações, transferências e conciliação — funcionalidades ainda não implementadas.
- Rate limiting distribuído (Redis) — o atual é em memória, por processo.
- Frontend Streamlit (telas de plano de contas e contas correntes) — testes de interface ainda não criados.
