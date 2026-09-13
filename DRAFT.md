
🗄️🛠️🎯

----------------------------------------------------
----------------------------------------------------

### O que já está implementado e funcionando:
- Frontend
  - Estrutura de telas (`app.py`) e navegação (navigation) 
  - Cliente de API no Streamlit (`api_client.py`, login() e logout())
  - Autenticação do usuário (`login.py`)
- Backend
  - Módulo de autenticação JWT
  - Criação de usuário `admin` no startup


### TODO:

- desenvolver o arquivo `backend/routers/titulos.py` (CRUD completo de Contas a Pagar) 
- interface correspondente `frontend/views/titulos.py` (tabela interativa e baixa de títulos).

1. **Modelagem do Banco de Dados:** Essencial para garantir integridade.
Estruture as tabelas principais: `ContasBancarias`, `PlanoDeContas`, `Fornecedores`, `Lancamentos` (Contas a Pagar), `Transferencias` e `Conciliacoes`.

- Mapeamento relacional completo no SQLAlchemy (`models.py`).

2. **Fluxo de Baixa e Movimentação:** Automação do saldo.
Ao dar baixa em um título a pagar, garanta que o sistema debite automaticamente o valor do saldo da `ContaBancaria` selecionada.

3. **Motor de Conciliação:** Validação dos saldos.
Crie uma regra de correspondência por data, valor e conta para facilitar a conferência do extrato do banco com as baixas do sistema.

**Fase 1: Infraestrutura de Dados e Autenticação:** - Estrutura de dados, autenticação e ambiente.

1. **Estrutura do Projeto:** Configurar repositório com diretórios divididos em `/backend` (FastAPI, SQLAlchemy, Schemas) e `/frontend` (Streamlit).
2. **Modelos SQLAlchemy & Migrações:** Criar a tabela de `usuarios` (`id`, `email`, `senha_hash`, `nome`, `ativo`) integrada aos modelos existentes (`plano_contas`, `contas_bancarias`, `titulos_pagar`, `movimentacoes_conta`, `conciliacoes`).
3. **Endpoints de Autenticação:**
    * `POST /api/v1/auth/token`: Valida credenciais e retorna o token `access_token` JWT.
    * `GET /api/v1/auth/me`: Retorna os dados do usuário autenticado.
4. **Camada de Login no Streamlit:** Criar tela de login que armazena o token JWT no `st.session_state` e envia o header `Authorization: Bearer <token>` em todas as chamadas HTTP para a FastAPI via `requests`/`httpx`.


**Fase 2: Gestão Cadastral e Contas a Pagar:** - Cadastros base e lançamento de obrigações.

1. **Endpoints de Cadastros (CRUDs):**
    * Endpoints para gestão de **Plano de Contas**, **Contas Bancárias** e **Fornecedores**.
2. **Endpoints do Contas a Pagar:**
    * `POST /api/v1/titulos`: Cadastro de novos títulos/agendamentos.
    * `GET /api/v1/titulos`: Listagem com filtros por período, fornecedor, status e categoria.
    * `POST /api/v1/titulos/{id}/baixa`: Baixa manual com suporte a juros, descontos e pagamentos parciais.
3. **Interfaces Streamlit:**
    * Form de cadastro de obrigações com seleção de fornecedor e plano de contas.
    * Tabela interativa (`st.dataframe` / `st.data_editor`) listando contas em aberto com botão de baixa manual.


**Fase 3: Gestão de Caixa e Extrato:** - Movimentações de conta e transferências.

1. **Endpoints de Movimentação e Transferências:**
    * `GET /api/v1/movimentacoes/extrato`: Retorna o extrato da conta com cálculo do saldo acumulado linha a linha.
    * `POST /api/v1/transferencias`: Efetua a transferência criando automaticamente as movimentações de `SAIDA` (origem) e `ENTRADA` (destino).
2. **Interfaces Streamlit:**
    * Tela de **Extrato Bancário** com seleção de conta, filtro por data e exibição de saldo atualizado.
    * Formulário de **Transferência entre Contas Propria**.


**Fase 4: Motor de Conciliação Bancária:** - Upload OFX e conciliação por score.

1. **Endpoints de Conciliação:**
    * `POST /api/v1/conciliacao/upload-ofx`: Recebe o arquivo `.ofx`, invoca o *matcher* Python e devolve a lista classificada por nível de confiança (*Exact*, *Flex*, *Parcial*, *Duplicado*).
    * `POST /api/v1/conciliacao/confirmar`: Efetiva o vínculo no banco de dados e atualiza os status dos títulos.
2. **Interface Streamlit:**
    * Tela dedicada ao upload de extrato OFX.
    * Exibição das transações do banco lado a lado com os lançamentos sugeridos do sistema para confirmação em lote ou individual com 1 clique.


**Fase 5: Dashboard, Aging e Migração de Banco:** - Relatórios, visão financeira e deploy.

1. **Endpoints Analíticos:**
    * `GET /api/v1/relatorios/aging`: Dados para o relatório de Aging List (contas em atraso por faixas de dias).
    * `GET /api/v1/relatorios/dre-resumido`: Dados consolidados por plano de contas.
2. **Dashboards no Streamlit:**
    * Visão executiva com indicadores de total a pagar no dia, valores vencidos, gráfico de aging e saldo consolidado das contas.
3. **Migração para Produção:**
    * Alterar a variável de ambiente `DATABASE_URL` no FastAPI para apontar para o banco de dados relacional remoto (ex: PostgreSQL) sem alterar nenhuma regra de código.

- Criar o arquivo docker-compose.yml para subir FastAPI, Streamlit e SQLite/PostgreSQL
- Em produção, ajustar leitura de variáveis de ambiente via pydantic-settings




ESTRUTURA DO PROJETO

financing/
├── .gitignore
├── README.md
├── docker-compose.yml             # (Opcional) Sobe o banco, FastAPI e Streamlit juntos
│
├── backend/                       # API FastAPI + Banco de Dados
│   ├── .env                       # Variáveis de ambiente locais (DATABASE_URL, SECRET_KEY)
│   ├── requirements.txt           # Dependências do backend (fastapi, sqlalchemy, passlib, etc)
│   ├── main.py                    # Inicializa o FastAPI, inclui os roteadores e cria um usuário inicial padrão (Seed) se o banco estiver vazio
│   ├── database.py                # Configuração do SQLAlchemy Engine e AsyncSession
│   ├── models.py                  # Modelos relacionais (ORM)
│   ├── schemas.py                 # Validações Pydantic (Request/Response)
│   ├── security.py                # Hash de senhas (bcrypt), validação de hash rotinas de criação/decodificação de tokens JWT
│   └── routers/                   # Módulos de endpoints por domínio
│       └── auth.py                # Endpoints /auth/token, /auth/register e /auth/me
│       ├── titulos.py
│       └── conciliacao.py
│
└── frontend/                      # Aplicação Streamlit
    ├── .env                       # Variáveis de ambiente (API_BASE_URL)
    ├── requirements.txt           # Dependências do frontend (streamlit, httpx)
    ├── app.py                     # Ponto de entrada do Streamlit (navegação e sidebar; roteamento)
    ├── api_client.py              # Centraliza a comunicação com o Backend; ciente HTTP (httpx); header Bearer <token>
    └── views/                     # Páginas/Telas do sistema
        ├── login.py               # Tela de login
        ├── dashboard.py           # Visão geral
        ├── titulos.py             # Contas a pagar
        └── conciliacao.py

Vamos trabalhar com um único Ambiente Virtuai na raiz, instalando todas as bibliotecas necessárias para rodar tanto o FastAPI quanto o Streamlit.
- Vantagem: Facilita o desenvolvimento e navegação na IDE (VS Code / PyCharm).
- Desvantagem: a imagem Docker ou o servidor de hospedagem do frontend vai instalar dependências do banco de dados/SQLAlchemy sem necessidade.




<details>
<summary>MODELAGEM DO BANCO DE DADOS</summary>

Modelo relacional completo estruturado para garantir **integridade referencial**, **rastreabilidade** e **precisão de saldos**.

### Visão Geral das Entidades

1. **`plano_contas`**: Estrutura hierárquica de categorias de despesas (e receitas/transferências).
2. **`contas_bancarias`**: Contas correntes, caixas ou cartões de onde saem/entram os recursos.
3. **`fornecedores`**: Cadastro de favorecidos/fornecedores dos pagamentos.
4. **`titulos_pagar`**: As obrigações/despesas agendadas ou liquidadas.
5. **`movimentacoes_conta`**: O livro-razão (*ledger*) de todas as saídas, entradas e transferências que impactam o saldo real de uma conta.
6. **`transferencias`**: Registro das movimentações entre contas próprias (associa duas `movimentacoes_conta`).
7. **`conciliacoes`**: Registro dos confrontos de extrato bancário (OFX/CSV) com os lançamentos do sistema.

### DDL / Estrutura das Tabelas (SQL)

```sql
-- 1. PLANO DE CONTAS
CREATE TABLE plano_contas (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL UNIQUE, -- Ex: "1.01", "1.01.001"
    nome VARCHAR(100) NOT NULL,
    tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('DESPESA', 'RECEITA', 'TRANSFERENCIA')),
    id_pai INT REFERENCES plano_contas(id) ON DELETE RESTRICT,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. CONTAS BANCÁRIAS / CAIXA
CREATE TABLE contas_bancarias (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL, -- Ex: "Itaú - Conta Corrente Principal"
    banco_codigo VARCHAR(10),   -- Ex: "341"
    agencia VARCHAR(20),
    numero_conta VARCHAR(20),
    saldo_inicial DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. FORNECEDORES
CREATE TABLE fornecedores (
    id SERIAL PRIMARY KEY,
    nome_razao VARCHAR(150) NOT NULL,
    cpf_cnpj VARCHAR(20) UNIQUE,
    email VARCHAR(100),
    telefone VARCHAR(20),
    chave_pix VARCHAR(100),
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. TÍTULOS A PAGAR (Contas a Pagar)
CREATE TABLE titulos_pagar (
    id SERIAL PRIMARY KEY,
    id_fornecedor INT NOT NULL REFERENCES fornecedores(id) ON DELETE RESTRICT,
    id_plano_contas INT NOT NULL REFERENCES plano_contas(id) ON DELETE RESTRICT,
    id_conta_bancaria_prevista INT REFERENCES contas_bancarias(id) ON DELETE SET NULL,
    
    descricao VARCHAR(200) NOT NULL,
    numero_documento VARCHAR(50),
    
    data_emissao DATE NOT NULL,
    data_vencimento DATE NOT NULL,
    data_pagamento DATE, -- Preenchido quando quitado
    
    valor_original DECIMAL(15, 2) NOT NULL CHECK (valor_original > 0),
    valor_desconto DECIMAL(15, 2) DEFAULT 0.00,
    valor_juros_multa DECIMAL(15, 2) DEFAULT 0.00,
    valor_pago DECIMAL(15, 2) DEFAULT 0.00, -- (valor_original - valor_desconto + valor_juros_multa)
    
    status VARCHAR(20) NOT NULL DEFAULT 'PENDENTE' 
        CHECK (status IN ('PENDENTE', 'PAGO', 'PARCIAL', 'CANCELADO')),
    
    recorrente BOOLEAN DEFAULT FALSE,
    anexo_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. MOVIMENTAÇÕES DE CONTA (Extrato Interno / Ledger)
CREATE TABLE movimentacoes_conta (
    id SERIAL PRIMARY KEY,
    id_conta_bancaria INT NOT NULL REFERENCES contas_bancarias(id) ON DELETE RESTRICT,
    id_titulo_pagar INT REFERENCES titulos_pagar(id) ON DELETE SET NULL, -- Vinculo se for quitação
    
    data_movimento DATE NOT NULL,
    tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('ENTRADA', 'SAIDA')),
    valor DECIMAL(15, 2) NOT NULL CHECK (valor > 0),
    descricao VARCHAR(200) NOT NULL,
    
    conciliado BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. TRANSFERÊNCIAS ENTRE CONTAS
CREATE TABLE transferencias (
    id SERIAL PRIMARY KEY,
    id_movimento_origem INT NOT NULL UNIQUE REFERENCES movimentacoes_conta(id) ON DELETE CASCADE,
    id_movimento_destino INT NOT NULL UNIQUE REFERENCES movimentacoes_conta(id) ON DELETE CASCADE,
    data_transferencia DATE NOT NULL,
    valor DECIMAL(15, 2) NOT NULL CHECK (valor > 0),
    observacao VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. CONCILIAÇÃO BANCÁRIA
CREATE TABLE conciliacoes (
    id SERIAL PRIMARY KEY,
    id_movimento_conta INT NOT NULL REFERENCES movimentacoes_conta(id) ON DELETE CASCADE,
    data_extrato DATE NOT NULL,
    fitid_ofx VARCHAR(100), -- Identificador único do lançamento na transação OFX/Banco
    descricao_extrato VARCHAR(200),
    valor_extrato DECIMAL(15, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

```

-----


### 1. Configuração do Banco e Conexão (`database.py`)

Ajuste a `DATABASE_URL` conforme o seu banco de dados (PostgreSQL, SQLite async, etc.).

```python
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# Para SQLite: "sqlite+aiosqlite:///./contas_pagar.db"
# Para PostgreSQL: "postgresql+asyncpg://usuario:senha@localhost:5432/nome_banco"
DATABASE_URL = "sqlite+aiosqlite:///./contas_pagar.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Altere para True se quiser ver o SQL gerado no terminal
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

class Base(DeclarativeBase):
    """Classe base declarativa para os modelos ORM."""
    pass

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection para sessões no FastAPI ou rotinas async."""
    async with AsyncSessionLocal() as session:
        yield session

async def init_db() -> None:
    """Cria todas as tabelas no banco de dados se não existirem."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

```

---

### 2. Mapeamento dos Modelos ORM (`models.py`)

Usa a sintaxe `Mapped[...]` e `mapped_column()` do SQLAlchemy 2.0 com tipos estáticos rigorosos.

```python
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import (
    String, Numeric, Boolean, Date, DateTime, ForeignKey, CheckConstraint, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class PlanoContas(Base):
    __tablename__ = "plano_contas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo: Mapped[str] = mapped_column(String(10), nullable=False) # 'DESPESA', 'RECEITA', 'TRANSFERENCIA'
    id_pai: Mapped[Optional[int]] = mapped_column(ForeignKey("plano_contas.id", ondelete="RESTRICT"))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relacionamentos
    filhos: Mapped[List["PlanoContas"]] = relationship("PlanoContas", backref="pai", remote_side=[id])
    titulos: Mapped[List["TitulosPagar"]] = relationship("TitulosPagar", back_populates="plano_contas")

    __table_args__ = (
        CheckConstraint("tipo IN ('DESPESA', 'RECEITA', 'TRANSFERENCIA')", name="chk_plano_contas_tipo"),
    )


class ContasBancarias(Base):
    __tablename__ = "contas_bancarias"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    banco_codigo: Mapped[Optional[str]] = mapped_column(String(10))
    agencia: Mapped[Optional[str]] = mapped_column(String(20))
    numero_conta: Mapped[Optional[str]] = mapped_column(String(20))
    saldo_inicial: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relacionamentos
    movimentacoes: Mapped[List["MovimentacoesConta"]] = relationship("MovimentacoesConta", back_populates="conta_bancaria")


class Fornecedores(Base):
    __tablename__ = "fornecedores"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome_razao: Mapped[str] = mapped_column(String(150), nullable=False)
    cpf_cnpj: Mapped[Optional[str]] = mapped_column(String(20), unique=True)
    email: Mapped[Optional[str]] = mapped_column(String(100))
    telefone: Mapped[Optional[str]] = mapped_column(String(20))
    chave_pix: Mapped[Optional[str]] = mapped_column(String(100))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relacionamentos
    titulos: Mapped[List["TitulosPagar"]] = relationship("TitulosPagar", back_populates="fornecedor")


class TitulosPagar(Base):
    __tablename__ = "titulos_pagar"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_fornecedor: Mapped[int] = mapped_column(ForeignKey("fornecedores.id", ondelete="RESTRICT"), nullable=False)
    id_plano_contas: Mapped[int] = mapped_column(ForeignKey("plano_contas.id", ondelete="RESTRICT"), nullable=False)
    id_conta_bancaria_prevista: Mapped[Optional[int]] = mapped_column(ForeignKey("contas_bancarias.id", ondelete="SET NULL"))

    descricao: Mapped[str] = mapped_column(String(200), nullable=False)
    numero_documento: Mapped[Optional[str]] = mapped_column(String(50))

    data_emissao: Mapped[date] = mapped_column(Date, nullable=False)
    data_vencimento: Mapped[date] = mapped_column(Date, nullable=False)
    data_pagamento: Mapped[Optional[date]] = mapped_column(Date)

    valor_original: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    valor_desconto: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    valor_juros_multa: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    valor_pago: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))

    status: Mapped[str] = mapped_column(String(20), default="PENDENTE") # PENDENTE, PAGO, PARCIAL, CANCELADO
    recorrente: Mapped[bool] = mapped_column(Boolean, default=False)
    anexo_url: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relacionamentos
    fornecedor: Mapped["Fornecedores"] = relationship("Fornecedores", back_populates="titulos")
    plano_contas: Mapped["PlanoContas"] = relationship("PlanoContas", back_populates="titulos")
    movimentacoes: Mapped[List["MovimentacoesConta"]] = relationship("MovimentacoesConta", back_populates="titulo_pagar")

    __table_args__ = (
        CheckConstraint("status IN ('PENDENTE', 'PAGO', 'PARCIAL', 'CANCELADO')", name="chk_titulos_status"),
        CheckConstraint("valor_original > 0", name="chk_titulos_valor_pos"),
    )


class MovimentacoesConta(Base):
    __tablename__ = "movimentacoes_conta"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_conta_bancaria: Mapped[int] = mapped_column(ForeignKey("contas_bancarias.id", ondelete="RESTRICT"), nullable=False)
    id_titulo_pagar: Mapped[Optional[int]] = mapped_column(ForeignKey("titulos_pagar.id", ondelete="SET NULL"))

    data_movimento: Mapped[date] = mapped_column(Date, nullable=False)
    tipo: Mapped[str] = mapped_column(String(10), nullable=False) # ENTRADA, SAIDA
    valor: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    descricao: Mapped[str] = mapped_column(String(200), nullable=False)
    conciliado: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relacionamentos
    conta_bancaria: Mapped["ContasBancarias"] = relationship("ContasBancarias", back_populates="movimentacoes")
    titulo_pagar: Mapped[Optional["TitulosPagar"]] = relationship("TitulosPagar", back_populates="movimentacoes")
    conciliacao: Mapped[Optional["Conciliacoes"]] = relationship("Conciliacoes", back_populates="movimentacao_conta", uselist=False)

    __table_args__ = (
        CheckConstraint("tipo IN ('ENTRADA', 'SAIDA')", name="chk_mov_tipo"),
        CheckConstraint("valor > 0", name="chk_mov_valor_pos"),
    )


class Transferencias(Base):
    __tablename__ = "transferencias"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_movimento_origem: Mapped[int] = mapped_column(ForeignKey("movimentacoes_conta.id", ondelete="CASCADE"), unique=True, nullable=False)
    id_movimento_destino: Mapped[int] = mapped_column(ForeignKey("movimentacoes_conta.id", ondelete="CASCADE"), unique=True, nullable=False)
    data_transferencia: Mapped[date] = mapped_column(Date, nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    observacao: Mapped[Optional[str]] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    movimento_origem: Mapped["MovimentacoesConta"] = relationship("MovimentacoesConta", foreign_keys=[id_movimento_origem])
    movimento_destino: Mapped["MovimentacoesConta"] = relationship("MovimentacoesConta", foreign_keys=[id_movimento_destino])


class Conciliacoes(Base):
    __tablename__ = "conciliacoes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_movimento_conta: Mapped[int] = mapped_column(ForeignKey("movimentacoes_conta.id", ondelete="CASCADE"), nullable=False)
    data_extrato: Mapped[date] = mapped_column(Date, nullable=False)
    fitid_ofx: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    descricao_extrato: Mapped[Optional[str]] = mapped_column(String(200))
    valor_extrato: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relacionamento
    movimentacao_conta: Mapped["MovimentacoesConta"] = relationship("MovimentacoesConta", back_populates="conciliacao")

```

---

### 3. Script de Inicialização e População de Dados (`seed.py`)

Script assíncrono para criar as tabelas e popular dados iniciais para testes.

```python
import asyncio
from datetime import date
from decimal import Decimal
from database import init_db, AsyncSessionLocal
from models import PlanoContas, ContasBancarias, Fornecedores, TitulosPagar

async def seed_data():
    # 1. Cria a estrutura de tabelas
    await init_db()
    
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # 2. Plano de Contas Basico
            pc_despesas = PlanoContas(codigo="2.0", nome="Despesas Operacionais", tipo="DESPESA")
            session.add(pc_despesas)
            await session.flush()

            pc_aluguel = PlanoContas(codigo="2.1", nome="Aluguel e Imóveis", tipo="DESPESA", id_pai=pc_despesas.id)
            pc_servicos = PlanoContas(codigo="2.2", nome="Serviços e Utilidades", tipo="DESPESA", id_pai=pc_despesas.id)
            session.add_all([pc_aluguel, pc_servicos])

            # 3. Conta Bancária
            conta_itau = ContasBancarias(
                nome="Itaú Principal",
                banco_codigo="341",
                agencia="1234",
                numero_conta="56789-0",
                saldo_inicial=Decimal("5000.00")
            )
            session.add(conta_itau)

            # 4. Fornecedor
            fornecedor_provedor = Fornecedores(
                nome_razao="Provedor de Internet Telecom S/A",
                cpf_cnpj="12.345.678/0001-90",
                email="financeiro@telecom.com"
            )
            session.add(fornecedor_provedor)
            await session.flush()

            # 5. Título a Pagar de Teste
            titulo = TitulosPagar(
                id_fornecedor=fornecedor_provedor.id,
                id_plano_contas=pc_servicos.id,
                descricao="Fatura Internet Fibra - Setembro/2026",
                numero_documento="DOC-99812",
                data_emissao=date(2026, 9, 1),
                data_vencimento=date(2026, 9, 15),
                valor_original=Decimal("250.00"),
                status="PENDENTE"
            )
            session.add(titulo)

        print("✅ Banco inicializado e populado com sucesso!")

if __name__ == "__main__":
    asyncio.run(seed_data())

```

</details>


--------------------

<details>
<summary>Escreva as queries SQL essenciais do sistema: cálculo de saldo acumulado linha a linha (extrato), relatório de contas em aberto (aging) e DRE simples por plano de contas.</summary>

## Escreva as queries SQL essenciais do sistema: cálculo de saldo acumulado linha a linha (extrato), relatório de contas em aberto (aging) e DRE simples por plano de contas.

Aqui estão as **queries SQL essenciais** construídas para o modelo relacional definido anterior.

Elas utilizam funções de janela (*window functions*) do SQL padrão (compatíveis com PostgreSQL, MySQL 8+, SQLite 3.25+ e SQL Server) para garantir eficiência no cálculo do extrato e dos relatórios.

---

### 1. Extrato por Conta Corrente com Saldo Acumulado (*Linha a Linha*)

Esta consulta recupera todas as movimentações de uma determinada conta e calcula o **saldo progressivo** a cada linha, considerando o `saldo_inicial` cadastrado na conta bancária.

```sql
WITH saldo_base AS (
    -- Busca o saldo inicial da conta bancária escolhida (ex: id_conta = 1)
    SELECT id, saldo_inicial 
    FROM contas_bancarias 
    WHERE id = 1
)
SELECT 
    m.id AS movimento_id,
    m.data_movimento,
    m.descricao,
    m.tipo,
    m.valor,
    m.conciliado,
    -- Calcula a variação líquida do lançamento (Entrada +, Saída -)
    CASE 
        WHEN m.tipo = 'ENTRADA' THEN m.valor 
        ELSE -m.valor 
    END AS valor_liquido,
    -- Soma o saldo inicial + a soma acumulada de todas as movimentações até a linha atual
    sb.saldo_inicial + SUM(
        CASE 
            WHEN m.tipo = 'ENTRADA' THEN m.valor 
            ELSE -m.valor 
        END
    ) OVER (
        PARTITION BY m.id_conta_bancaria 
        ORDER BY m.data_movimento ASC, m.id ASC
    ) AS saldo_acumulado
FROM movimentacoes_conta m
CROSS JOIN saldo_base sb
WHERE m.id_conta_bancaria = 1
  AND m.data_movimento BETWEEN '2026-09-01' AND '2026-09-30'
ORDER BY m.data_movimento ASC, m.id ASC;

```

---

### 2. Relatório de Contas a Pagar em Aberto (*Aging List*)

Gera a listagem de títulos **PENDENTES** e **PARCIAIS**, agrupando os débitos por faixas de atraso (*Aging*) com base na data atual (`CURRENT_DATE`).

```sql
SELECT 
    t.id AS titulo_id,
    f.nome_razao AS fornecedor,
    p.nome AS categoria_plano_contas,
    t.numero_documento,
    t.descricao,
    t.data_vencimento,
    (t.valor_original - t.valor_desconto + t.valor_juros_multa - t.valor_pago) AS valor_em_aberto,
    
    -- Dias de atraso (valores positivos indicam que já venceu)
    (CURRENT_DATE - t.data_vencimento) AS dias_atraso,
    
    -- Classificação do Aging
    CASE 
        WHEN (CURRENT_DATE - t.data_vencimento) <= 0 THEN 'A Vencer'
        WHEN (CURRENT_DATE - t.data_vencimento) BETWEEN 1 AND 30 THEN '1 a 30 dias'
        WHEN (CURRENT_DATE - t.data_vencimento) BETWEEN 31 AND 60 THEN '31 a 60 dias'
        WHEN (CURRENT_DATE - t.data_vencimento) BETWEEN 61 AND 90 THEN '61 a 90 dias'
        ELSE 'Acima de 90 dias'
    END AS faixa_aging

FROM titulos_pagar t
JOIN fornecedores f ON f.id = t.id_fornecedor
JOIN plano_contas p ON p.id = t.id_plano_contas
WHERE t.status IN ('PENDENTE', 'PARCIAL')
ORDER BY t.data_vencimento ASC;

```

#### Visão Sintética do Aging (Resumo do Passivo em Aberto):

Se precisar do valor total devido por faixa de atraso para dashboard/gráfico:

```sql
SELECT 
    CASE 
        WHEN (CURRENT_DATE - t.data_vencimento) <= 0 THEN 'A Vencer'
        WHEN (CURRENT_DATE - t.data_vencimento) BETWEEN 1 AND 30 THEN '1 a 30 dias'
        WHEN (CURRENT_DATE - t.data_vencimento) BETWEEN 31 AND 60 THEN '31 a 60 dias'
        WHEN (CURRENT_DATE - t.data_vencimento) BETWEEN 61 AND 90 THEN '61 a 90 dias'
        ELSE 'Acima de 90 dias'
    END AS faixa_aging,
    COUNT(t.id) AS qtd_titulos,
    SUM(t.valor_original - t.valor_desconto + t.valor_juros_multa - t.valor_pago) AS total_aberto
FROM titulos_pagar t
WHERE t.status IN ('PENDENTE', 'PARCIAL')
GROUP BY 1
ORDER BY MIN(t.data_vencimento) ASC;

```

---


### 3. DRE Simplificada por Plano de Contas (*Regime de Caixa / Efetuados*)

Soma as saídas e entradas reais do período consultado agrupando pelas categorias do `plano_contas`. Ignora movimentações do tipo `TRANSFERENCIA` para não distorcer o resultado financeiro.

```sql
SELECT 
    p.codigo AS codigo_plano,
    p.nome AS categoria,
    p.tipo AS natureza_categoria,
    
    -- Totalizador por categoria
    SUM(
        CASE 
            WHEN m.tipo = 'ENTRADA' THEN m.valor 
            ELSE -m.valor 
        END
    ) AS resultado_financeiro

FROM movimentacoes_conta m
-- Relaciona a movimentação com a despesa do contas a pagar para obter o plano de contas
JOIN titulos_pagar t ON t.id = m.id_titulo_pagar
JOIN plano_contas p ON p.id = t.id_plano_contas

WHERE m.data_movimento BETWEEN '2026-09-01' AND '2026-09-30'
  AND p.tipo IN ('RECEITA', 'DESPESA') -- Filtra fora as contas de transferência interna

GROUP BY p.id, p.codigo, p.nome, p.tipo
ORDER BY p.codigo ASC;

```

---

### Resumo das Regras Aplicadas

* **Integridade das Transferências:** As queries do DRE e de extrato isolam registros de transferências do resultado de despesas reais do negócio.
* **Extrato Dinâmico:** A *Window Function* (`SUM() OVER (...)`) calcula o saldo histórico em tempo de execução sem a necessidade de gravar saldos consolidados na tabela de contas, evitando inconsistência por edições ou exclusões retroativas.
* **Aging Atualizado:** O aging é calculado dinamicamente considerando a diferença entre `CURRENT_DATE` e a data de vencimento real do título.

---

## TODO: Criar o script de inserção com dados de teste (Seeds SQL)

--------------------

<details>
<summary>Desenhar a arquitetura da rotina de importação de arquivo OFX</summary>

## Desenhar a arquitetura da rotina de importação de arquivo OFX
Explique a lógica e os passos para processar um arquivo de extrato bancário no formato OFX e realizar o matching automático com os lançamentos.

O processamento de arquivos OFX (*Open Financial Exchange*) para conciliação bancária baseia-se em extrair transações estruturadas e aplicar algoritmos de divergência (data, valor e identificador) para vinculá-las aos lançamentos do sistema.

---

### Estrutura Base do Arquivo OFX

Um arquivo OFX é um formato baseado em SGML/XML. Para a conciliação, as tags essenciais dentro do bloco `<BANKTRANLIST>` são:

* **`<TRNTYPE>`:** Tipo da transação (`DEBIT` para saídas, `CREDIT` para entradas).
* **`<DTPOSTED>`:** Data em que a transação foi processada no banco (formato `YYYYMMDDHHMMSS`).
* **`<TRNAMT>`:** Valor da transação (negativo para saídas, positivo para entradas).
* **`<FITID>`:** *Financial Institution Transaction ID* — o identificador único universal da transação no banco.
* **`<MEMO>` / `<NAME>`:** Descrição ou histórico do lançamento no extrato bancário.

---

### Algoritmo de Conciliação e *Matching*

O processo de conciliação automática segue **5 etapas sequenciais**:

1. **Leitura e Parsing do OFX:** Extração e padronização dos dados do banco.
1. Parsear o arquivo OFX e extrair a lista de transações bancárias.
2. Validar o número da conta/agência presente no cabeçalho (`<BANKID>` e `<ACCTID>`) para garantir que o arquivo pertence à `conta_bancaria` selecionada no sistema.
3. Converter datas e valores para o padrão do banco de dados (ex: converter `<TRNAMT>-150.00</TRNAMT>` em `tipo = 'SAIDA'` e `valor = 150.00`).


2. **Filtragem de Duplicidades (Check por FITID):** Evita reprocessar a mesma transação.
1. Para cada transação do OFX, verificar se o `<FITID>` já existe cadastrado na tabela `conciliacoes`.
2. Se o `FITID` já existir, a transação é ignorada ou marcada como **Já Conciliada**, garantindo idempotência ao importar o mesmo extrato múltiplas vezes.


3. **Matching de Precisão Exata (Score 100%):** Identificação inequívoca de lançamentos no sistema.
Buscar no banco de dados por movimentações não conciliadas (`conciliado = FALSE`) na mesma conta que atendam a **todos** os critérios:

* **Valor Exato:** `movimentacao.valor == ofx.valor`
* **Tipo Exato:** `movimentacao.tipo == ofx.tipo`
* **Data Exata:** `movimentacao.data_movimento == ofx.data`

*Ação:* Se encontrar exatamente 1 correspondência, o sistema sugere/vincula com **alta confiança**.


4. **Matching por Tolerância / Regras Flexíveis (Score 70% - 90%):** Aplica tolerância temporal e de baixas pendentes.
Se o passo anterior não encontrar correspondência, o algoritmo relaxa os critérios:

* **Tolerância de Datas (Janela de D+3 / D-3):** Busca movimentações ou títulos abertos com o mesmo valor, porém com diferença de até 3 dias úteis (para compensação de boletos, PIX agendado ou finais de semana).
* **Busca em Títulos a Pagar (Sem Baixa):** Caso não exista uma `movimentacao_conta` criada, busca em `titulos_pagar` pendentes com o mesmo valor e vencimento próximo.

*Ação:* O sistema classifica a sugestão com score médio e exige confirmação com 1 clique do usuário.


5. **Gravação da Conciliação e Ajuste de Saldo:** Efetivação do vínculo no banco de dados.
Quando uma transação do OFX é conciliada (automaticamente ou manualmente):

1. Caso o vínculo seja com um título a pagar pendente, registra-se a baixa do título e cria-se a `movimentacao_conta`.
2. Insere-se o registro na tabela `conciliacoes` salvando o `fitid_ofx`.
3. Atualiza-se a `movimentacao_conta` atribuindo `conciliado = TRUE`.


---

### Resumo das Regras de Sugestão de Matching

| Nível de Confiança | Critérios de Associação | Ação Recomendada do Sistema |
| --- | --- | --- |
| **Conciliado Anteriormente** | `fitid_ofx` já cadastrado na tabela `conciliacoes`. | Ocultar da lista ou marcar como processado. |
| **Alta Confiança (Exact Match)** | Mesma conta + Mesmo valor + Mesma data exata. | Aprovado automaticamente (ou confirmação em lote). |
| **Média Confiança (Flex Match)** | Mesma conta + Mesmo valor + Datas com diferença de ±3 dias. | Exibir no topo da lista com botão "Confirmar". |
| **Sem Match (Lançamento Novo)** | Nenhuma movimentação ou título encontrado com o mesmo valor no período. | Sugerir botões: "Criar Nova Despesa", "Registrar Transferência" ou "Ignorar". |

Esta implementação em Python 3.12 utiliza a biblioteca `ofxparse` para ler o arquivo OFX e executa o algoritmo de matching baseado em pontuação (*scoring*), associando as transações do banco com as movimentações e títulos pendentes registrados no banco de dados.

---

### Módulo de Parsing e Matching (`ofx_matcher.py`)

```python
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any
import ofxparse

class MatchConfidence(Enum):
    EXACT = "ALTA_CONFIANCA"     # Score 100: Conta, Valor, Tipo e Data exata
    FLEX = "MEDIA_CONFIANCA"    # Score 70-90: Conta, Valor e Data próxima (D±3)
    NONE = "SEM_MATCH"          # Score 0: Nenhuma correspondência encontrada
    DUPLICATE = "JA_CONCILIADO"  # FITID já processado anteriormente

@dataclass
class OFXTransaction:
    fitid: str
    trntype: str  # 'DEBIT' ou 'CREDIT'
    dtposted: date
    amount: Decimal
    memo: str

@dataclass
class MatchResult:
    ofx_tx: OFXTransaction
    confidence: MatchConfidence
    score: int
    matched_movimento_id: Optional[int] = None
    matched_titulo_id: Optional[int] = None
    reason: str = ""

def parse_ofx(file_stream) -> List[OFXTransaction]:
    """
    Realiza o parse do arquivo/stream OFX utilizando ofxparse 
    e padroniza os dados para a estrutura interna.
    """
    ofx = ofxparse.OfxParser.parse(file_stream)
    account = ofx.account
    statement = account.statement
    
    transactions = []
    for tx in statement.transactions:
        # Padroniza o valor para Decimal absoluto e define o tipo
        amount = Decimal(str(abs(tx.amount)))
        trntype = "SAIDA" if tx.amount < 0 else "ENTRADA"
        
        transactions.append(
            OFXTransaction(
                fitid=str(tx.id).strip(),
                trntype=trntype,
                dtposted=tx.date.date() if isinstance(tx.date, datetime) else tx.date,
                amount=amount,
                memo=str(tx.memo or tx.payee or "").strip()
            )
        )
    return transactions


def match_transactions(
    ofx_transactions: List[OFXTransaction],
    conta_id: int,
    fitids_conciliados: set[str],
    movimentacoes_pendentes: List[Dict[str, Any]],
    titulos_abertos: List[Dict[str, Any]],
    dias_tolerancia: int = 3
) -> List[MatchResult]:
    """
    Executa a lógica de matching entre transações do OFX e os dados do sistema.
    
    :param ofx_transactions: Lista de transações extraídas do OFX.
    :param conta_id: ID da conta bancária sendo conciliada.
    :param fitids_conciliados: Conjunto de FITIDs já registrados na tabela `conciliacoes`.
    :param movimentacoes_pendentes: Movimentações não conciliadas da conta.
           Ex: [{'id': 10, 'data': date(2026, 9, 10), 'tipo': 'SAIDA', 'valor': Decimal('150.00')}]
    :param titulos_abertos: Títulos a pagar/receber em aberto.
           Ex: [{'id': 101, 'data_vencimento': date(2026, 9, 10), 'valor_liquido': Decimal('150.00')}]
    :param dias_tolerancia: Janela de dias para match flexível.
    """
    results: List[MatchResult] = []
    movimentacoes_utilizadas = set()
    titulos_utilizados = set()

    for tx in ofx_transactions:
        # 1. Checagem de Idempotência / Duplicidade
        if tx.fitid in fitids_conciliados:
            results.append(
                MatchResult(
                    ofx_tx=tx,
                    confidence=MatchConfidence.DUPLICATE,
                    score=0,
                    reason="Transação (FITID) já conciliada anteriormente."
                )
            )
            continue

        best_match = None
        highest_score = 0
        matched_mov_id = None
        matched_tit_id = None
        match_reason = "Nenhuma correspondência encontrada."

        # 2. Busca em Movimentações de Conta (Extrato Interno)
        for mov in movimentacoes_pendentes:
            if mov['id'] in movimentacoes_utilizadas:
                continue

            # Validações rígidas de Tipo e Valor
            if mov['tipo'] != tx.trntype or mov['valor'] != tx.amount:
                continue

            dias_diff = abs((tx.dtposted - mov['data_movimento']).days)

            if dias_diff == 0:
                # Match Perfeito em Movimentação
                highest_score = 100
                matched_mov_id = mov['id']
                match_reason = "Correspondência exata de data, valor e tipo na movimentação."
                break
            elif dias_diff <= dias_tolerancia:
                score = 90 - (dias_diff * 5) # Ex: 1 dia = 85, 2 dias = 80...
                if score > highest_score:
                    highest_score = score
                    matched_mov_id = mov['id']
                    match_reason = f"Correspondência flexível na movimentação (Diferença de {dias_diff} dia(s))."

        # 3. Busca em Títulos a Pagar/Receber Pendentes (caso não achou match exato)
        if highest_score < 100:
            for tit in titulos_abertos:
                if tit['id'] in titulos_utilizados:
                    continue

                if tit['valor_liquido'] != tx.amount:
                    continue

                dias_diff = abs((tx.dtposted - tit['data_vencimento']).days)

                if dias_diff <= dias_tolerancia:
                    # Títulos ganham pontuação ligeiramente menor que movimentações já lançadas
                    score = 80 - (dias_diff * 5)
                    if score > highest_score:
                        highest_score = score
                        matched_mov_id = None  # Reseta movimentação se o título for melhor
                        matched_tit_id = tit['id']
                        match_reason = f"Sugestão de baixa de título em aberto (Diferença de {dias_diff} dia(s))."

        # 4. Classificação final conforme a pontuação
        if highest_score == 100:
            confidence = MatchConfidence.EXACT
            movimentacoes_utilizadas.add(matched_mov_id)
        elif highest_score >= 60:
            confidence = MatchConfidence.FLEX
            if matched_mov_id:
                movimentacoes_utilizadas.add(matched_mov_id)
            if matched_tit_id:
                titulos_utilizados.add(matched_tit_id)
        else:
            confidence = MatchConfidence.NONE

        results.append(
            MatchResult(
                ofx_tx=tx,
                confidence=confidence,
                score=highest_score,
                matched_movimento_id=matched_mov_id,
                matched_titulo_id=matched_tit_id,
                reason=match_reason
            )
        )

    return results

```

---

### Exemplo de Uso Prático

```python
from io import StringIO
from decimal import Decimal
from datetime import date

# Dados simulados do Banco de Dados
fitids_no_banco = {"FITID-2026-001"}

movimentacoes_db = [
    {"id": 50, "data_movimento": date(2026, 9, 10), "tipo": "SAIDA", "valor": Decimal("150.00")},
    {"id": 51, "data_movimento": date(2026, 9, 8), "tipo": "SAIDA", "valor": Decimal("450.00")}
]

titulos_db = [
    {"id": 201, "data_vencimento": date(2026, 9, 11), "valor_liquido": Decimal("89.90")}
]

# Conteúdo simulado de um arquivo OFX
sample_ofx = """
OFXHEADER:100
DATA:OFXSGML
<OFX>
  <BANKMSGSRSV1>
    <STMTTRNRS>
      <STMTRS>
        <BANKTRANLIST>
          <STMTTRN>
            <TRNTYPE>DEBIT</TRNTYPE>
            <DTPOSTED>20260910120000</DTPOSTED>
            <TRNAMT>-150.00</TRNAMT>
            <FITID>FITID-2026-002</FITID>
            <MEMO>PAGTO FORNECEDOR ABC</MEMO>
          </STMTTRN>
          <STMTTRN>
            <TRNTYPE>DEBIT</TRNTYPE>
            <DTPOSTED>20260910120000</DTPOSTED>
            <TRNAMT>-89.90</TRNAMT>
            <FITID>FITID-2026-003</FITID>
            <MEMO>INTERNET FIBRA</MEMO>
          </STMTTRN>
        </BANKTRANLIST>
      </STMTRS>
    </STMTTRNRS>
  </BANKMSGSRSV1>
</OFX>
"""

# Execução
transacoes_ofx = parse_ofx(StringIO(sample_ofx))
resultados = match_transactions(
    ofx_transactions=transacoes_ofx,
    conta_id=1,
    fitids_conciliados=fitids_no_banco,
    movimentacoes_pendentes=movimentacoes_db,
    titulos_abertos=titulos_db
)

# Exibição do Resultado
for res in resultados:
    print(f"[{res.confidence.value}] Score: {res.score} | FITID: {res.ofx_tx.fitid} | R$ {res.ofx_tx.amount}")
    print(f"  └─ Movimento ID: {res.matched_movimento_id} | Título ID: {res.matched_tit_id}")
    print(f"  └─ Detalhe: {res.reason}\n")

```

---

### Destaques da Implementação

* **Consumo Eficiente de Memória:** Usa `StringIO` ou *file streams* de bibliotecas padrão com `ofxparse` para ler arquivos direto do upload.
* **Prevenção de Dupla Associação:** Mantém conjuntos (`movimentacoes_utilizadas` e `titulos_utilizados`) para impedir que a mesma movimentação do sistema seja vinculada a duas transações do OFX na mesma execução.
* **Priorização do Ledger:** Tenta vincular primeiro com movimentações já registradas (`movimentacoes_conta`) e só recorre aos `titulos_pagar` pendentes caso não ache movimentação lançada.

## Ajuste o script Python para lidar com transações do OFX cujos valores diferem dos títulos por conta de juros, multas ou tarifas bancárias.

---

##

Aqui está a atualização do módulo de *matching* em Python.

Para tratar variações de valor causadas por **juros, multas ou tarifas bancárias**, introduzimos uma **margem de tolerância percentual/absoluta** e uma estrutura para registrar esses acréscimos ou decréscimos durante a baixa do título.

---

### Módulo Ajustado (`ofx_matcher_v2.py`)

```python
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any
from io import StringIO
import ofxparse

class MatchConfidence(Enum):
    EXACT = "ALTA_CONFIANCA"           # Match 100% de valor e data exata
    EXACT_WITH_ADJUSTMENT = "ALTA_COM_AJUSTE" # Data próxima + Valor dentro da tolerância (com juros/multa/desconto)
    FLEX = "MEDIA_CONFIANCA"          # Data flexível (D±3) e/ou pequena divergência de valor
    NONE = "SEM_MATCH"                # Nenhuma correspondência
    DUPLICATE = "JA_CONCILIADO"        # FITID já processado

@dataclass
class OFXTransaction:
    fitid: str
    trntype: str  # 'DEBIT' ou 'CREDIT'
    dtposted: date
    amount: Decimal
    memo: str

@dataclass
class MatchResult:
    ofx_tx: OFXTransaction
    confidence: MatchConfidence
    score: int
    matched_movimento_id: Optional[int] = None
    matched_titulo_id: Optional[int] = None
    
    # Campos para conciliação com divergência financeira
    valor_titulo_original: Optional[Decimal] = None
    valor_juros_multa: Decimal = Decimal("0.00")
    valor_desconto_tarifa: Decimal = Decimal("0.00")
    
    reason: str = ""

def parse_ofx(file_stream) -> List[OFXTransaction]:
    ofx = ofxparse.OfxParser.parse(file_stream)
    transactions = []
    for tx in ofx.account.statement.transactions:
        amount = Decimal(str(abs(tx.amount)))
        trntype = "SAIDA" if tx.amount < 0 else "ENTRADA"
        transactions.append(
            OFXTransaction(
                fitid=str(tx.id).strip(),
                trntype=trntype,
                dtposted=tx.date.date() if isinstance(tx.date, datetime) else tx.date,
                amount=amount,
                memo=str(tx.memo or tx.payee or "").strip()
            )
        )
    return transactions


def match_transactions(
    ofx_transactions: List[OFXTransaction],
    conta_id: int,
    fitids_conciliados: set[str],
    movimentacoes_pendentes: List[Dict[str, Any]],
    titulos_abertos: List[Dict[str, Any]],
    dias_tolerancia: int = 3,
    percentual_tolerancia_valor: Decimal = Decimal("0.05"),  # 5% de tolerância para juros/tarifas
    valor_maximo_tolerancia_abs: Decimal = Decimal("50.00")  # Teto absoluto em R$ (ex: até R$ 50 de diferença)
) -> List[MatchResult]:
    
    results: List[MatchResult] = []
    movimentacoes_utilizadas = set()
    titulos_utilizados = set()

    for tx in ofx_transactions:
        # 1. Checagem de Idempotência
        if tx.fitid in fitids_conciliados:
            results.append(
                MatchResult(
                    ofx_tx=tx,
                    confidence=MatchConfidence.DUPLICATE,
                    score=0,
                    reason="Transação (FITID) já conciliada anteriormente."
                )
            )
            continue

        best_result = None
        highest_score = 0
        matched_mov_id = None
        matched_tit_id = None
        val_orig = None
        juros_calc = Decimal("0.00")
        desconto_calc = Decimal("0.00")
        match_reason = "Nenhuma correspondência encontrada."

        # 2. Busca em Movimentações de Conta (Extrato Interno) - Exige Valor Exato
        for mov in movimentacoes_pendentes:
            if mov['id'] in movimentacoes_utilizadas:
                continue

            if mov['tipo'] != tx.trntype or mov['valor'] != tx.amount:
                continue

            dias_diff = abs((tx.dtposted - mov['data_movimento']).days)

            if dias_diff == 0:
                highest_score = 100
                matched_mov_id = mov['id']
                match_reason = "Correspondência exata de data, valor e tipo na movimentação."
                break
            elif dias_diff <= dias_tolerancia:
                score = 90 - (dias_diff * 5)
                if score > highest_score:
                    highest_score = score
                    matched_mov_id = mov['id']
                    match_reason = f"Correspondência flexível na movimentação (Diferença de {dias_diff} dia(s))."

        # 3. Busca em Títulos Aberto (Aceita variação de valor por juros/tarifas/multa)
        if highest_score < 100:
            for tit in titulos_abertos:
                if tit['id'] in titulos_utilizados:
                    continue

                dias_diff = abs((tx.dtposted - tit['data_vencimento']).days)
                if dias_diff > dias_tolerancia:
                    continue

                valor_titulo = tit['valor_original']
                diferenca_valor = tx.amount - valor_titulo  # Positivo = Pago a mais (juros/multa), Negativo = Pago a menos (desconto/tarifa)
                abs_diferenca = abs(diferenca_valor)

                # Calcula o limite aceitável de divergência
                limite_tolerado = min(valor_titulo * percentual_tolerancia_valor, valor_maximo_tolerancia_abs)

                if abs_diferenca <= limite_tolerado:
                    # Cálculo da pontuação com base na diferença de dias e valor
                    score_data = 80 - (dias_diff * 5)
                    score_valor = 20 - int((abs_diferenca / limite_tolerado) * 15) if limite_tolerado > 0 else 20
                    total_score = score_data + score_valor

                    if total_score > highest_score:
                        highest_score = total_score
                        matched_mov_id = None
                        matched_tit_id = tit['id']
                        val_orig = valor_titulo
                        
                        if diferenca_valor > 0:
                            juros_calc = diferenca_valor
                            desconto_calc = Decimal("0.00")
                            detalhe_val = f"Diferença de +R$ {juros_calc:.2f} identificada como juros/multa."
                        elif diferenca_valor < 0:
                            juros_calc = Decimal("0.00")
                            desconto_calc = abs_diferenca
                            detalhe_val = f"Diferença de -R$ {desconto_calc:.2f} identificada como desconto/tarifa."
                        else:
                            juros_calc = Decimal("0.00")
                            desconto_calc = Decimal("0.00")
                            detalhe_val = "Valor exato do título."

                        match_reason = f"Título localizado. {detalhe_val} (Diferença de {dias_diff} dia(s))."

        # 4. Determinação do nível de confiança
        if highest_score == 100:
            confidence = MatchConfidence.EXACT
            movimentacoes_utilizadas.add(matched_mov_id)
        elif highest_score >= 70:
            confidence = MatchConfidence.EXACT_WITH_ADJUSTMENT if (juros_calc > 0 or desconto_calc > 0) else MatchConfidence.FLEX
            if matched_mov_id: movimentacoes_utilizadas.add(matched_mov_id)
            if matched_tit_id: titulos_utilizados.add(matched_tit_id)
        elif highest_score >= 50:
            confidence = MatchConfidence.FLEX
            if matched_tit_id: titulos_utilizados.add(matched_tit_id)
        else:
            confidence = MatchConfidence.NONE

        results.append(
            MatchResult(
                ofx_tx=tx,
                confidence=confidence,
                score=highest_score,
                matched_movimento_id=matched_mov_id,
                matched_titulo_id=matched_tit_id,
                valor_titulo_original=val_orig,
                valor_juros_multa=juros_calc,
                valor_desconto_tarifa=desconto_calc,
                reason=match_reason
            )
        )

    return results

```

---

### Demonstração do Funcionamento

No exemplo abaixo, uma conta de **R$ 1.000,00** foi paga com atraso no valor de **R$ 1.025,00** (R$ 25,00 de juros). O algoritmo detecta e separa o acréscimo automaticamente:

```python
# Título pendente no sistema
titulos_db = [
    {"id": 301, "data_vencimento": date(2026, 9, 10), "valor_original": Decimal("1000.00")}
]

# Extrato OFX com pagamento de R$ 1.025,00 (Título + Juros/Multa)
sample_ofx = """
OFXHEADER:100
DATA:OFXSGML
<OFX>
  <BANKMSGSRSV1>
    <STMTTRNRS>
      <STMTRS>
        <BANKTRANLIST>
          <STMTTRN>
            <TRNTYPE>DEBIT</TRNTYPE>
            <DTPOSTED>20260912120000</DTPOSTED>
            <TRNAMT>-1025.00</TRNAMT>
            <FITID>FITID-JUROS-001</FITID>
            <MEMO>PAGTO TITULO C/ JUROS</MEMO>
          </STMTTRN>
        </BANKTRANLIST>
      </STMTRS>
    </STMTTRNRS>
  </BANKMSGSRSV1>
</OFX>
"""

# Execução
transacoes = parse_ofx(StringIO(sample_ofx))
resultados = match_transactions(
    ofx_transactions=transacoes,
    conta_id=1,
    fitids_conciliados=set(),
    movimentacoes_pendentes=[],
    titulos_abertos=titulos_db
)

res = resultados[0]
print(f"Status: {res.confidence.value} | Score: {res.score}")
print(f"Ofx Valor: R$ {res.ofx_tx.amount} | Título Original: R$ {res.valor_titulo_original}")
print(f"Juros/Multa: R$ {res.valor_juros_multa} | Desconto/Tarifa: R$ {res.valor_desconto_tarifa}")
print(f"Detalhe: {res.reason}")

```

---

### Como Efetivar a Baixa no Banco de Dados

Ao confirmar a conciliação marcada com `ALTA_COM_AJUSTE`, o backend deve executar a baixa atualizando os campos de ajuste do título e gerando a movimentação de conta pelo valor total do extrato:

```sql
-- 1. Atualiza o título quitado gravando os juros e o valor total pago (R$ 1.025,00)
UPDATE titulos_pagar 
SET status = 'PAGO',
    data_pagamento = '2026-09-12',
    valor_juros_multa = 25.00,
    valor_pago = 1025.00
WHERE id = 301;

-- 2. Insere a movimentação de saída na conta bancária pelo valor real debitado no banco
INSERT INTO movimentacoes_conta (id_conta_bancaria, id_titulo_pagar, data_movimento, tipo, valor, descricao, conciliado)
VALUES (1, 301, '2026-09-12', 'SAIDA', 1025.00, 'PAGTO TITULO C/ JUROS', TRUE);

-- 3. Registra a conciliação com o FITID para evitar duplicidades
INSERT INTO conciliacoes (id_movimento_conta, data_extrato, fitid_ofx, descricao_extrato, valor_extrato)
VALUES (LASTVAL(), '2026-09-12', 'FITID-JUROS-001', 'PAGTO TITULO C/ JUROS', 1025.00);

```

## TODO: Modelar o fluxo de conciliação para pagamentos parciais de títulos

## TODO: Escrever a API FastAPI/Flask para recepcionar o OFX e retornar o JSON para a interface

Como deve ser tratado o algoritmo de matching quando o valor no OFX representa um pagamento parcial de um título de valor maior?

O tratamento de **pagamentos parciais** no algoritmo de *matching* exige que o sistema reconheça a quitação de uma fração de um débito sem liquidar o título por completo.

Quando o valor do débito no extrato OFX for **menor** que o valor do `titulos_pagar`, a lógica deve permitir amortizar o saldo e manter a pendência da diferença.

---

### Lógica de Identificação e *Scoring* do Matching Parcial

Para evitar falsos positivos com pagamentos parciais acidentais, a busca de candidatos no banco de dados deve seguir regras específicas de avaliação:

1. **Critério de Elegibilidade:**
* `ofx.tipo == 'SAIDA'`
* `ofx.valor < titulo.valor_em_aberto` *(Onde `valor_em_aberto = valor_original - valor_pago + juros - descontos`)*
* `abs(ofx.data - titulo.data_vencimento) <= janela_dias` *(Ex: até 5 dias de tolerância)*


2. **Regra de Priorização do Matching:**
* **Score Alto (Aproximadamente 85):** Se o valor no OFX corresponder exatamente a uma fração padrão do título (ex: exatamente **50%** do valor original, representando uma parcela combinada) ou se o campo `<MEMO>` do OFX contiver termos como *"Parc"*, *"Amort"*, ou o número do documento.
* **Score Médio (60 a 70):** Se o valor no OFX for qualquer valor inferior ao título dentro da janela de vencimento. Classifica-se como **Sugestão de Pagamento Parcial** para validação manual do usuário.



---

### Atualização no Módulo Python (`ofx_matcher`)

Adiciona-se o suporte ao estado de quitação parcial na avaliação dos títulos:

```python
# Trecho a ser adicionado dentro do loop de busca em titulos_abertos:

valor_em_aberto = tit['valor_original'] - tit.get('valor_pago', Decimal('0.00'))

# Verifica se o lançamento do OFX é um pagamento menor que o saldo devedor
if tx.amount < valor_em_aberto:
    dias_diff = abs((tx.dtposted - tit['data_vencimento']).days)
    
    if dias_diff <= dias_tolerancia:
        # Verifica se o valor bate com uma fração comum (ex: 50% do título)
        e_fracao_exata = (valor_em_aberto % tx.amount == 0) or (abs((valor_em_aberto / 2) - tx.amount) < Decimal('0.01'))
        
        base_score = 75 if e_fracao_exata else 60
        score = base_score - (dias_diff * 5)
        
        if score > highest_score:
            highest_score = score
            matched_tit_id = tit['id']
            is_parcial = True
            valor_remanescente = valor_em_aberto - tx.amount
            
            match_reason = (
                f"Amortização parcial detectada: R$ {tx.amount} debitados de um saldo "
                f"de R$ {valor_em_aberto}. Restará R$ {valor_remanescente} em aberto."
            )

```

---

### Fluxo de Baixa no Banco de Dados ao Confirmar a Parcial

Quando o usuário confirma o vínculo da transação parcial, as operações no banco devem ser executadas dentro de uma **transação SQL atômica**:

```sql
BEGIN;

-- 1. Registra a saída real da conta bancária (pelo valor parcial do OFX)
INSERT INTO movimentacoes_conta (
    id_conta_bancaria, 
    id_titulo_pagar, 
    data_movimento, 
    tipo, 
    valor, 
    descricao, 
    conciliado
) VALUES (
    1, 
    102, -- ID do título
    '2026-09-10', 
    'SAIDA', 
    500.00, -- Valor amortizado do OFX
    'PAGAMENTO PARCIAL - VIA CONCILIACAO OFX', 
    TRUE
);

-- 2. Amortiza o título a pagar e altera seu status para PARCIAL
UPDATE titulos_pagar 
SET valor_pago = valor_pago + 500.00,
    status = CASE 
        WHEN (valor_original - valor_desconto + valor_juros_multa) - (valor_pago + 500.00) <= 0 THEN 'PAGO'
        ELSE 'PARCIAL'
    END
WHERE id = 102;

-- 3. Grava o FITID para evitar duplo reprocessamento
INSERT INTO conciliacoes (
    id_movimento_conta, 
    data_extrato, 
    fitid_ofx, 
    descricao_extrato, 
    valor_extrato
) VALUES (
    LASTVAL(), 
    '2026-09-10', 
    'FITID-PARCIAL-991', 
    'PAGTO PARCIAL FORNECEDOR', 
    500.00
);

COMMIT;

```

---

### Diretrizes de Interface e Experiência do Usuário (UX)

* **Indicador Visual Claro:** Transações identificadas como pagamentos parciais devem exibir uma tag visual como `<PAGAMENTO PARCIAL>` na tela de conciliação, destacando o valor que continuará pendente no título.
* **Ajuste de Vencimento:** Ao confirmar a parcial, o sistema deve oferecer uma opção rápida para redefinir a data de vencimento do saldo restante (ex: *"Deseja postergar os R$ 500,00 restantes para o próximo mês?"*).
* **Múltiplos Vínculos:** Permita que o histórico de um mesmo `titulos_pagar` contenha vários registros vinculados na tabela `movimentacoes_conta`, permitindo rastrear cada amortização individualmente até a quitação final.


---

## TODO: Modelar o fluxo de conciliação para pagamentos agrupados (1 débito OFX para N títulos)

---

## Escrever a API FastAPI para listar e confirmar os correspondentes do OFX

Escreva uma API REST em FastAPI completa com o endpoint de upload do OFX e o endpoint de confirmação de baixa (incluindo baixas parciais e com juros).

Esta é a implementação completa da API REST em **FastAPI** para processamento de extrato OFX e confirmação de conciliação (com suporte a quitação integral, juros/multas, descontos e pagamentos parciais).

O código utiliza **SQLAlchemy 2.0 (Async)** e **Pydantic v2** para garantir performance e validação estrita dos dados.

---

### 1. Schemas de Entrada e Saída (`schemas.py`)

```python
from decimal import Decimal
from datetime import date
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class MatchConfidence(str, Enum):
    EXACT = "ALTA_CONFIANCA"
    EXACT_WITH_ADJUSTMENT = "ALTA_COM_AJUSTE"
    FLEX = "MEDIA_CONFIANCA"
    NONE = "SEM_MATCH"
    DUPLICATE = "JA_CONCILIADO"

class OFXTransactionSchema(BaseModel):
    fitid: str
    trntype: str
    dtposted: date
    amount: Decimal
    memo: str

class MatchResultResponse(BaseModel):
    ofx_tx: OFXTransactionSchema
    confidence: MatchConfidence
    score: int
    matched_movimento_id: Optional[int] = None
    matched_titulo_id: Optional[int] = None
    valor_titulo_original: Optional[Decimal] = None
    valor_juros_multa: Decimal = Decimal("0.00")
    valor_desconto_tarifa: Decimal = Decimal("0.00")
    reason: str

class ParseOFXResponse(BaseModel):
    conta_bancaria_id: int
    total_transacoes: int
    resultados: List[MatchResultResponse]

# Schema para o Payload do Endpoint de Confirmação
class ConfirmacaoConciliacaoRequest(BaseModel):
    id_conta_bancaria: int
    fitid_ofx: str
    data_extrato: date
    descricao_extrato: str
    valor_extrato: Decimal = Field(gt=0, description="Valor absoluto do movimento no banco")
    
    # Vínculo opcional se já existir uma movimentação
    id_movimento_conta: Optional[int] = None 
    
    # Vínculo com Título a Pagar
    id_titulo_pagar: Optional[int] = None
    valor_juros_multa: Decimal = Decimal("0.00")
    valor_desconto: Decimal = Decimal("0.00")
    
    # Ajuste de vencimento caso seja parcial
    nova_data_vencimento_saldo: Optional[date] = None

class ConfirmacaoResponse(BaseModel):
    sucesso: bool
    mensagem: str
    id_movimento_conta: int
    id_conciliacao: int
    id_titulo_pagar: Optional[int] = None
    status_titulo: Optional[str] = None
    saldo_remanescente_titulo: Optional[Decimal] = None

```

---

### 2. Endpoints FastAPI e Lógica de Negócio (`main.py`)

```python
from io import BytesIO
from decimal import Decimal
from typing import List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

# Importações dos seus modelos SQLAlchemy e do módulo matcher ajustado anteriormente
from database import get_db_session  # Dependência da sessão async do banco
from models import TitulosPagar, MovimentacoesConta, Conciliacoes, ContasBancarias
from ofx_matcher_v2 import parse_ofx, match_transactions
from schemas import (
    ParseOFXResponse, 
    ConfirmacaoConciliacaoRequest, 
    ConfirmacaoResponse
)

app = FastAPI(
    title="API de Conciliação Bancária & Contas a Pagar",
    version="1.0.0"
)

# --------------------------------------------------------------------------
# ENDPOINT 1: Upload e Parsing de Arquivo OFX + Algoritmo de Matching
# --------------------------------------------------------------------------
@app.post(
    "/api/v1/conciliacao/upload-ofx", 
    response_model=ParseOFXResponse,
    summary="Processa arquivo OFX e sugere correspondências"
)
async def upload_ofx(
    id_conta_bancaria: int = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session)
):
    if not file.filename.lower().endswith(".ofx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Arquivo inválido. O arquivo deve ter a extensão .ofx"
        )
    
    # 1. Valida existência da conta bancária
    query_conta = await db.execute(select(ContasBancarias).where(ContasBancarias.id == id_conta_bancaria))
    if not query_conta.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Conta bancária não encontrada.")

    # 2. Leitura do arquivo OFX
    contents = await file.read()
    try:
        transacoes_ofx = parse_ofx(BytesIO(contents))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail=f"Falha ao ler arquivo OFX: {str(e)}"
        )

    # 3. Carrega dados do banco para o algoritmo de matching
    # A) FITIDs já conciliados nesta conta
    query_fitids = await db.execute(
        select(Conciliacoes.fitid_ofx)
        join(MovimentacoesConta, Conciliacoes.id_movimento_conta == MovimentacoesConta.id)
        where(MovimentacoesConta.id_conta_bancaria == id_conta_bancaria)
    )
    fitids_conciliados = set(query_fitids.scalars().all())

    # B) Movimentações internas pendentes de conciliação
    query_movs = await db.execute(
        select(MovimentacoesConta).where(
            MovimentacoesConta.id_conta_bancaria == id_conta_bancaria,
            MovimentacoesConta.conciliado == False
        )
    )
    movs_pendentes = [
        {"id": m.id, "data_movimento": m.data_movimento, "tipo": m.tipo, "valor": m.valor}
        for m in query_movs.scalars().all()
    ]

    # C) Títulos a pagar em aberto
    query_titulos = await db.execute(
        select(TitulosPagar).where(TitulosPagar.status.in_(["PENDENTE", "PARCIAL"]))
    )
    titulos_abertos = [
        {
            "id": t.id, 
            "data_vencimento": t.data_vencimento, 
            "valor_original": t.valor_original,
            "valor_pago": t.valor_pago
        }
        for t in query_titulos.scalars().all()
    ]

    # 4. Executa a engine de matching
    resultados_matching = match_transactions(
        ofx_transactions=transacoes_ofx,
        conta_id=id_conta_bancaria,
        fitids_conciliados=fitids_conciliados,
        movimentacoes_pendentes=movs_pendentes,
        titulos_abertos=titulos_abertos
    )

    return ParseOFXResponse(
        conta_bancaria_id=id_conta_bancaria,
        total_transacoes=len(transacoes_ofx),
        resultados=resultados_matching
    )


# --------------------------------------------------------------------------
# ENDPOINT 2: Confirmação da Conciliação / Baixa (Parcial, Juros ou Integral)
# --------------------------------------------------------------------------
@app.post(
    "/api/v1/conciliacao/confirmar", 
    response_model=ConfirmacaoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Confirma o vínculo, gera a movimentação e efetua a baixa do título"
)
async def confirmar_conciliacao(
    payload: ConfirmacaoConciliacaoRequest,
    db: AsyncSession = Depends(get_db_session)
):
    async with db.begin():  # Inicia transação atômica (commit automático ao final)
        
        # 1. Verifica se o FITID já foi processado (evita duplicidade)
        query_fitid = await db.execute(
            select(Conciliacoes.id).where(Conciliacoes.fitid_ofx == payload.fitid_ofx)
        )
        if query_fitid.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Esta transação (FITID) já foi conciliada anteriormente."
            )

        movimento_id = payload.id_movimento_conta
        status_titulo_final = None
        saldo_remanescente = None

        # 2. Processa a liquidação do Título (se associado)
        if payload.id_titulo_pagar:
            query_tit = await db.execute(
                select(TitulosPagar)
                .where(TitulosPagar.id == payload.id_titulo_pagar)
                .with_for_update()  # Lock pessimista para concorrência
            )
            titulo = query_tit.scalar_one_or_none()
            
            if not titulo:
                raise HTTPException(status_code=404, detail="Título a pagar não encontrado.")

            # Atualiza valores de juros e descontos acumulados
            titulo.valor_juros_multa += payload.valor_juros_multa
            titulo.valor_desconto += payload.valor_desconto
            
            # Novo valor pago acumulado
            titulo.valor_pago += payload.valor_extrato
            titulo.data_pagamento = payload.data_extrato

            # Calcula total líquido devido do título
            total_devido = (titulo.valor_original - titulo.valor_desconto + titulo.valor_juros_multa)
            saldo_remanescente = total_devido - titulo.valor_pago

            # Define o novo status do título
            if saldo_remanescente <= Decimal("0.00"):
                titulo.status = "PAGO"
                saldo_remanescente = Decimal("0.00")
            else:
                titulo.status = "PARCIAL"
                if payload.nova_data_vencimento_saldo:
                    titulo.data_vencimento = payload.nova_data_vencimento_saldo

            status_titulo_final = titulo.status

        # 3. Cria a movimentação bancária (caso não existia uma movimentação manual prévia)
        if not movimento_id:
            nova_movimentacao = MovimentacoesConta(
                id_conta_bancaria=payload.id_conta_bancaria,
                id_titulo_pagar=payload.id_titulo_pagar,
                data_movimento=payload.data_extrato,
                tipo="SAIDA",  # Contas a pagar é saída
                valor=payload.valor_extrato,
                descricao=f"{payload.descricao_extrato} (OFX)",
                conciliado=True
            )
            db.add(nova_movimentacao)
            await db.flush()  # Gera o ID da movimentação
            movimento_id = nova_movimentacao.id
        else:
            # Se já existia uma movimentação não conciliada, apenas marca como conciliada
            await db.execute(
                update(MovimentacoesConta)
                .where(MovimentacoesConta.id == movimento_id)
                .values(conciliado=True)
            )

        # 4. Registra a Conciliação gravando o FITID do banco
        nova_conciliacao = Conciliacoes(
            id_movimento_conta=movimento_id,
            data_extrato=payload.data_extrato,
            fitid_ofx=payload.fitid_ofx,
            descricao_extrato=payload.descricao_extrato,
            valor_extrato=payload.valor_extrato
        )
        db.add(nova_conciliacao)
        await db.flush()

    return ConfirmacaoResponse(
        sucesso=True,
        mensagem="Conciliação e baixa efetuadas com sucesso.",
        id_movimento_conta=movimento_id,
        id_conciliacao=nova_conciliacao.id,
        id_titulo_pagar=payload.id_titulo_pagar,
        status_titulo=status_titulo_final,
        saldo_remanescente_titulo=saldo_remanescente
    )

```

---

### Exemplo de Payload para o Endpoint de Confirmação

#### Exemplo A: Baixa com Juros (Débito de R$ 1.025,00 para Título de R$ 1.000,00)

```json
POST /api/v1/conciliacao/confirmar
{
  "id_conta_bancaria": 1,
  "fitid_ofx": "20260910-341-00123",
  "data_extrato": "2026-09-10",
  "descricao_extrato": "PAGTO BOLETO FORNECEDOR",
  "valor_extrato": 1025.00,
  "id_titulo_pagar": 45,
  "valor_juros_multa": 25.00,
  "valor_desconto": 0.00
}

```

#### Exemplo B: Pagamento Parcial (Débito de R$ 300,00 para Título de R$ 1.000,00)

```json
POST /api/v1/conciliacao/confirmar
{
  "id_conta_bancaria": 1,
  "fitid_ofx": "20260910-341-00124",
  "data_extrato": "2026-09-10",
  "descricao_extrato": "PIX PARCIAL FORNECEDOR",
  "valor_extrato": 300.00,
  "id_titulo_pagar": 46,
  "valor_juros_multa": 0.00,
  "valor_desconto": 0.00,
  "nova_data_vencimento_saldo": "2026-09-25"
}

```

---

### Recursos de Segurança e Concorrência

* **Transação Atômica (`async with db.begin()`):** Se houver falha ao inserir a conciliação ou atualizar o título, nenhuma movimentação é persistida no banco.
* **Bloqueio Pessimista (`with_for_update()`):** Garante que duas requisições simultâneas confirmando baixas para o mesmo `TitulosPagar` não causem concorrência ou cálculo incorreto do saldo remanescente.
* **Validação Estrita:** Garante que pagamentos parciais alterem o status para `PARCIAL` e calculem a diferença restante sem zerar a obrigação do contas a pagar.




