## Como os módulos se relacionam (visão resumida)

O fluxo segue a **direção da requisição HTTP para o banco**, sempre em camadas. Cada camada chama apenas a imediatamente inferior:

**1. HTTP (routers + main)** — os endpoints são "finos": recebem a requisição, autenticam via `get_current_user` (do `dependencies.py`), validam o payload com os schemas e delegam toda a lógica ao serviço. O `main.py` registra os routers, o CORS e os handlers que convertem as exceções de domínio em respostas HTTP (404/409/422).

**2. Serviços (regras de negócio)** — aqui moram as regras: ciclo na hierarquia, vínculo plano↔conta corrente, duplicidade, exclusão protegida. O serviço **controla a transação** (commit/rollback) e lança as exceções de `exceptions.py` quando uma regra é violada.

**3. Repositórios (acesso a dados)** — fazem a leitura/gravação no banco, filtram o soft delete automaticamente e dão `flush`. Uma regra importante: **regra de negócio nunca fica no repositório** — ele só sabe persistir.

**4. Models + Schemas (o "contrato" do dado)** — `models.py` é o ORM: define como o dado é armazenado (tabelas). `schemas.py` (Pydantic) é o contrato de entrada/saída: valida o que chega e serializa o que sai — e é o elo que você citou: o endpoint valida com o schema, o repositório persiste pelo model, e a resposta sai serializada de novo pelo schema.

```
Requisição → Router (valida com Schema) → Service (regras + transação) → Repository (SQL) → Model → Banco
Resposta   ← main.py (handlers)         ← Exception (se violou regra) ← Service
```

Vou montar o mapa mental com essa estrutura:

O mapa mostra a relação em camadas, mas o **insight mais importante de design** está na direção das dependências:

- **Cada camada só chama a imediatamente inferior.** O router nunca toca o repositório; o repositório nunca decide regra de negócio. É isso que permite trocar o banco (SQLite → Postgres) sem tocar nos serviços, e testar cada camada isoladamente (como fizemos nos 46 testes).
- **A transação é do serviço, não do repositório.** O repositório dá `flush` (manda os comandos), mas só o serviço faz `commit` — se uma regra falhar no meio, o rollback é garantido.
- **Schemas e Models são o "contrato duplo" do dado:** o Schema (Pydantic) valida o que entra e serializa o que sai; o Model (ORM) define como fica no banco. Um dado pode passar por schema → service → repository → model sem que nenhuma camada "reinterprete" o formato.
- **O fluxo de volta é via exceções:** o serviço lança `NotFoundError`/`ConflictError`/`BusinessRuleError` e o `main.py` converte em 404/409/422 — é por isso que o frontend recebe mensagens de erro consistentes.

**Resumindo**
- Fluxo: Router (valida com Schema) → Service (regras de negócio + commit) → Repository (soft delete + flush) → Model → Banco; o retorno de erro vem por exceções mapeadas no `main.py`.
- Services e repositories são separados de propósito: regra de negócio nunca mora no repositório, e a transação pertence ao serviço.
- Models definem armazenamento; Schemas definem contrato de entrada/saída — juntos, o "contrato duplo" de cada entidade.

Se quiser, posso:
- Gerar um mapa mental focado só no fluxo de uma operação concreta (ex.: criar uma conta corrente) mostrando cada módulo executado.
- Detalhar em texto como um `POST /api/v1/contas` cruza cada camada, linha a linha.