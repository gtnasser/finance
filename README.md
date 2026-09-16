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
- **`services/`** — regras de negócio e operações multi-tabela (baixa de título, transferência, conciliação). Controlam transações.
- **`routers/`** — endpoints HTTP; finos, delegando para serviços.
- **`security.py`** — emissão/validação de JWT e hash de senha (`pwdlib[bcrypt]`).
- **`database.py`** — engine e sessão assíncrona.
- **`config.py`** — configuração central via `pydantic-settings` (lê variáveis de ambiente).

### Frontend

- **`app.py`** — entrada do Streamlit com `st.navigation`.
- **`api_client.py`** — cliente HTTPX que injeta o Bearer Token e centraliza tratamento de erros.
- **`views/`** — telas (login, dashboard, títulos).

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

## Estado Atual do Projeto

> Status honesto do que já existe no repositório.

- ✅ **Implementado (MVP)**: autenticação (register, token, me), modelo `Usuario`, seed de ambiente, logging, estrutura de pastas.
- 🚧 **Em desenvolvimento**: CRUD de **plano de contas** e **contas correntes** (próximo passo).
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
uvicorn main:app --reload --port 8000
```

**Frontend** (terminal 2):
```bash
cd frontend
streamlit run app.py
```

- Acesse o frontend em `http://localhost:8501`
- Documentação interativa da API em `http://localhost:8000/docs`
- Em desenvolvimento, o banco é criado automaticamente com o usuário seed definido no `.env`

## Configuração de Produção

### Variáveis de ambiente

Copie `.env.example` para `.env` e preencha:

| Variável | Descrição | Exemplo |
| --- | --- | --- |
| `SECRET_KEY` | Chave de assinatura do JWT (obrigatória, gere uma forte) | `openssl rand -hex 32` |
| `DATABASE_URL` | String de conexão do banco | `postgresql+asyncpg://user:pass@host:5432/financing` |
| `ENVIRONMENT` | Ambiente de execução | `development` / `production` |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Credenciais do seed inicial | — |

### Banco de dados

- **Desenvolvimento**: SQLite (`sqlite+aiosqlite:///./contas_pagar.db`), zero configuração.
- **Produção**: PostgreSQL via `asyncpg`. A string de conexão vem do `.env`; o engine aplica `pool_pre_ping` para reconectar conexões ociosas.

### Migrações (Alembic)
```bash
# Criar a estrutura inicial de migrações
alembic init alembic

# Após alterar models.py, gerar uma nova migração
alembic revision --autogenerate -m "descricao"

# Aplicar
alembic upgrade head
```

> **Importante**: `create_all` é usado apenas para bootstrap em desenvolvimento. Em produção, toda evolução do schema passa por migrações Alembic.

### Segurança (checklist antes do deploy)

- [ ] `SECRET_KEY` forte, gerada por ambiente (nunca commitada)
- [ ] Endpoint `/register` desabilitado ou restrito a admin
- [ ] Rate limiting ativo no `/token`
- [ ] `diagnose=False` e `backtrace=False` no logger (evita vazar dados sensíveis em log)
- [ ] Seed de usuário desabilitado ou com senha vinda do `.env`
- [ ] Validação de senha ativa (mínimo de 8 caracteres)

### Logs

- Backend: `backend/logs/` — rotação de 10 MB, retenção de 14 dias, compressão zip.
- Frontend: `frontend/logs/` — mesma política.
- Em produção, `diagnose` e `backtrace` desativados.

## Regras de Negócio e Relacionamentos

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
│   ├── config.py           # Configuração central (pydantic-settings)
│   ├── database.py         # Engine e sessão assíncrona
│   ├── logger.py           # Configuração de log
│   ├── models.py           # Modelos ORM
│   ├── schemas.py          # Contratos Pydantic
│   ├── security.py         # JWT e hash de senha
│   ├── main.py             # FastAPI: lifespan, rotas, seed
│   ├── services/           # Regras de negócio (a criar)
│   ├── routers/
│   │   ├── auth.py         # /auth/token, /auth/me, /auth/register
│   │   └── contas.py       # CRUD de contas bancárias (a reescrever)
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