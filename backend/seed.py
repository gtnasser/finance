from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models import PlanoContas, Usuario
from security import get_password_hash


# ---------- Usuario Inicial ----------

async def seed_admin(session: AsyncSession) -> bool:
    """Cria o usuário administrador inicial, se ainda não existir."""
    existe = await session.scalar(
        select(Usuario).where(Usuario.email == settings.ADMIN_EMAIL)
    )
    if existe:
        return False
    session.add(
        Usuario(
            nome=settings.ADMIN_NAME,
            email=settings.ADMIN_EMAIL,
            senha_hash=get_password_hash(settings.ADMIN_PASSWORD),
            ativo=True,
        )
    )
    await session.commit()
    return True

# ---------- Plano de Contas ----------

# Estrutura: (codigo, descricao, tipo, natureza, sintetica, parent_codigo)
# - sintetica=True  -> conta agrupadora
# - sintetica=False -> conta analítica (recebe lançamento)
PLANO_CONTAS_PADRAO = [
    # ----- ATIVO (natureza DEVEDORA) -----
    ("1", "Ativo", "ATIVO", "DEVEDORA", True, None),
    ("1.1", "Ativo Circulante", "ATIVO", "DEVEDORA", True, "1"),
    ("1.1.1", "Caixa e Equivalentes", "ATIVO", "DEVEDORA", True, "1.1"),
    ("1.1.1.1", "Caixa", "ATIVO", "DEVEDORA", False, "1.1.1"),
    ("1.1.1.2", "Conta Corrente", "ATIVO", "DEVEDORA", False, "1.1.1"),
    ("1.1.1.3", "Poupança", "ATIVO", "DEVEDORA", False, "1.1.1"),
    ("1.1.2", "Aplicações Financeiras", "ATIVO", "DEVEDORA", True, "1.1"),
    ("1.1.2.1", "Investimentos", "ATIVO", "DEVEDORA", False, "1.1.2"),
    ("1.2", "Ativo Não Circulante", "ATIVO", "DEVEDORA", True, "1"),
    ("1.2.1", "Imobilizado", "ATIVO", "DEVEDORA", True, "1.2"),
    ("1.2.1.1", "Veículos", "ATIVO", "DEVEDORA", False, "1.2.1"),
    ("1.2.1.2", "Imóveis", "ATIVO", "DEVEDORA", False, "1.2.1"),
    # ----- PASSIVO (natureza CREDORA) -----
    ("2", "Passivo", "PASSIVO", "CREDORA", True, None),
    ("2.1", "Passivo Circulante", "PASSIVO", "CREDORA", True, "2"),
    ("2.1.1", "Contas a Pagar", "PASSIVO", "CREDORA", True, "2.1"),
    ("2.1.1.1", "Fornecedores", "PASSIVO", "CREDORA", False, "2.1.1"),
    ("2.1.1.2", "Impostos a Recolher", "PASSIVO", "CREDORA", False, "2.1.1"),
    ("2.1.2", "Empréstimos e Financiamentos", "PASSIVO", "CREDORA", True, "2.1"),
    ("2.1.2.1", "Empréstimos Bancários", "PASSIVO", "CREDORA", False, "2.1.2"),
    # ----- PATRIMÔNIO LÍQUIDO (natureza CREDORA) -----
    ("3", "Patrimônio Líquido", "PATRIMONIO_LIQUIDO", "CREDORA", True, None),
    ("3.1", "Capital Social", "PATRIMONIO_LIQUIDO", "CREDORA", True, "3"),
    ("3.1.1", "Capital Integralizado", "PATRIMONIO_LIQUIDO", "CREDORA", False, "3.1"),
    # ----- RECEITAS (natureza CREDORA) -----
    ("4", "Receitas", "RECEITA", "CREDORA", True, None),
    ("4.1", "Receitas Operacionais", "RECEITA", "CREDORA", True, "4"),
    ("4.1.1", "Vendas", "RECEITA", "CREDORA", False, "4.1"),
    ("4.1.2", "Prestação de Serviços", "RECEITA", "CREDORA", False, "4.1"),
    ("4.2", "Receitas Não Operacionais", "RECEITA", "CREDORA", True, "4"),
    ("4.2.1", "Rendimentos de Investimentos", "RECEITA", "CREDORA", False, "4.2"),
    # ----- DESPESAS (natureza DEVEDORA) -----
    ("5", "Despesas", "DESPESA", "DEVEDORA", True, None),
    ("5.1", "Despesas Operacionais", "DESPESA", "DEVEDORA", True, "5"),
    ("5.1.1", "Pessoal", "DESPESA", "DEVEDORA", True, "5.1"),
    ("5.1.1.1", "Salários", "DESPESA", "DEVEDORA", False, "5.1.1"),
    ("5.1.1.2", "Encargos Sociais", "DESPESA", "DEVEDORA", False, "5.1.1"),
    ("5.1.2", "Ocupação", "DESPESA", "DEVEDORA", True, "5.1"),
    ("5.1.2.1", "Aluguel", "DESPESA", "DEVEDORA", False, "5.1.2"),
    ("5.1.2.2", "Condomínio", "DESPESA", "DEVEDORA", False, "5.1.2"),
    ("5.1.3", "Utilidades", "DESPESA", "DEVEDORA", True, "5.1"),
    ("5.1.3.1", "Energia Elétrica", "DESPESA", "DEVEDORA", False, "5.1.3"),
    ("5.1.3.2", "Água e Esgoto", "DESPESA", "DEVEDORA", False, "5.1.3"),
    ("5.1.3.3", "Internet", "DESPESA", "DEVEDORA", False, "5.1.3"),
    ("5.1.3.4", "Telefonia", "DESPESA", "DEVEDORA", False, "5.1.3"),
    ("5.1.4", "Deslocamento", "DESPESA", "DEVEDORA", True, "5.1"),
    ("5.1.4.1", "Combustível", "DESPESA", "DEVEDORA", False, "5.1.4"),
    ("5.1.4.2", "Transporte Público", "DESPESA", "DEVEDORA", False, "5.1.4"),
    ("5.1.5", "Alimentação", "DESPESA", "DEVEDORA", True, "5.1"),
    ("5.1.5.1", "Mercado", "DESPESA", "DEVEDORA", False, "5.1.5"),
    ("5.1.5.2", "Restaurantes", "DESPESA", "DEVEDORA", False, "5.1.5"),
    ("5.1.6", "Saúde", "DESPESA", "DEVEDORA", True, "5.1"),
    ("5.1.6.1", "Plano de Saúde", "DESPESA", "DEVEDORA", False, "5.1.6"),
    ("5.1.6.2", "Medicamentos", "DESPESA", "DEVEDORA", False, "5.1.6"),
    ("5.1.7", "Educação", "DESPESA", "DEVEDORA", True, "5.1"),
    ("5.1.7.1", "Mensalidades", "DESPESA", "DEVEDORA", False, "5.1.7"),
    ("5.1.8", "Lazer", "DESPESA", "DEVEDORA", True, "5.1"),
    ("5.1.8.1", "Assinaturas e Streaming", "DESPESA", "DEVEDORA", False, "5.1.8"),
    ("5.1.8.2", "Viagens", "DESPESA", "DEVEDORA", False, "5.1.8"),
    ("5.2", "Despesas Financeiras", "DESPESA", "DEVEDORA", True, "5"),
    ("5.2.1", "Juros e Multas", "DESPESA", "DEVEDORA", False, "5.2"),
    ("5.2.2", "Tarifas Bancárias", "DESPESA", "DEVEDORA", False, "5.2"),
]

async def seed_plano_contas(session: AsyncSession) -> int:
    """Popula o plano de contas padrão se a tabela estiver vazia.

    Retorna o número de contas criadas (0 se já havia dados).
    """
    total = await session.scalar(select(func.count(PlanoContas.id)))
    if total:
        return 0

    # Mapa codigo -> id, para resolver o parent_id em tempo de inserção
    codigo_para_id: dict[str, int] = {}
    criados = 0

    for codigo, descricao, tipo, natureza, sintetica, parent_codigo in PLANO_CONTAS_PADRAO:
        conta = PlanoContas(
            codigo=codigo,
            descricao=descricao,
            tipo=tipo,
            natureza=natureza,
            sintetica=sintetica,
            parent_id=codigo_para_id.get(parent_codigo) if parent_codigo else None,
        )
        session.add(conta)
        await session.flush()  # gera o id para o próximo nível usar como parent
        codigo_para_id[codigo] = conta.id
        criados += 1

    await session.commit()
    return criados


# ---------- SEED ----------

async def seed_all(session: AsyncSession) -> dict:
    """Executa todos os seeds em ordem e retorna o que foi criado."""
    usuario_admin = await seed_admin(session)
    plano_contas = await seed_plano_contas(session)
    return {
        "admin_criado": usuario_admin,
        "plano_contas_criadas": plano_contas,
    }


