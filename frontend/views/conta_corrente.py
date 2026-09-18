# views/contas_correntes.py
from datetime import date

import streamlit as st
from api_client import APIClient, APIError

api_client = APIClient()

PAGE_SIZE = 200  # limite máximo aceito pelo backend (le=200)
TIPOS_CONTA = ["CORRENTE", "POUPANCA"]
MOEDAS = ["BRL", "USD", "EUR"]

def _carregar_contas(offset: int = 0):
    """Busca uma página de contas correntes. Retorna (items, total) ou None em erro."""
    try:
        dados = api_client.listar_contas(limit=PAGE_SIZE, offset=offset)
        return dados.get("items", []), dados.get("total", 0)
    except APIError as exc:
        st.error(f"Falha na requisição ({exc.status_code}): {exc.detail}")
        return None
    except Exception:
        st.error("Servidor indisponível. Verifique a conexão com o backend.")
        return None

def _carregar_planos_analiticos():
    """Planos analíticos (únicos aceitos para vincular conta corrente)."""
    try:
        dados = api_client.listar_plano_contas(limit=PAGE_SIZE, offset=0)
        return [c for c in dados.get("items", []) if not c.get("sintetica")]
    except APIError as exc:
        st.error(f"Falha na requisição ({exc.status_code}): {exc.detail}")
        return None
    except Exception:
        st.error("Servidor indisponível. Verifique a conexão com o backend.")
        return None

def _mapa_planos() -> dict:
    """id -> 'codigo - descricao', para exibir na listagem e no select."""
    try:
        dados = api_client.listar_plano_contas(limit=PAGE_SIZE, offset=0)
        return {c["id"]: f"{c['codigo']} - {c['descricao']}" for c in dados.get("items", [])}
    except APIError as exc:
        st.error(f"Falha na requisição ({exc.status_code}): {exc.detail}")
        return {}
    except Exception:
        st.error("Servidor indisponível. Verifique a conexão com o backend.")
        return {}

def _formatar_saldo(valor) -> str:
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "R$ 0,00"

def _mostrar_formulario(conta: dict | None = None) -> None:
    st.subheader(f"✏️ Editar conta: {conta['nome']}" if conta else "➕ Nova conta corrente")

    analiticos = _carregar_planos_analiticos()
    if analiticos is None:
        return  # erro já exibido
    if not analiticos:
        st.warning("Nenhum plano de contas analítico cadastrado. Crie uma conta analítica no Plano de Contas antes de vincular.")
        return

    opcoes_plano = {c["id"]: f"{c['codigo']} - {c['descricao']}" for c in analiticos}
    plano_atual = conta.get("plano_conta_id") if conta else None
    plano_selecionado = plano_atual if plano_atual in opcoes_plano else list(opcoes_plano.keys())[0]

    data_inicial = None
    if conta and conta.get("data_saldo_inicial"):
        try:
            data_inicial = date.fromisoformat(str(conta["data_saldo_inicial"]))
        except ValueError:
            data_inicial = None

    with st.form(key=f"form_cc_{'edit' if conta else 'new'}"):
        nome = st.text_input("Nome", value=conta["nome"] if conta else "", placeholder="Ex.: Conta Principal")
        banco = st.text_input("Banco", value=conta["banco"] if conta else "", placeholder="Ex.: 001")
        agencia = st.text_input("Agência", value=conta["agencia"] if conta else "", placeholder="Ex.: 1234")
        numero = st.text_input("Número", value=conta["numero"] if conta else "", placeholder="Ex.: 56789-0")
        tipo = st.selectbox("Tipo", TIPOS_CONTA, index=TIPOS_CONTA.index(conta["tipo"]) if conta and conta.get("tipo") in TIPOS_CONTA else 0)
        moeda = st.selectbox("Moeda", MOEDAS, index=MOEDAS.index(conta["moeda"]) if conta and conta.get("moeda") in MOEDAS else 0)
        saldo_inicial = st.number_input(
            "Saldo inicial",
            min_value=0.0,
            value=float(conta["saldo_inicial"]) if conta and conta.get("saldo_inicial") is not None else 0.0,
            step=0.01,
            format="%.2f",
        )
        data_saldo_inicial = st.date_input("Data do saldo inicial", value=data_inicial or date.today())
        plano_conta_id = st.selectbox(
            "Plano de contas (apenas analíticos)",
            options=list(opcoes_plano.keys()),
            format_func=lambda x: opcoes_plano[x],
            index=list(opcoes_plano.keys()).index(plano_selecionado),
        )
        ativo = st.checkbox("Ativa", value=conta.get("ativo", True) if conta else True)

        submitted = st.form_submit_button("Salvar", use_container_width=True)

    if submitted:
        payload = {
            "nome": nome.strip(),
            "banco": banco.strip(),
            "agencia": agencia.strip(),
            "numero": numero.strip(),
            "tipo": tipo,
            "moeda": moeda,
            "saldo_inicial": round(float(saldo_inicial), 2),
            "data_saldo_inicial": data_saldo_inicial.isoformat(),
            "plano_conta_id": plano_conta_id,
            "ativo": bool(ativo),
        }
        try:
            resp = (
                api_client.atualizar_conta(conta["id"], payload)
                if conta
                else api_client.criar_conta(payload)
            )
            if "id" in resp:
                st.success("Conta corrente salva com sucesso!")
                st.session_state.pop("cc_editar", None)
                st.session_state.pop("cc_form_aberto", None)
                st.rerun()
            else:
                st.error("Resposta inesperada do servidor.")
        except APIError as exc:
            st.error(f"Falha na requisição ({exc.status_code}): {exc.detail}")
        except Exception:
            st.error("Servidor indisponível. Verifique a conexão com o backend.")

    if st.button("Cancelar"):
        st.session_state.pop("cc_editar", None)
        st.session_state.pop("cc_form_aberto", None)
        st.rerun()

def _render_tabela(items: list, planos: dict) -> None:
    if not items:
        st.info("Nenhuma conta corrente cadastrada. Use 'Nova conta corrente' para começar.")
        return

    # widths = [2.2, 1, 1.1, 1.4, 1.2, 0.9, 1.3, 2.4, 1, 1.6]
    widths = [2.2, 1, 1.1, 1.4, 1.2, 0.9, 1.3, 2.4, 1, 1.6]
    header = st.columns(widths)
    headers = ["Nome", "Banco", "Agência", "Número", "Tipo", "Moeda", "Saldo inicial", "Plano de contas", "Status", "Ações"]
    for col, label in zip(header, headers):
        col.markdown(f"**{label}**")
    st.divider()

    for item in items:
        col = st.columns(widths)
        col[0].markdown(f"**{item['nome']}**")
        col[1].write(item["banco"])
        col[2].write(item["agencia"])
        col[3].write(item["numero"])
        col[4].write(item["tipo"])
        col[5].write(item["moeda"])
        col[6].write(_formatar_saldo(item.get("saldo_inicial")))
        col[7].write(planos.get(item.get("plano_conta_id"), "-"))
        col[8].write("✅ Ativa" if item.get("ativo") else "⛔ Inativa")

        st.html(
            "<style>button{padding:0!important;background-color:red!important;}</style>"
        )
        # ajustar seletor apenas para os botoes dentro do relatorio
        #<button kind="secondary" data-testid="stBaseButton-secondary" aria-label="" class="st-emotion-cache-en1taq eqzt73c2"><div class="st-emotion-cache-ztlrr4 eqzt73c22"><span data-has-shortcut="false" class="st-emotion-cache-o0vne1 eqzt73c23"><span style="display: contents;"><div data-testid="stMarkdownContainer" class="st-emotion-cache-88blro ewutnf10"><p>🗑️</p></div></span></span></div></button>
        with col[9]:
            c_editar, c_excluir = st.columns(2)
            if c_editar.button(
                "✏️", key=f"cc_editar_{item['id']}", help="Editar",
                use_container_width=True,
            ):
                st.session_state["cc_editar"] = item
                st.rerun()
            if c_excluir.button(
                "🗑️", key=f"cc_excluir_{item['id']}", help="Excluir",
                use_container_width=True,
            ):
                st.session_state["cc_excluir"] = item
                st.rerun()

def _render_paginacao(total: int, offset: int) -> None:
    if total == 0:
        return
    col1, col2, col3 = st.columns(3)
    with col1:
        if offset > 0 and st.button("⬅️ Anterior"):
            st.session_state["cc_offset"] = max(0, offset - PAGE_SIZE)
            st.rerun()
    with col2:
        fim = min(offset + PAGE_SIZE, total)
        st.markdown(f"<div style='text-align:center'>Exibindo {offset + 1}–{fim} de {total}</div>", unsafe_allow_html=True)
    with col3:
        if offset + PAGE_SIZE < total and st.button("Próxima ➡️"):
            st.session_state["cc_offset"] = offset + PAGE_SIZE
            st.rerun()

def _render_confirmacao_exclusao() -> None:
    item = st.session_state.get("cc_excluir")
    if not item:
        return
    st.warning(f"Excluir a conta corrente **{item['nome']}** ({item['banco']} / {item['agencia']} / {item['numero']})?")
    c1, c2 = st.columns(2)
    if c1.button("Confirmar exclusão", type="primary"):
        try:
            ok = api_client.excluir_conta(item["id"])
            if ok:
                st.success("Conta corrente excluída.")
            else:
                st.error("Não foi possível excluir a conta corrente.")
        except APIError as exc:
            st.error(f"Não foi possível excluir ({exc.status_code}): {exc.detail}")
        except Exception:
            st.error("Erro ao excluir. Servidor indisponível?")
        st.session_state.pop("cc_excluir", None)
        st.rerun()
    if c2.button("Cancelar"):
        st.session_state.pop("cc_excluir", None)
        st.rerun()

def render_contas_correntes() -> None:
    offset = st.session_state.get("cc_offset", 0)

    if st.session_state.get("cc_form_aberto") or st.session_state.get("cc_editar"):
        _mostrar_formulario(st.session_state.get("cc_editar"))
    else:
        col_titulo, col_btn = st.columns([3, 1])
        with col_titulo:
            st.subheader("🏦 Contas Correntes")
        with col_btn:
            if st.button("➕ Nova conta corrente", use_container_width=True):
                st.session_state["cc_form_aberto"] = True
                st.rerun()

        resultado = _carregar_contas(offset)
        if resultado is None:
            return  # erro já exibido
        items, total = resultado
        planos = _mapa_planos()
        items = sorted(items, key=lambda c: (str(c.get("banco", "")), str(c.get("agencia", "")), str(c.get("numero", ""))))
        _render_tabela(items, planos)
        _render_paginacao(total, offset)

    _render_confirmacao_exclusao()

render_contas_correntes()

