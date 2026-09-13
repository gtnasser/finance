# FINANCING

Objetivo: desenvolver um app simples de **Contas a Pagar/Gestão Financeira**

### 📋 Requisitos funcionais
- agendar os pagamentos
- classificar conforme um plano de contas
- indicar de qual conta corrente será pago
- emitir uma lista de titulos em aberto
- emitir um extrato por conta corrente
- registrar transferencias entre contas
- permitir fazer conciliação do que foi pago 

### ⚙️ Requisitos não funcionais
- devera ser desenvolvido em python
- front-end e back-end isolados 
- transações executadas no backend via API
- armazenamento em banco de dados relacional remoto (SQLite em dev local, Postgres remoto em em prod)
- autenticacao de usuario atraves de login simples
- dimensionar para: 100 transações/dia, 4 usuários simultâneos
- registro das atividades em log estilo LOGCAT

--- 

## 🚀 Escopo e Funcionalidades

> **Nota sobre o estado atual do projeto:**
> As funcionalidades listadas abaixo representam a visão completa do produto e serão desenvolvidas gradualmente. O foco inicial da **Fase 1 (MVP)** é a entrega da fundação do sistema: arquitetura desacoplada, autenticação segura (OAuth2/JWT), persistência assíncrona e navegação base.

### 1. Gestão e Agendamento de Títulos

* **Cadastro de Contas a Pagar:** Registro de lançamentos com data de emissão, data de vencimento, valor, fornecedor/favorecido, número do documento/nota e descrição.
* **Agendamento de Pagamentos:** Programação de pagamentos futuros (únicos, recorrentes ou parcelados) com alertas ou notificações de vencimentos próximos e contas em atraso.
* **Anexo de Comprovantes/Documentos:** Opção de anexar boletos, PDFs ou fotos de recibos diretamente ao lançamento.

### 2. Classificação Financeira (Plano de Contas)

* **Estruturação por Categorias e Subcategorias:** Organização das despesas conforme o plano de contas (ex.: *Despesas Operacionais > Aluguel*, *Fornecedores > Matéria-Prima*, *Pessoal > Salários*).
* **Atribuição de Centro de Custos:** Identificação de qual departamento, projeto ou unidade do negócio gerou a despesa.

### 3. Gestão de Contas Bancárias e Transferências

* **Seleção de Conta Origem:** Indicação explícita da conta corrente, conta digital, caixa físico ou cartão de crédito de onde sairá o recurso para a quitação.
* **Transferências entre Contas (TED/Pix/Interna):** Registro de movimentações entre contas próprias da empresa/usuário, garantindo a atualização exata dos saldos sem duplicar receitas ou despesas no DRE/relatórios.

### 4. Controle e Conciliação Financeira

* **Baixa de Pagamentos:** Registro da data efetiva do pagamento, valor pago (aplicando juros, multas ou descontos) e meio utilizado (Pix, boleto, cartão, débito automático).
* **Conciliação Bancária:**
* **Manual:** Mapeamento e marcação individual dos lançamentos do app em relação ao extrato bancário.
* **Importação (OFX/CSV):** Leitura de arquivo de extrato do banco com cruzamento automático (matching) entre o extrato e os títulos quitados no app.

### 5. Relatórios e Extratos

* **Relatório de Contas em Aberto:** Listagem detalhada de obrigações a vencer e vencidas (aging list), filtrável por período, fornecedor ou categoria.
* **Extrato por Conta Corrente:** Histórico de entradas, saídas, transferências e saldo acumulado linha a linha de uma conta específica em um determinado período.
* **Fluxo de Caixa Projetado:** Visão consolidada das saídas previstas versus entradas (caso integrado ao Contas a Receber) para evitar saldo negativo nas contas.


---


## 🔄 Principais Regras de Negócio e Relacionamentos

| Funcionalidade | Implementação na Modelagem |
| --- | --- |
| **Baixa de Título** | Ao pagar um `titulos_pagar`, cria-se um registro de `SAIDA` em `movimentacoes_conta` associado ao `id_titulo_pagar`. |
| **Transferência entre Contas** | Cria **dois** registros em `movimentacoes_conta` (uma `SAIDA` na origem e uma `ENTRADA` no destino) unidos por um registro único na tabela `transferencias`. |
| **Extrato da Conta** | É obtido diretamente ordenando a tabela `movimentacoes_conta` por `data_movimento` para a conta informada. O saldo atual é o `saldo_inicial` da conta mais a soma de `ENTRADA` menos `SAIDA`. |
| **Conciliação** | Grava o vínculo da movimentação com o registro vindo do arquivo OFX/CSV (usando `fitid_ofx` para evitar duplicidades) e marca `conciliado = TRUE` no movimento. |


-----

## ARQUITETURA

O projeto adota uma arquitetura **MVP (Minimum Viable Product)** robusta, bem estruturada e desacoplada em três camadas principais: **Streamlit (Frontend) → FastAPI (Backend) → Relational DB (Database)**.

### 🏛️ Pilares da Arquitetura

- **Decoupled MVP (Separação de Responsabilidades):** Em vez de construir uma aplicação monolítica onde o banco de dados é acessado diretamente pelas telas, o frontend e o backend são totalmente independentes. A lógica de negócios e as regras financeiras residem 100% na API RESTful, permitindo reutilizar o backend no futuro para outras interfaces (como React, Vue ou aplicativos móveis).
- **Persistência Escalável sem Refatoração:** Com a adoção do **SQLAlchemy 2.0 Async**, o ambiente de desenvolvimento utiliza **SQLite** (`contas_pagar.db`) para agilidade e simplicidade de testes locais. A transição para um banco relacional robusto em produção (como **PostgreSQL** ou **MySQL**) exige apenas a alteração da string de conexão (`DATABASE_URL`), sem necessidade de reescrever a camada de regras de negócio.
- **Segurança Profissional desde o Dia 1:** O sistema adota padrões modernos de autenticação baseados em **OAuth2 Password Flow** com tokens **JWT** e hashing defensivo de senhas via **`pwdlib[bcrypt]`**, garantindo proteção contra vulnerabilidades básicas de segurança em um ecossistema financeiro.


### 💻 Camada de Frontend (`frontend/`)

- **Abstração HTTP (`api_client.py`):** Atua como a camada de serviço de rede no frontend, isolando as views do Streamlit de detalhes de infraestrutura HTTP. Ele encapsula a biblioteca `httpx`, gerencia a URL base da API, realiza o tratamento centralizado de exceções de conexão e injeta automaticamente o cabeçalho de autenticação (`Authorization: Bearer <token>`) em todas as requisições autenticadas.


### ⚙️ Camada de Backend (`backend/`)

- **Autenticação e Autorização (`routers/auth.py` & `security.py`):** O backend é o único responsável por validar credenciais, emitir e verificar tokens JWT (assinados assincronamente com chave secreta) e gerenciar o ciclo de vida da sessão do usuário.
- **Camada de persistência:** Adotado o **SQLAlchemy 2.0 Async** para gerenciar um banco relacional SQL, mapeamentos relacionais usando **ORM Models**, e scripts para **configuração da sessão/Engine**, **carga inicial (*Seed*)** com valores padrão e adicional para testes.
- **Desacoplamento de Persistência e Integração (`models.py` vs `schemas.py`):**
  - **`models.py` (SQLAlchemy):** Define o mapeamento objeto-relacional (ORM) e a estrutura física das tabelas no banco de dados.
  - **`schemas.py` (Pydantic v2):** Define os contratos da API, realizando a validação estrita de entrada (payloads), a serialização de saída e a sanitização de dados sensíveis (impedindo a exposição de campos como `senha_hash`).
  - Essa divisão garante contratos flexíveis de criação, atualização e leitura de dados sem acoplar a interface ao esquema estrutural do banco de dados.
- **Registro de Atividades em log:**
  - Rastreabilidade sem poluição: utiliza um padrão profissional de log com rotação e retenção customizáveis, e possibilidade de ativar/desativar/alterar nivel de registro em tempo de execução.
  - Auditoria de Operações Financeiras: Registra ações críticas (ex: criação de títulos, alteração de saldos, tentativas de login) com carimbo de data/hora (timestamp).
  - Diagnóstico em Produção: Quando em produção, pode ser lido por outras ferramentas para identificação de falhas e geração de estatísticas.


### 📂 Estrutura de Diretórios Atual

```text
financing/
├── .gitignore            # Ignora venv, *.db, .env, caches
├── .env.example          # Modelo de variáveis de ambiente (SECRET_KEY, DATABASE_URL)
├── requirements.txt      # Dependências do projeto (FastAPI, Streamlit, SQLAlchemy, etc.)
├── backend/
│   ├── database.py       # Engine e AsyncSessionLocal (SQLAlchemy 2.0)
│   ├── logs/             # Logs exclusivos da API FastAPI
│   │   └── api.log
│   ├── logger.py         # Configuração de log do backend
│   ├── models.py         # Modelos relacionais ORM (Usuario, PlanoContas, TitulosPagar, etc.)
│   ├── schemas.py        # Validações Pydantic (Token, Request/Response, etc.)
│   ├── security.py       # Gerenciamento de JWT e validação de hash pwdlib
│   ├── main.py           # FastAPI lifespan, rotas principais, seed automático
│   └── routers/
│       └── auth.py       # Endpoints /auth/token e /auth/me
└── frontend/
    ├── app.py            # Ponto de entrada Streamlit com st.navigation
    ├── api_client.py     # Cliente HTTPX com injeção de Bearer Token
    ├── logs/             # Logs exclusivos da interface Streamlit
    │   └── ui.log
    ├── logger.py         # Configuração de log do frontend
    └── views/
        ├── login.py      # Tela de autenticação
        ├── dashboard.py  # Visão geral de métricas
        └── titulos.py    # Gestão de Contas a Pagar (CRUD)
```


financing/
├── backend/
│   └── main.py
│
└── frontend/
    └── app.py


-----


## TO RUN

```bash
# Na raiz do projeto (financing/)
python -m venv venv
.\venv\Scripts\Activate.ps1
# source venv/bin/activate

# Instale os pacotes necessários
pip install fastapi "uvicorn[standard]" sqlalchemy aiosqlite pydantic pyjwt "passlib[bcrypt]" python-multipart httpx streamlit pedlib pydantic[email] loguru
#pip install -r frontend/requirements.txt
#pip install -r backend/requirements.txt
```

backend - terminal 1: Navegue até a pasta do backend ou rode via caminho relativo
- será criado o banco SQLite local (contas_pagar.db)
- será criado um usuário inicial admin@admin.com com a senha admin123
- testar a documentação interativa da API em: http://localhost:8000/docs
```bash
cd backend
uvicorn main:app --reload --port 8000
```

frontend - terminal2: Navegue até a pasta do frontend e execute ou indique o app
```bash
cd frontend
streamlit run app.py
# streamlit run frontend/app.py
```

Testando o Fluxo Completo
- Acessar o Streamlit: O navegador abrirá automaticamente em http://localhost:8501
- Realizar o Login: Informe as credenciais iniciais (admin@admin.com/admin123)
- Autenticação e Navegação: O cliente HTTP solicitará o token JWT ao backend, salvará o cabeçalho no st.session_state e redirecionará para o Dashboard


