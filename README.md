# FINANCING

Sistema de **Contas a Pagar / Gestão Financeira** - aplicação web que permite lançar despesas, agendar pagamentos, classificar despesas por plano de contas, indicar a conta corrente de origem, emitir extratos e conciliar pagamentos.

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

## 📌 Estado Atual do Projeto

> Status honesto do que já existe no repositório.

- ✅ **Frontend (parcial)**: telas de **Plano de Contas** e **Contas Correntes** implementadas (listagem paginada, formulários de criação/edição, exclusão com confirmação, botões de ação alinhados horizontalmente via `st.columns`); `api_client.py` com 8 métodos CRUD; navegação via `st.navigation` com proteção por token.
- ✅ **Dashboard**: 3 abas, visualizações por status, hierarquia, natureza e tipo.
- ✅ **Backend (MVP)**: API FastAPI com autenticação JWT (register bloqueado em produção, rate limiting no login, 401 padronizado, logger sem diagnose), CRUD de plano de contas e contas correntes (repositories + services + routers), soft delete, envelope paginado, migrações Alembic, seed idempotente, CORS e 46 testes.
- ✅ **Testes (46)**: regras de hierarquia (ciclo), vínculo plano ↔ conta corrente, segurança da autenticação, seed idempotente e CRUD via HTTP (incluindo o contrato de listagem paginada).
- 🚧 **Em desenvolvimento**: tela de **Contas a Pagar** (placeholder ativo — aguarda o CRUD de títulos no backend).
- 📋 **Planejado**: títulos a pagar, movimentações, transferências, conciliação (OFX/CSV), relatórios e extratos.

---

## 🗺️ Roadmap

- Títulos a pagar (CRUD + tela)
- Movimentações e transferências
- Conciliação bancária (OFX/CSV)
- Relatórios e extratos

---

## 📋 Regras de negócio

- Conta corrente só aponta para plano **analítico**.
- Plano com filhos não pode ser excluído nem convertido em analítico.
- Plano vinculado a conta corrente não pode ser excluído.
- Banco + agência + número de conta corrente são únicos.
- Código do plano de contas é único.

### Funcionalidades planejadas, ainda não implementadas.

| Funcionalidade | Implementação na Modelagem |
| --- | --- |
| **Baixa de Título** | Ao pagar um `titulos_pagar`, cria-se um registro de `SAIDA` em `movimentacoes_conta` associado ao `id_titulo_pagar`. |
| **Transferência entre Contas** | Cria **dois** registros em `movimentacoes_conta` (uma `SAIDA` na origem e uma `ENTRADA` no destino) unidos por um registro único na tabela `transferencias`. |
| **Extrato da Conta** | Obtido ordenando `movimentacoes_conta` por `data_movimento` para a conta informada. O saldo atual é o `saldo_inicial` mais a soma de `ENTRADA` menos `SAIDA`. |
| **Conciliação** | Grava o vínculo da movimentação com o registro do arquivo OFX/CSV (usando `fitid_ofx` para evitar duplicidades) e marca `conciliado = TRUE`. |

---

## 🏗️ Arquitetura


Este sistema segue uma arquitetura desacoplada em três camadas, com o backend exposto como API RESTful, o frontend consumindo-a via HTTP, e os dados persistidos em Banco de Dados Relacional (SQL). Conta ainda com autenticação JWT, exclusão de dados com soft delete e acesso a dados exclusivamente via API.

```
┌─────────────┐   HTTP + JWT   ┌──────────────┐   SQLAlchemy 2.0 Async   ┌───────────────────┐
│  Streamlit  │ ─────────────► │   FastAPI    │ ───────────────────────► │  Banco Relacional │
│  (Frontend) │                │  (Backend)   │                          │ SQLite / Postgres │
└─────────────┘                └──────────────┘                          └───────────────────┘
```

O backend segue uma arquitetura em camadas, onde cada camada chama apenas a imediatamente inferior:
```
Requisição → Router (valida com Schema) → Service (regras + transação) → Repository (SQL) → Model → Banco
Resposta   ← main.py (handlers)         ← Exception (se violou regra)  ← Service
```

O frontend fala apenas com a API (`http://localhost:8000/api/v1`) — não há acesso direto ao banco.

- **Routers**: endpoints finos, autenticados via `get_current_user`, validam o payload com os schemas e delegam ao serviço.
- **Services**: regras de negócio e controle de transação (commit/rollback).
- **Repositories**: leitura/gravação no banco, filtro automático de soft delete, `flush`. Regra de negócio nunca mora aqui.
- **Models**: ORM SQLAlchemy 2.0 — definem como o dado é armazenado.
- **Schemas**: Pydantic v2 — validam a entrada e serializam a saída (nunca expõem `senha_hash`).

O fluxo de erro é via exceções de domínio (`NotFoundError` → 404, `ConflictError` → 409, `BusinessRuleError` → 422), mapeadas em `main.py` para respostas HTTP com corpo `{"detail": ...}`.

---

## 🧰 Stack

| Camada | Tecnologias |
| --- | --- |
| Frontend | Streamlit, httpx, pandas, plotly |
| Backend | FastAPI, Uvicorn |
| ORM | SQLAlchemy 2.0 (async) |
| Validação | Pydantic v2 |
| Autenticação | OAuth2 Password Flow + JWT, `pwdlib[bcrypt]` |
| Banco (dev) | SQLite + aiosqlite |
| Banco (prod) | PostgreSQL + asyncpg |
| Migrações | Alembic |
| Logs | Loguru (rotação e retenção) |
| Testes | pytest + pytest-asyncio + httpx |


### Decisões de Modelagem

- **Multi-usuário com dados compartilhados**: todos os usuários veem todos os dados. Nenhuma entidade de domínio possui `usuario_id`; o `Usuario` serve apenas para autenticação.
- **Soft delete**: entidades de domínio usam `deleted_at`; exclusões são lógicas, nunca físicas.
- **Plano de contas hierárquico**: `parent_id` auto-referente + flag `sintetica` (conta agrupadora) vs analítica (recebe lançamento).
- **Valores monetários**: `Decimal` / `Numeric(14,2)` — nunca `float`.

---

## 📁 Estrutura de Diretórios
```text
financing/
├── backend/
│   ├── main.py             # FastAPI: Criação do app, CORS, handlers de exceção, routers
│   ├── config.py           # Configurações (ENVIRONMENT, DATABASE_URL, SECRET_KEY, pydantic-settings)
│   ├── database.py         # Engine e sessão assíncrona
│   ├── dependencies.py     # get_current_user (JWT → usuário)
│   ├── exceptions.py       # Exceções de domínio (404/409/422)
│   ├── models.py           # ORM: Usuario, PlanoContas, ContaCorrente (títulos e movimentações virão com o roadmap)
│   ├── schemas.py          # Contratos Pydantic (Create/Update/Read)
│   ├── seed.py             # Seed idempotente (admin + plano de contas)
│   ├── logger.py           # Configuração de log
│   ├── alembic.ini         # Configuração do Alembic (sqlalchemy.url vazio)
│   ├── alembic/
│   │   ├── env.py          # Versão assíncrona (lê DATABASE_URL do config)
│   │   └── versions/       # Migrações geradas
│   ├── pytest.ini          # Configuração do pytest (pythonpath = .)
│   ├── security.py         # JWT, hash de senha e política de senha
│   ├── routers/
│   │   ├── auth.py         # /auth/token, /auth/me, /auth/register
│   │   ├── plano_contas.py # CRUD /api/v1/plano-contas
│   │   └── conta_corrente.py # CRUD /api/v1/contas
│   ├── services/
│   │   ├── plano_contas.py
│   │   └── conta_corrente.py
│   ├── repositories/
│   │   ├── base.py         # Repositório genérico (soft delete automático)
│   │   ├── plano_contas.py
│   │   └── conta_corrente.py
│   ├── tests/
│   │   ├── conftest.py     # Fixtures: session (SQLite em memória) + client HTTP
│   │   └── test_*.py       # 46 testes
│   └── logs/
└── frontend/
    ├── app.py              # Entrada Streamlit (st.navigation + proteção por token)
    ├── api_client.py       # Cliente HTTPX: 8 métodos CRUD + auth + tratamento de 401
    ├── logger.py           # Log do frontend
    ├── views/
    │   ├── login.py
    │   ├── dashboard.py
    │   ├── titulos.py      # Placeholder (aguarda backend de títulos)
    │   ├── plano_contas.py # CRUD plano de contas (listagem paginada + formulário)
    │   └── contas_correntes.py # CRUD contas correntes (listagem paginada + formulário)
    └── logs/
```

---

## 🔐 Autenticação

- Fluxo OAuth2 Password (form data) em `/auth/token`, retornando JWT.
- `dependencies.py` expõe `get_current_user` para proteger os endpoints.
- No frontend, o token é guardado na sessão do Streamlit e injetado como `Authorization: Bearer <token>`.
- 401 fora do login → logout automático + `st.rerun()`.

---

## 🖥️ Frontend — padrões

### Tratamento de erros
- `api_client.py` define `APIError(status_code, detail)`: o `_request` lança essa exceção para toda resposta 4xx/5xx, com a mensagem `detail` vinda do servidor.
- 401 no `/auth/token` → credenciais inválidas: `login()` captura `APIError` e retorna `None` (não dispara logout).
- Falha de conexão (sem resposta HTTP) → propaga `httpx.RequestError`; as views exibem "Servidor indisponível".
- Distinção de causa: `APIError` = servidor respondeu explicando o motivo (4xx = acesso/regras, 5xx = falha interna); `RequestError` = falha estrutural de transporte.
- Views: carregadores retornam `None` em falha — nunca exibem o falso "Nenhuma conta cadastrada" quando houve erro real.
- `PAGE_SIZE = 200` em todas as views (teto do backend: `le=200`).
- DELETE retorna `bool` (204 vazio); erros de regra de negócio (422/409) chegam via `APIError` com o `detail` real do servidor.


---

## ⚙️ Como rodar

### Backend

```bash
# Na raiz do projeto
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head # cria o schema (tabelas)
uvicorn main:app --reload --port 8000   # seed roda no startup (dev)
```

### Frontend

```bash
# Na raiz do projeto
cd frontend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

### Testes

```bash
# Na raiz do projeto
cd backend
python -m pytest tests/ -v
```

- Acesse o frontend em `http://localhost:8501`
- Documentação interativa da API em `http://localhost:8000/docs`

---

## 🧪 Testes

- Suíte com **46 testes** cobrindo regras de negócio, segurança e os endpoints HTTP reais.
- Por enquanto abrange autenticação, plano de contas e contas correntes (regras de negócio, soft delete, hierarquia, vínculos).
- O banco é SQLite em memória, isolado por teste.
- A API é exercitada via `ASGITransport` (sem abrir porta e sem rodar o seed).
- Contrato de listagem: envelope paginado `{items, total, limit, offset}` (`limit` máximo aceito pelo backend: **200**).

| Arquivo | Cobertura | Testes |
| --- | --- | --- |
| `tests/test_plano_contas_service.py` | Hierarquia do plano: ciclo, parentesco, exclusão/conversão, código único | 9 |
| `tests/test_conta_corrente_service.py` | Vínculo plano ↔ conta corrente, duplicidade bancária, proteção do plano | 7 |
| `tests/test_auth_security.py` | 401 padronizado, rate limit, `/register` protegido, `/me`, logger | 13 |
| `tests/test_seed.py` | Seed idempotente (admin + plano de contas) | 4 |
| `tests/test_crud_http.py` | Endpoints reais via HTTP: CRUD + autenticação obrigatória | 13 |

---

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

**Obs:**
- O *seed* roda apenas em desenvolvimento e cria o usuário admin (`ADMIN_EMAIL`/`ADMIN_PASSWORD` do `.env`) e o plano de contas padrão. É idempotente — não duplica dados.

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

### Como recriar o `contas_pagar.db`:

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


