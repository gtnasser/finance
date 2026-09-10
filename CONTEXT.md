Olá! Gostaria de continuar o desenvolvimento do meu sistema de Contas a Pagar e Gestão Bancária em Python.

### Stack Técnica Definida:
- **Linguagem:** Python 3.12+
- **Arquitetura:** Monorepo (backend/ e frontend/)
- **Frontend:** Streamlit (`st.navigation`, `httpx` para consumo da API)
- **Backend:** FastAPI, SQLAlchemy 2.0 Async, Pydantic v2
- **Banco de Dados:** SQLite async (`aiosqlite`) via `contas_pagar.db` (abstraído para migração futura para PostgreSQL)
- **Segurança/Auth:** OAuth2 Password Flow, JWT (`pyjwt`), Hash via `pwdlib[bcrypt]`

### Estrutura de Diretórios Atual:
financing/
├── backend/
│   ├── database.py       # Engine e AsyncSessionLocal (SQLAlchemy 2.0)
│   ├── models.py         # Mapeamento ORM (Usuario, PlanoContas, TitulosPagar, etc.)
│   ├── schemas.py        # Validações Pydantic (Token, UsuarioResponse, etc.)
│   ├── security.py       # Gerenciamento de JWT e hash pwdlib
│   ├── main.py           # FastAPI lifespan e rotas principais
│   └── routers/
│       └── auth.py       # Endpoints /auth/token e /auth/me
└── frontend/
    ├── app.py            # Ponto de entrada Streamlit com st.navigation
    ├── api_client.py     # Cliente HTTPX com Bearer Token
    └── views/
        ├── login.py      # Form de Login
        ├── dashboard.py  # Visão geral
        └── titulos.py    # Contas a Pagar

### O que já está implementado e funcionando:
1. Mapeamento relacional completo no SQLAlchemy (`models.py`).
2. Módulo de autenticação JWT funcional com criação de usuário admin no startup.
3. Estrutura de navegação e cliente de API no Streamlit.

### Nosso próximo passo:
Vamos desenvolver o arquivo `backend/routers/titulos.py` (CRUD completo de Contas a Pagar) e a interface correspondente `frontend/views/titulos.py` (tabela interativa e baixa de títulos).