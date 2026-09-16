# FINANCING

Sistema de **Contas a Pagar / Gestão Financeira** — aplicação web com frontend e backend isolados, autenticação JWT e persistência relacional.

## Visão Geral

O FINANCING permite agendar pagamentos, classificar despesas por plano de contas, indicar a conta corrente de origem, emitir extratos e conciliar pagamentos. O projeto segue uma arquitetura desacoplada em três camadas, com o backend exposto como API RESTful e o frontend consumindo-a via HTTP.

## Arquitetura
```
┌─────────────┐   HTTP + JWT   ┌──────────────┐   SQLAlchemy 2.0 Async   ┌───────────────────┐
│  Streamlit  │ ─────────────► │   FastAPI    │ ───────────────────────► │  Banco Relacional │
│  (Frontend) │                │  (Backend)   │                          │ SQLite / Postgres │
└─────────────┘                └──────────────┘                          └───────────────────┘
```

### Camadas do backend

- **`models.py`** — mapeamento ORM (SQLAlchemy 2.0, tipado com `Mapped[...]`) e estrutura física das tabelas.
- **`schemas.py`** — contratos Pydantic v2: validação de entrada, serialização de saída e sanitização de dados sensíveis (nunca expõe `senha_hash`).
- **`repositories/`** — acesso a dados. Filtra o soft delete automaticamente e faz `flush`; a transação pertence ao serviço.
- **`services/`** — regras de negócio e operações multi-tabela (baixa de título, transferência, conciliação). Controlam transações (`commit`).
- **`routers/`** — endpoints HTTP; finos, delegando para serviços e autenticados via `get_current_user`.
- **`dependencies.py`** — `get_current_user`: decodifica o JWT e busca o usuário no banco.
- **`exceptions.py`** — exceções de domínio (`NotFoundError`, `ConflictError`, `BusinessRuleError`) mapeadas para 404/409/422 no `main.py`.
- **`security.py`** — emissão/validação de JWT, hash de senha (`pwdlib[bcrypt]`) e política de senha.
- **`database.py`** — engine e sessão assíncrona.
- **`config.py`** — configuração central via `pydantic-settings` (lê variáveis de ambiente).
- **`seed.py`** — seed idempotente (admin + plano de contas padrão), roda no startup em desenvolvimento.

### Frontend

- **`app.py`** — entrada do Streamlit com `st.navigation`.
- **`api_client.py`** — cliente HTTPX que injeta o Bearer Token e centraliza tratamento de erros.
- **`views/`** — telas (login, dashboard, títulos).

## Decisões de Modelagem

- **Multi-usuário com dados compartilhados**: todos os usuários veem todos os dados. Nenhuma entidade de domínio possui `usuario_id`; o `Usuario` serve apenas para autenticação.
- **Soft delete**: entidades de domínio usam `deleted_at`; exclusões são lógicas, nunca físicas.
- **Plano de contas hierárquico**: `parent_id` auto-referente + flag `sintetica` (conta agrupadora) vs analítica (recebe lançamento).
- **Valores monetários**: `Decimal` / `Numeric(14,2)` — nunca `float`.

## Stack Tecnológica

| Camada | Tecnologia |
| --- | --- |
| Frontend | Streamlit, HTTPX |
| Backend | FastAPI, Uvicorn |
| ORM | SQLAlchemy 2.0 (async) |
| Validação | Pydantic v2 |
| Autenticação | OAuth2 Password Flow + JWT, `pwdlib[bcrypt]` |
| Banco (dev) | SQLite + aiosqlite |
| Banco (prod) | PostgreSQL + asyncpg |
| Migrações | Alembic |
| Logs | Loguru (rotação e retenção) |
| Testes | pytest + pytest-asyncio + httpx |

## Estado Atual do Projeto

> Status honesto do que já existe no repositório.

- ✅ **Implementado (MVP)**: autenticação (register, token, me) com proteções de segurança — `/register` bloqueado em produção, rate limiting no login, erro 401 padronizado, logger sem diagnose em produção; modelos `Usuario`/`PlanoContas`/`ContaCorrente`; CRUD de plano de contas e contas correntes (repositories + services + routers); migrações Alembic; seed (admin + plano de contas); logging; CORS.
- ✅ **Testes (46)**: regras de hierarquia (ciclo), vínculo plano ↔ conta corrente, segurança da autenticação, seed idempotente e CRUD via HTTP (incluindo o contrato de listagem paginada).
- 🚧 **Em desenvolvimento**: frontend Streamlit — telas de plano de contas e contas correntes.
- 📋 **Planejado**: títulos a pagar, movimentações, transferências, conciliação (OFX/CSV), relatórios e extratos.

## Como Executar (Desenvolvimento)
```bash
# Na raiz do projeto
python -m venv venv
.\venv\Scripts\Activate.ps1

# Instale as dependências
pip install -r requirements.txt
```

**Backend** (terminal 1):
```bash
cd backend
alembic upgrade head          # cria o schema (tabelas)
uvicorn main:app --reload --port 8000   # seed roda no startup (dev)
```

**Frontend** (terminal 2):
```bash
cd frontend
streamlit run app.py
```

**Testes**:
```bash
cd backend
python -m pytest tests/ -v
```

- Acesse o frontend em `http://localhost:8501`
- Documentação interativa da API em `http://localhost:8000/docs`
- O seed roda apenas em desenvolvimento e cria o usuário admin (`ADMIN_EMAIL`/`ADMIN_PASSWORD` do `.env`) e o plano de contas padrão. É idempotente — não duplica dados.

## Testes

Suíte com **46 testes** cobrindo regras de negócio, segurança e os endpoints HTTP reais. O banco é SQLite em memória, isolado por teste; a API é exercitada via `ASGITransport` (sem abrir porta e sem rodar o seed).

| Arquivo | Cobertura | Testes |
| --- | --- | --- |
| `tests/test_plano_contas_service.py` | Hierarquia do plano: ciclo, parentesco, exclusão/conversão, código único | 9 |
| `tests/test_conta_corrente_service.py` | Vínculo plano ↔ conta corrente, duplicidade bancária, proteção do plano | 7 |
| `tests/test_auth_security.py` | 401 padronizado, rate limit, `/register` protegido, `/me`, logger | 13 |
| `tests/test_seed.py` | Seed idempotente (admin + plano de contas) | 4 |
| `tests/test_crud_http.py` | Endpoints reais via HTTP: CRUD + autenticação obrigatória | 13 |

> **Contrato das listagens:** `GET /api/v1/plano-contas` e `GET /api/v1/contas` retornam um envelope paginado `{ items, total, limit, offset }` — não uma lista direta. Os testes de CRUD validam `items` e `total`.

Referência completa do escopo: `test.md`.

## Configuração de Produção

### Variáveis de ambiente

Copie `.env.example` para `.env` e preencha:

| Variável | Descrição | Exemplo |
| --- | --- | --- |
| `SECRET_KEY` | Chave de assinatura do JWT (obrigatória, gere uma forte com 32+ bytes) | `openssl rand -hex 32` |
| `DATABASE_URL` | String de conexão do banco | `postgresql+asyncpg://user:pass@host:5432/financing` |
| `ENVIRONMENT` | Ambiente de execução | `development` / `production` |
| `CORS_ORIGINS` | Origens permitidas (separadas por vírgula) | `http://localhost:8501` |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Credenciais do seed inicial | — |

### Banco de dados

- **Desenvolvimento**: SQLite (`sqlite+aiosqlite:///./contas_pagar.db`), zero configuração.
- **Produção**: PostgreSQL via `asyncpg`. A string de conexão vem do `.env`; o engine aplica `pool_pre_ping` para reconectar conexões ociosas.

### Migrações (Alembic)

As migrações são executadas a partir da pasta `backend/`:
```bash
cd backend
pip install alembic
alembic init alembic
```

> Após o `alembic init`, **substitua o `env.py` gerado pela versão assíncrona do projeto** (que lê a `DATABASE_URL` do `config.py`). No `alembic.ini`, deixe `sqlalchemy.url =` vazio — o `env.py` o preenche em tempo de execução.

Gerar e aplicar uma migração:
```bash
# Após alterar models.py, gerar uma nova migração
alembic revision --autogenerate -m "descricao das alterações"
alembic upgrade head
```

O que fazer depois de cada geração:
- Revise o arquivo gerado em `alembic/versions/`. O autogenerate não é perfeito: não detecta renomeações (vira drop + create) e às vezes gera `op` desnecessários. Confira se `upgrade()` e `downgrade()` são simétricos.
- Migração vazia (sem `op.` nenhum) = o banco já está igual ao metadata. Acontece quando o banco foi criado pelo `create_all` e o Alembic nunca foi usado — por isso a recomendação de apagar o `.db` antes da primeira geração.
- Nunca edite uma migração já aplicada em outro ambiente. Se precisar mudar algo, gere uma migração nova.

**Importante**:
- `create_all` é usado apenas para bootstrap em desenvolvimento. Em produção, toda evolução do schema passa por migrações Alembic.
- Gere a primeira migração contra um banco vazio. Se o `contas_pagar.db` já existir com as tabelas criadas pelo `create_all`, o autogenerate compara com o banco e produz uma migração vazia. Apague o arquivo antes de rodar `alembic revision --autogenerate`.
- Senha do Postgres com `%` quebra o `alembic.ini` (o configparser interpreta como interpolação). Como a URL vem do `env.py`, escape `%` como `%%` se aparecer.
- O `env.py` é o "motor" do Alembic — ele roda toda vez que você executa qualquer comando (`revision`, `upgrade`, `downgrade`).

Como recriar o `contas_pagar.db`:
```bash
# 1. Pare o uvicorn (importante no Windows: o arquivo fica travado em uso)
# Ctrl+C no terminal do backend

# 2. Apague o arquivo
cd backend
del contas_pagar.db        # PowerShell: Remove-Item contas_pagar.db

# 3. O schema vem do Alembic, os dados vêm do seed.
alembic upgrade head
uvicorn main:app --reload --port 8000
```

### Segurança

**Já implementado:**
- [X] `SECRET_KEY` forte, gerada por ambiente (nunca commitada)
- [X] Validação de senha ativa (mínimo de 8 caracteres, limite de 72 bytes do bcrypt)
- [X] Endpoint `/register` desabilitado em produção (retorna 404)
- [X] Rate limiting no `/token` (5 tentativas / 5 minutos por e-mail)
- [X] Usuário inativo, inexistente ou senha errada → sempre 401 (não revela qual é o caso)
- [X] `diagnose=False` e `backtrace=False` no logger em produção (evita vazar dados sensíveis em log)
- [X] Seed de usuário desabilitado em produção (roda apenas em dev)

**Pendente para o deploy:**
- [ ] Rate limiting distribuído (Redis) se houver múltiplos workers do uvicorn — o atual é em memória, por processo
- [ ] Revisão de logs em produção para confirmar que nenhum dado sensível é gravado

### Logs

- Backend: `backend/logs/` — rotação de 10 MB, retenção de 14 dias, compressão zip.
- Frontend: `frontend/logs/` — mesma política.
- Em produção, `diagnose` e `backtrace` desativados.

## Regras de Negócio e Relacionamentos

> Modelo de design — funcionalidades planejadas, ainda não implementadas.

| Funcionalidade | Implementação na Modelagem |
| --- | --- |
| **Baixa de Título** | Ao pagar um `titulos_pagar`, cria-se um registro de `SAIDA` em `movimentacoes_conta` associado ao `id_titulo_pagar`. |
| **Transferência entre Contas** | Cria **dois** registros em `movimentacoes_conta` (uma `SAIDA` na origem e uma `ENTRADA` no destino) unidos por um registro único na tabela `transferencias`. |
| **Extrato da Conta** | Obtido ordenando `movimentacoes_conta` por `data_movimento` para a conta informada. O saldo atual é o `saldo_inicial` mais a soma de `ENTRADA` menos `SAIDA`. |
| **Conciliação** | Grava o vínculo da movimentação com o registro do arquivo OFX/CSV (usando `fitid_ofx` para evitar duplicidades) e marca `conciliado = TRUE`. |

## Estrutura de Diretórios
```text
financing/
├── .env.example            # Modelo de variáveis de ambiente
├── requirements.txt        # Dependências do projeto
├── backend/
│   ├── alembic.ini         # Configuração do Alembic (sqlalchemy.url vazio)
│   ├── alembic/
│   │   ├── env.py          # Versão assíncrona (lê DATABASE_URL do config)
│   │   └── versions/       # Migrações geradas
│   ├── pytest.ini          # Configuração do pytest (pythonpath = .)
│   ├── config.py           # Configuração central (pydantic-settings)
│   ├── database.py         # Engine e sessão assíncrona
│   ├── dependencies.py     # get_current_user (JWT → usuário)
│   ├── exceptions.py       # Exceções de domínio (404/409/422)
│   ├── logger.py           # Configuração de log
│   ├── main.py             # FastAPI: lifespan, CORS, handlers, routers
│   ├── models.py           # Usuario, PlanoContas, ContaCorrente
│   ├── schemas.py          # Contratos Pydantic (Create/Update/Read)
│   ├── security.py         # JWT, hash de senha e política de senha
│   ├── seed.py             # Seed idempotente (admin + plano de contas)
│   ├── repositories/
│   │   ├── base.py         # Repositório genérico (soft delete automático)
│   │   ├── plano_contas.py
│   │   └── conta_corrente.py
│   ├── services/
│   │   ├── plano_contas.py
│   │   └── conta_corrente.py
│   ├── routers/
│   │   ├── auth.py         # /auth/token, /auth/me, /auth/register
│   │   ├── plano_contas.py # CRUD /api/v1/plano-contas
│   │   └── conta_corrente.py # CRUD /api/v1/contas
│   ├── tests/
│   │   ├── conftest.py     # Fixtures: session (SQLite em memória) + client HTTP
│   │   ├── test_plano_contas_service.py
│   │   ├── test_conta_corrente_service.py
│   │   ├── test_auth_security.py
│   │   ├── test_seed.py
│   │   └── test_crud_http.py
│   └── logs/
└── frontend/
    ├── app.py              # Entrada Streamlit (st.navigation)
    ├── api_client.py       # Cliente HTTPX com Bearer Token
    ├── logger.py           # Log do frontend
    ├── views/
    │   ├── login.py
    │   ├── dashboard.py
    │   └── titulos.py
    └── logs/
```

## Requisitos Funcionais

- Agendar pagamentos
- Classificar conforme um plano de contas
- Indicar a conta corrente de origem do pagamento
- Emitir lista de títulos em aberto
- Emitir extrato por conta corrente
- Registrar transferências entre contas
- Permitir conciliação do que foi pago

## Requisitos Não Funcionais

- Desenvolvido em Python
- Frontend e backend isolados
- Transações executadas no backend via API
- Banco relacional remoto (SQLite em dev, PostgreSQL em prod)
- Autenticação por login simples (OAuth2/JWT)
- Dimensionado para 100 transações/dia e 4 usuários simultâneos
- Registro de atividades em log estilo LOGCAT