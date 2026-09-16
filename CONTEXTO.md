# FINANCING — Documento de Contexto e Estado Atual

> Documento de retomada: captura o histórico da conversa, o estado do projeto e todas as definições
> feitas até agora. O próximo passo é a **definição do frontend** (telas Streamlit de plano de contas
> e contas correntes).

## 1. Visão Geral do Projeto

- **Nome**: FINANCING — Sistema de Contas a Pagar / Gestão Financeira.
- **Arquitetura**: frontend e backend isolados, comunicação via API RESTful com autenticação JWT.
- **Stack**:
  - Frontend: Streamlit + HTTPX
  - Backend: FastAPI + Uvicorn
  - ORM: SQLAlchemy 2.0 (async)
  - Validação: Pydantic v2
  - Autenticação: OAuth2 Password Flow + JWT, `pwdlib[bcrypt]`
  - Banco dev: SQLite + aiosqlite | Banco prod: PostgreSQL + asyncpg
  - Migrações: Alembic | Logs: Loguru | Testes: pytest + pytest-asyncio + httpx

## 2. Decisões de Modelagem (definidas e aprovadas)

- **Multi-usuário com dados compartilhados**: todos os usuários veem todos os dados. Nenhuma entidade
  de domínio possui `usuario_id`; o `Usuario` serve apenas para autenticação.
- **Soft delete**: entidades de domínio usam `deleted_at`; exclusões são lógicas, nunca físicas.
- **Plano de contas hierárquico**: `parent_id` auto-referente + flag `sintetica` (agrupadora) vs
  analítica (recebe lançamento).
- **Valores monetários**: `Decimal` / `Numeric(14,2)` — nunca `float`.
- **Requirements**: arquivo único (`requirements.txt`). A separação por ambiente foi **descartada**
  por decisão do usuário.

## 3. Backend — Implementado (MVP)

### Autenticação (`routers/auth.py`)
- Endpoints: `POST /api/v1/auth/token`, `POST /api/v1/auth/register`, `GET /api/v1/auth/me`.
- Proteções implementadas:
  - `/register` bloqueado em produção (retorna 404).
  - Rate limiting no `/token`: 5 tentativas / 5 minutos por e-mail (dicionário em memória
    `_login_attempts`).
  - 401 padronizado para usuário inexistente, inativo ou senha errada (não revela o caso).
  - Validação de senha: mínimo 8 caracteres, limite de 72 bytes do bcrypt.
- `security.py`: emissão/validação de JWT, hash de senha, política de senha.
- `dependencies.py`: `get_current_user` (decodifica JWT e busca usuário no banco).

### Domínio
- `models.py`: `Usuario`, `PlanoContas`, `ContaCorrente`.
- `schemas.py`: contratos Pydantic v2 (Create/Update/Read), nunca expõe `senha_hash`.
- `repositories/`: `base.py` (genérico, soft delete automático, flush), `plano_contas.py`,
  `conta_corrente.py`.
- `services/`: `plano_contas.py`, `conta_corrente.py` — regras de negócio e transações (commit).
- `routers/`: `auth.py`, `plano_contas.py` (CRUD `/api/v1/plano-contas`), `conta_corrente.py`
  (CRUD `/api/v1/contas`).
- `exceptions.py`: `NotFoundError` (404), `ConflictError` (409), `BusinessRuleError` (422),
  mapeadas no `main.py`.
- `config.py`: pydantic-settings. `is_production` é property **somente leitura** (deriva de
  `ENVIRONMENT`).
- `seed.py`: seed idempotente (admin + `PLANO_CONTAS_PADRAO`), roda no startup apenas em dev.
- `logger.py`: Loguru com rotação 10 MB / retenção 14 dias; em produção `diagnose=False` e
  `backtrace=False`.
- `main.py`: lifespan, CORS, handlers de exceção, routers.

### Contrato das listagens (importante para o frontend)
`GET /api/v1/plano-contas` e `GET /api/v1/contas` retornam **envelope paginado**, não lista direta:
```json
{ "items": [...], "total": 2, "limit": 50, "offset": 0 }
```

## 4. Testes — 46 testes passando (33 + 13 CRUD HTTP)

### Infraestrutura
- `backend/pytest.ini`: `pythonpath = .` (resolve imports) + `testpaths = tests`.
- `backend/tests/conftest.py`:
  - Fixture `session`: SQLite em memória com `StaticPool`, schema recriado por teste.
  - Fixture `client`: `ASGITransport` + `dependency_overrides` (API real sem abrir porta, sem seed).
  - Fixture `limpar_rate_limit` (autouse, `@pytest.fixture` síncrono): limpa `_login_attempts`
    entre testes — resolve o vazamento do rate limit global.

### Arquivos e cobertura
| Arquivo | Cobertura | Testes |
| --- | --- | --- |
| `test_plano_contas_service.py` | Ciclo na hierarquia, parentesco, exclusão/conversão, código único | 9 |
| `test_conta_corrente_service.py` | Vínculo plano↔conta corrente, duplicidade bancária, proteção do plano | 7 |
| `test_auth_security.py` | 401 padronizado, rate limit, `/register` protegido, `/me`, logger | 13 |
| `test_seed.py` | Seed idempotente (admin + plano) | 4 |
| `test_crud_http.py` | Endpoints reais: CRUD + autenticação obrigatória + envelope paginado | 13 |

### Bugs corrigidos durante os testes
1. **`repositories/base.py:45`** — `order_by` recebia tupla e o SQLAlchemy rejeitava
   (`ArgumentError`). Correção: desempacotar com `*` (`stmt.order_by(*order_expr)`).
2. **Rate limit vazando entre testes** — `_login_attempts` é global de módulo; após 5 logins, o 6º
   retornava 429. Correção: fixture autouse no `conftest.py`.
3. **`monkeypatch.setattr(settings, "is_production", ...)`** — property sem setter no pydantic.
   Correção: monkeypatchear `ENVIRONMENT` (campo subjacente).
4. **Envelope paginado** — testes liam lista direta; ajustados para `["items"]` / `["total"]`.

### Documentação gerada
- `test.md`: escopo completo da suíte, contrato das listagens, o que ainda não é testado.
- `README.md`: estado atual, seção de testes, contrato das listagens, estrutura de diretórios.

## 5. Estado Atual (checklist)

- ✅ Backend MVP: auth + segurança, modelos, CRUD plano de contas e contas correntes, migrations,
  seed, logging, CORS.
- ✅ Testes: 46 passando.
- ✅ Documentação: `test.md` e `README.md` atualizados.
- 🚧 **Em desenvolvimento: frontend Streamlit — telas de plano de contas e contas correntes
  (PRÓXIMO PASSO).**
- 📋 Planejado (não implementado): títulos a pagar, movimentações, transferências, conciliação
  (OFX/CSV), relatórios e extratos.
- ⏸️ Adiado por decisão do usuário: separação de requirements por ambiente.

## 6. Frontend — estado atual (implementado)

### Estrutura
```text
frontend/
├── app.py              # st.navigation + proteção por token (redireciona p/ login)
├── api_client.py       # Cliente HTTPX: auth + 8 métodos CRUD + 401 centralizado
├── logger.py           # Loguru (rotação 10MB / retenção 14 dias)
├── views/
│   ├── login.py        # Formulário de login (OAuth2 form data)
│   ├── dashboard.py    # Visão geral (placeholder)
│   ├── titulos.py      # Placeholder — aguarda backend de títulos
│   ├── plano_contas.py # CRUD plano de contas (implementado)
│   └── contas_correntes.py # CRUD contas correntes (implementado)
└── logs/
```

### Implementado nesta sessão
- **`app.py`**: páginas Plano de Contas (📚) e Contas Correntes (🏦) registradas no `st.navigation`; código morto `render_header` (condição `1==3`) removido.
- **`api_client.py`**: 8 métodos CRUD — `listar/criar/atualizar/excluir_plano_conta` e `listar/criar/atualizar/excluir_conta`. DELETE retorna `bool` (204 vazio). Listagens retornam envelope paginado (`items`/`total`/`limit`/`offset`).
- **`views/plano_contas.py`**: listagem hierárquica (ordenação por nível do código), paginação via `session_state`, formulário com select de conta superior (só sintéticas), exclusão com confirmação, tratamento de 409/422.
- **`views/contas_correntes.py`**: listagem paginada, formulário com select de plano (só analíticas), `data_saldo_inicial.isoformat()`, exclusão com confirmação, tratamento de 409/422.
- **Alinhamento horizontal dos botões de ação**: `st.columns(2)` + `use_container_width=True` dentro da coluna de ações (padrão aplicado nas duas telas).

### Próximo passo
- **Backend de títulos a pagar** (modelo, schemas, repository, service, router + endpoints) e depois ativar a `views/titulos.py` com o mesmo padrão das outras telas.

### Regras de negócio que o frontend respeita (vindas do backend)
- Conta corrente só aponta para plano **analítico**.
- Plano com filhos não pode ser excluído nem convertido em analítico.
- Plano vinculado a conta corrente não pode ser excluído.
- Banco + agência + número de conta corrente são únicos.
- Código do plano de contas é único.
- Listagens retornam envelope paginado (`items`/`total`/`limit`/`offset`).

## 7. Como rodar (referência)
```bash
# Backend (terminal 1)
cd backend
alembic upgrade head
uvicorn main:app --reload --port 8000

# Frontend (terminal 2)
cd frontend
streamlit run app.py

# Testes
cd backend
python -m pytest tests/ -v
```
`
```

---

**Resumindo**
- O documento captura o histórico completo: decisões de modelagem, backend implementado, 46 testes passando, bugs corrigidos, documentação gerada e o estado do frontend.
- O **próximo passo está marcado**: definição e implementação das telas Streamlit de plano de contas e contas correntes, com as regras de negócio que o frontend deve respeitar já listadas.
- Basta salvar este documento (ex.: `CONTEXTO.md` na raiz do projeto) para retomarmos de onde paramos.

Se quiser, posso:
- Gerar este documento em formato Word/PDF para você guardar junto ao projeto.
- Já iniciar agora a definição das telas Streamlit de plano de contas e contas correntes, partindo deste ponto.