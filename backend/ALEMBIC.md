# ALEMBIC

## Primeira migração

Para gerar a primeira migração do zero, o fluxo é: gerar a migração inicial → revisar → aplicar → subir o backend.

Excluir o banco `contas_pagar.db`.

Pré-requisitos (se ainda não fez):
```bash
cd backend
pip install alembic
alembic init alembic
```

Depois do init:

- Substitua o `alembic/env.py` gerado pela versão assíncrona (a que lê `settings.DATABASE_URL` e importa `models`).
- Em seguida confira no `alembic.ini`:
  - `script_location = alembic` (relativo a `backend/`)
  - `sqlalchemy.url` vazio — o `env.py` preenche com a URL do `.env`

<details>
<summary>env.py versão assíncrona</summary>

```python
import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# Garante que o pacote backend/ esteja no path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import settings          # noqa: E402
from database import Base            # noqa: E402
import models                         # noqa: F401,E402  (registra as tabelas)

config = context.config
config.set_main_option("sqlalchemy.url", settings.

DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    context.configure(
        url=settings.

DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        # SQLite não suporta ALTER completo; batch mode contorna isso
        render_as_batch=connection.dialect.name == "sqlite",
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.

NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

</details>



## Passo 1 — Gerar a migração inicial

Com o banco vazio e os modelos importáveis:
```bash
alembic revision --autogenerate -m "esquema inicial"
```

O autogenerate compara o metadata dos modelos com o banco vazio e escreve `alembic/versions/xxxx_esquema_inicial.py`.

## Passo 2 — Revisar o arquivo gerado

Abra o arquivo e confira que ele contém `op.create_table` para as três tabelas:

- `usuarios`
- `plano_contas`
- `contas_correntes`

E que o `downgrade()` tem o `op.drop_table` correspondente.

**Migração vazia tem duas causas:**

1. O `import models` não está sendo enxergado (metadata vazio).
2. O banco já tem as tabelas criadas pelo `create_all` — o autogenerate compara e não acha diferença. Por isso o banco deve estar vazio antes da primeira geração.

## Passo 3 — Aplicar
```bash
alembic upgrade head
```

Isso cria as três tabelas + a tabela `alembic_version`, que registra a revisão atual.

O `init_db()` foi **removido do lifespan** — o schema agora é responsabilidade exclusiva do Alembic. O seed depende das tabelas existirem, por isso `alembic upgrade head` sempre vem antes do uvicorn.

## Passo 4 — Verificar e subir
```bash
alembic current
```

Deve mostrar a revisão `esquema inicial` como atual. Depois:
```bash
uvicorn main:app --reload --port 8000
```

## O que mudou e o que isso implica

- O schema vem exclusivamente do Alembic. A ordem correta de subida é: `alembic upgrade head` → `uvicorn main:app`.
- O seed roda só em dev (`if not settings.is_production`). Em produção, o plano de contas padrão pode ser carregado manualmente ou via um script — não no startup.
- Import novo no `main.py`: `from seed import seed_all` (cria **admin + plano de contas**) e `from loguru import logger` para o log do seed.
- Se você subir sem aplicar a migração, o seed vai falhar com "no such table: plano_contas" — é o comportamento esperado, e o erro deixa claro que falta o `alembic upgrade head`.

## Ordem de execução para testar
```bash
cd backend
alembic upgrade head          # cria as tabelas
uvicorn main:app --reload --port 8000   # roda o seed no startup
```

Para confirmar que o seed funcionou, consulte a API autenticado:
```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -d "username=admin@admin.com&password=admin123" \
  -H "Content-Type: application/x-www-form-urlencoded"
```

Depois use o token no `GET /api/v1/plano-contas` — deve retornar as **58 contas** do padrão.

## Comandos úteis de verificação
```bash
alembic current          # revisão atual aplicada
alembic history          # cadeia de revisões disponíveis
alembic downgrade -1     # desfaz a última migração aplicada
```
