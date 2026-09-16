# views/plano_contas.py
import streamlit as st
from api_client import APIClient

api_client = APIClient()

PAGE_SIZE = 50
TIPOS = ["ATIVO", "PASSIVO", "RECEITA", "DESPESA"]
NATUREZAS = ["DEVEDORA", "CREDORA"]

def _mensagem_erro(resp: dict) -> str:
    """Extrai a mensagem de erro do envelope (detail pode ser str ou lista)."""
    detail = resp.get("detail", "Erro desconhecido")
    if isinstance(detail, list):
        return "; ".join(str(e.get("msg", e)) for e in detail)
    return str(detail)

def _carregar_plano(offset: int = 0) -> tuple:
    """Busca uma página do plano de contas. Retorna (items, total)."""
    try:
        dados = api_client.listar_plano_contas(limit=PAGE_SIZE, offset=offset)
        return dados.get("items", []), dados.get("total", 0)
    except Exception:
        st.error("Servidor indisponível. Verifique se o backend está no ar.")
        return [], 0

def _carregar_sinteticas() -> list:
    """Contas sintéticas (candidatas a 'conta superior'), para os selects."""
    try:
        dados = api_client.listar_plano_contas(limit=1000, offset=0)
        return [c for c in dados.get("items", []) if c.get("sintetica")]
    except Exception:
        return []

def _ordenar_hierarquia(items: list) -> list:
    """Ordena por nível hierárquico numérico (1, 1.1, 1.1.1...)."""
    def chave(item):
        return [int(p) for p in item["codigo"].split(".")]
    return sorted(items, key=chave)

def _nome_pai(items: list, parent_id) -> str:
    for item in items:
        if item["id"] == parent_id:
            return f"{item['codigo']} - {item['descricao']}"
    return "-"

def _mostrar_formulario(conta: dict | None = None) -> None:
    """Formulário de criação (conta=None) ou edição (conta=dict)."""
    st.subheader(f"✏️ Editar conta: {conta['codigo']}" if conta else "➕ Nova conta")

    sinteticas = _carregar_sinteticas()
    if conta:
        # a própria conta não pode ser superior de si mesma
        sinteticas = [c for c in sinteticas if c["id"] != conta["id"]]

    opcoes_pai = {0: "— Nenhuma (conta raiz) —"}
    opcoes_pai.update({c["id"]: f"{c['codigo']} - {c['descricao']}" for c in sinteticas})
    parent_atual = conta.get("parent_id") if conta else None
    parent_selecionado = parent_atual if parent_atual in opcoes_pai else 0

    with st.form(key=f"form_pc_{'edit' if conta else 'new'}"):
        codigo = st.text_input("Código", value=conta["codigo"] if conta else "", placeholder="Ex.: 1.1.1")
        descricao = st.text_input("Descrição", value=conta["descricao"] if conta else "", placeholder="Ex.: Contas a Receber")
        tipo = st.selectbox("Tipo", TIPOS, index=TIPOS.index(conta["tipo"]) if conta and conta.get("tipo") in TIPOS else 0)
        natureza = st.selectbox("Natureza", NATUREZAS, index=NATUREZAS.index(conta["natureza"]) if conta and conta.get("natureza") in NATUREZAS else 0)
        sintetica = st.checkbox("Conta sintética (agrupadora)", value=conta.get("sintetica", True) if conta else True)
        parent_id = st.selectbox(
            "Conta superior (apenas sintéticas)",
            options=list(opcoes_pai.keys()),
            format_func=lambda x: opcoes_pai[x],
            index=list(opcoes_pai.keys()).index(parent_selecionado),
        )
        ativo = st.checkbox("Ativa", value=conta.get("ativo", True) if conta else True)

        submitted = st.form_submit_button("Salvar", use_container_width=True)

    if submitted:
        payload = {
            "codigo": codigo.strip(),
            "descricao": descricao.strip(),
            "tipo": tipo,
            "natureza": natureza,
            "sintetica": bool(sintetica),
            "parent_id": parent_id if parent_id != 0 else None,
            "ativo": bool(ativo),
        }
        try:
            resp = (
                api_client.atualizar_plano_conta(conta["id"], payload)
                if conta
                else api_client.criar_plano_conta(payload)
            )
            if "id" in resp:
                st.success("Conta salva com sucesso!")
                st.session_state.pop("pc_editar", None)
                st.session_state.pop("pc_form_aberto", None)
                st.rerun()
            else:
                st.error(_mensagem_erro(resp))
        except Exception:
            st.error("Erro ao salvar. Verifique os dados e tente novamente.")

    if st.button("Cancelar"):
        st.session_state.pop("pc_editar", None)
        st.session_state.pop("pc_form_aberto", None)
        st.rerun()

def _render_tabela(items: list) -> None:
    if not items:
        st.info("Nenhuma conta cadastrada. Use 'Nova conta' para começar.")
        return

    widths = [1, 3.5, 1.2, 1.4, 1.2, 3.5, 1.1, 1.5]
    header = st.columns(widths)
    headers = ["Código", "Descrição", "Tipo", "Natureza", "Tipo de conta", "Conta superior", "Status", "Ações"]
    for col, label in zip(header, headers):
        col.markdown(f"**{label}**")
    st.divider()

    for item in items:
        nivel = item["codigo"].count(".")
        col = st.columns(widths)
        col[0].markdown(f"**{item['codigo']}**")
        col[1].markdown("&emsp;" * nivel + item["descricao"])
        col[2].write(item["tipo"])
        col[3].write(item["natureza"])
        col[4].write("Sintética" if item.get("sintetica") else "Analítica")
        col[5].write(_nome_pai(items, item.get("parent_id")))
        col[6].write("✅ Ativa" if item.get("ativo") else "⛔ Inativa")

        with col[7]:
            c_editar, c_excluir = st.columns(2)
            if c_editar.button("✏️", key=f"pc_editar_{item['id']}", help="Editar", use_container_width=True, ):
                st.session_state["pc_editar"] = item
                st.rerun()
            if c_excluir.button("🗑️", key=f"pc_excluir_{item['id']}", help="Excluir", use_container_width=True, ):
                st.session_state["pc_excluir"] = item
                st.rerun()
                

def _render_paginacao(total: int, offset: int) -> None:
    if total == 0:
        return
    col1, col2, col3 = st.columns(3)
    with col1:
        if offset > 0 and st.button("⬅️ Anterior"):
            st.session_state["pc_offset"] = max(0, offset - PAGE_SIZE)
            st.rerun()
    with col2:
        fim = min(offset + PAGE_SIZE, total)
        st.markdown(f"<div style='text-align:center'>Exibindo {offset + 1}–{fim} de {total}</div>", unsafe_allow_html=True)
    with col3:
        if offset + PAGE_SIZE < total and st.button("Próxima ➡️"):
            st.session_state["pc_offset"] = offset + PAGE_SIZE
            st.rerun()

def _render_confirmacao_exclusao() -> None:
    item = st.session_state.get("pc_excluir")
    if not item:
        return
    st.warning(f"Excluir a conta **{item['codigo']} - {item['descricao']}**?")
    c1, c2 = st.columns(2)
    if c1.button("Confirmar exclusão", type="primary"):
        try:
            ok = api_client.excluir_plano_conta(item["id"])
            if ok:
                st.success("Conta excluída.")
            else:
                st.error("Não foi possível excluir. Verifique as regras: conta com filhos ou vinculada a conta corrente não pode ser excluída.")
            st.session_state.pop("pc_excluir", None)
            st.rerun()
        except Exception:
            st.error("Erro ao excluir.")
    if c2.button("Cancelar"):
        st.session_state.pop("pc_excluir", None)
        st.rerun()

def render_plano_contas() -> None:
    offset = st.session_state.get("pc_offset", 0)

    if st.session_state.get("pc_form_aberto") or st.session_state.get("pc_editar"):
        _mostrar_formulario(st.session_state.get("pc_editar"))
    else:
        col_titulo, col_btn = st.columns([3, 1])
        with col_titulo:
            st.subheader("📚 Plano de Contas")
        with col_btn:
            if st.button("➕ Nova conta", use_container_width=True):
                st.session_state["pc_form_aberto"] = True
                st.rerun()

        items, total = _carregar_plano(offset)
        items = _ordenar_hierarquia(items)
        _render_tabela(items)
        _render_paginacao(total, offset)

    _render_confirmacao_exclusao()

render_plano_contas()
