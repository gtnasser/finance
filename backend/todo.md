
📋 Lista de alterações (plano de ação)🔴 Crítico — segurança e correção
- [X] security.py — remover SECRET_KEY hardcoded; ler de configuração via pydantic-settings.
- [X] security.py — adicionar política de senha: min_length e max_length (bcrypt tem limite de 72 bytes).
- [ ] auth.py — proteger /register: fechar em produção ou restringir a admin.
- [ ] auth.py — adicionar rate limiting no /token (proteção contra força bruta).
- [ ] auth.py — padronizar usuário inativo como 401 (hoje devolve 400 no login e 401 no get_current_user).
- [ ] logger.py — diagnose=False e backtrace=False em produção (evita gravar senhas em log).
- [ ] contas.py — reescrever com autenticação real (get_current_user), sem o mock verificar_token.

🟠 Arquitetura
- [X] Criar config.py — pydantic-settings centralizando SECRET_KEY, DATABASE_URL e ambiente (dev/prod).
- [X] Criar camada services/ — onde vivem as regras financeiras multi-tabela (baixa, transferência, conciliação). Hoje não existe.
- [X] database.py — ler DATABASE_URL do config; adicionar pool_pre_ping para Postgres; remover future=True (inócuo no 2.0).
- [X] contas.py — mover schemas para schemas.py; Decimal no lugar de float; endpoints async; UUID completo (sem truncar para 8 chars).
- [X] main.py — incluir routers reais; seed condicionado por ambiente (nunca admin123 em produção).

🟡 Modelagem
- [X] Criar PlanoContas — hierárquico (parent_id), tipo, natureza, codigo único, distinção sintética vs analítica.
- [X] Criar ContaCorrente — FK para conta analítica do plano, unique em (banco, agencia, numero), saldo_inicial em Decimal.
- [X] Todos os modelos — adicionar updated_at (hoje só existe created_at).
- [X] Usuario.ativo — usar server_default (default do lado Python não cobre inserts via SQL direto).
- [X] __table_args__ — declarar UniqueConstraints explícitos.

🟢 Ambiente e dependências
- [X] requirements.txt — adicionar asyncpg, alembic, pydantic-settings; usar sqlalchemy[asyncio].
- [ ] Separar requirements por ambiente — base.txt, dev.txt, prod.txt (ou documentar claramente).
- [X] .env.example — completar com todas as variáveis necessárias.
- [X] Configurar Alembic — migrações versionadas no lugar de create_all puro.

📄 Documentação
- [X] Reescrever README — entregue abaixo.
- [X] Seção "Configuração de Produção" — guia no README (entregue abaixo).

❓ Decisões em aberto (precisam ser fechadas antes da modelagem)
- [X] Multi-usuário: todos compartilham a base financeira (sem FK usuario_id + filtro de visibilidade).
- [X] Plano de contas: hierarquia sintetica + analítica, com controle de natureza (devedora/credora).
