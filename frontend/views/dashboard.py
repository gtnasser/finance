# views/dashboard.py
import pandas as pd
import plotly.express as px
import streamlit as st
from api_client import APIClient, APIError

api_client = APIClient()

PAGE_SIZE = 200  # limite máximo aceito pelo backend (le=200)

def _carregar_plano_ativos() -> tuple:
    """Busca todas as páginas do plano de contas (envelope paginado).
    Retorna (itens, erro): erro é None em sucesso, ou a mensagem da falha.
    """
    itens: list = []
    offset = 0
    try:
        while True:
            dados = api_client.listar_plano_contas(limit=PAGE_SIZE, offset=offset)
            pagina = dados.get("items", [])
            itens.extend(pagina)
            offset += len(pagina)
            if offset >= dados.get("total", 0) or not pagina:
                break
        itens_ativos = [item for item in itens if item["ativo"]]
        return itens_ativos, None
    except APIError as exc:
        return [], f"Falha na requisição ({exc.status_code}): {exc.detail}"
    except Exception:
        return [], "Servidor indisponível. Verifique a conexão com o backend."

def _carregar_contas_ativas() -> tuple:
    """Busca todas as páginas de contas correntes (envelope paginado).
    Retorna (itens, erro): erro é None em sucesso, ou a mensagem da falha.
    """
    itens: list = []
    offset = 0
    try:
        while True:
            dados = api_client.listar_contas(limit=PAGE_SIZE, offset=offset)
            pagina = dados.get("items", [])
            itens.extend(pagina)
            offset += len(pagina)
            if offset >= dados.get("total", 0) or not pagina:
                break
        itens_ativos = [item for item in itens if item["ativo"]]
        return itens_ativos, None
    except APIError as exc:
        return [], f"Falha na requisição ({exc.status_code}): {exc.detail}"
    except Exception:
        return [], "Servidor indisponível. Verifique a conexão com o backend."

def _card_html(titulo: str, valor, cor_texto: str, cor_fundo: str, cor_borda: str) -> str:
    """Define um card com titulo (linha superior), valor (linha inferior) e cores customizáveis."""
    return f"""
    <div style="background-color:{cor_fundo}; border-left:6px solid {cor_borda};
                padding:20px; border-radius:10px; text-align:center;
                box-shadow:0 2px 6px rgba(0,0,0,0.08);">
        <div style="font-size:14px; color:#555; margin-bottom:4px;">{titulo}</div>
        <div style="font-size:36px; font-weight:700; color:{cor_texto};">{valor}</div>
    </div>
    """

def _render_inline_cards(cards: list):
    """Cria uma sequência de cards dispostos horizontalmente e retorna o container."""
    if len(cards) > 0:
        container = st.container()
        cols = container.columns(len(cards))
        for card, col in zip(cards, cols):
            html = _card_html(
                card["title"],
                card["value"],
                card["text_color"],
                card["background_color"],
                card["border_color"],
            )
            col.markdown(html, unsafe_allow_html=True)
        return container
    return None

def _formatar_moeda(valor: float) -> str:
    """Formata valor em moeda brasileira (R$ 1.234,56)."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def render_dashboard() -> None:
    st.subheader("📊 Visão Geral")

				   
															   
    # Carrega os dados uma única vez (usados nas abas)
    itens_plano_contas, erro_pc = _carregar_plano_ativos()
    itens_contas, erro_cc = _carregar_contas_ativas()

    tabs = st.tabs(["Plano de Contas", "Contas Correntes", "Base de Dados"])

    # ---------- PLANO DE CONTAS ----------

    with tabs[0]:
        st.markdown("#### Plano de Contas")

														   

					   
        if erro_pc:
            st.error(f"Falha no processamento da consulta ao plano de contas: {erro_pc}")
        elif not itens_plano_contas:
            st.info("Nenhuma conta cadastrada no plano de contas ainda.")
        else:

										 
            cont_cards = st.container()

            cont_charts = st.container()
            with cont_charts:
                charts = st.columns(2)

            # Formata legenda do grafico										  
            _legend_layout = dict(
                orientation="h",
																		   
                yanchor="top", y=-0.05,
                xanchor="center", x=0.5,
                bordercolor="silver", borderwidth=1,
            )

            qtd_total = len(itens_plano_contas)

            # ----- distribuição por hierarquia -----

            qtd_analitica = sum(1 for c in itens_plano_contas if c.get("ativo") and not c.get("sintetica"))
            qtd_sintetica = sum(1 for c in itens_plano_contas if c.get("ativo") and c.get("sintetica"))

            contas_by_hierarquia = pd.DataFrame(
                {"Hierarquia": ["Sintética", "Analítica"], "Quantidade": [qtd_sintetica, qtd_analitica]}
            )

            fig2 = px.pie(
                contas_by_hierarquia,
                names="Hierarquia",
                values="Quantidade",
                title="Distribuição por Hierarquia",
                color="Hierarquia",
                color_discrete_map={"Sintética": "#00cc96", "Analítica": "#734de3"},
                hole=0.4,
            )
            fig2.update_traces(textinfo="value+percent", textposition="inside")
            fig2.update_layout(showlegend=True, legend=_legend_layout, height=420)
            charts[0].plotly_chart(fig2, width='stretch')


            # ----- distribuição por natureza -----

            qtd_credito = sum(1 for c in itens_plano_contas if c.get("ativo") and c.get("natureza") == "CREDORA")
            qtd_debito = sum(1 for c in itens_plano_contas if c.get("ativo") and c.get("natureza") == "DEVEDORA")

            contas_by_natureza = pd.DataFrame(
                {"Natureza": ["Crédito", "Débito"], "Quantidade": [qtd_credito, qtd_debito]}
            )

            fig3 = px.pie(
                contas_by_natureza,
                names="Natureza",
                values="Quantidade",
                title="Distribuição por Natureza",
                color="Natureza",
                color_discrete_map={"Crédito": "#0068C9", "Débito": "#C62828"},
                hole=0.4,
            )
            fig3.update_traces(textinfo="value+percent", textposition="inside")
            fig3.update_layout(showlegend=True, legend=_legend_layout, height=420)
            charts[1].plotly_chart(fig3, width='stretch')


            # ----- cards -----

            with cont_cards:
                _render_inline_cards([
                    {"title": "Contas ativas", "value": qtd_total, "text_color": "#2E7D32", "background_color": "#E8F5E9", "border_color": "#2E7D32"},
                    {"title": "Contas Analíticas", "value": qtd_analitica, "text_color": "#734de3", "background_color": "#e3dbf9", "border_color": "#734de3"},
                    {"title": "Contas de Crédito", "value": qtd_credito, "text_color": "#0068C9", "background_color": "#cce1f4", "border_color": "#0068C9"},
                    {"title": "Contas de Débito", "value": qtd_debito, "text_color": "#C62828", "background_color": "#FFEBEE", "border_color": "#C62828"},
                ])

            charts2 = st.columns(2)


            # ----- distribuição por tipo -----

            df = pd.DataFrame(itens_plano_contas)
            contas_by_tipo = df.groupby("tipo").size().reset_index(name="Quantidade")

            fig11 = px.bar(
                contas_by_tipo,
                x="tipo",
                y="Quantidade",
                title="Distribuição por Tipo",
                color="tipo",
                text="Quantidade",
            )
            fig11.update_traces(textposition="outside")
            fig11.update_layout(height=420, showlegend=False)
            charts2[0].plotly_chart(fig11, width='stretch')

            fig12 = px.bar(
                contas_by_tipo,
                y="tipo",
                x="Quantidade",
                title="Distribuição por Tipo",
                orientation="h",
                color="tipo",
                text="Quantidade",
            )
            fig12.update_traces(textposition="outside")
            fig12.update_layout(height=420, showlegend=False)
            charts2[1].plotly_chart(fig12, width='stretch')


            # ----- gráficos hierárquicos -----

            fig13 = px.treemap(
                df,
                path=["tipo", "descricao"],
								  
                color="tipo",
                color_discrete_map={
                    "ATIVO": "#0068C9", "PASSIVO": "#FF9800",
                    "RECEITA": "#2E7D32", "DESPESA": "#C62828",
                },

                title="[Treemap] Tipo / Descrição",
            )
            fig13.update_layout(height=800)
            st.plotly_chart(fig13, width='stretch')

            fig14 = px.sunburst(
                df,
                path=["tipo", "descricao"],
                color="tipo",
                color_discrete_map={
                    "ATIVO": "#0068C9", "PASSIVO": "#FF9800",
                    "RECEITA": "#2E7D32", "DESPESA": "#C62828",
                },
                title="[Sunburst] Tipo / Descrição",
            )
            fig14.update_layout(height=800)
            st.plotly_chart(fig14, width='stretch')


    # ---------- CONTAS CORRENTES ----------

    with tabs[1]:
        st.markdown("#### Contas Correntes")

        if erro_cc:
            st.error(f"Falha no processamento da consulta às contas correntes: {erro_cc}")
        elif not itens_contas:
            st.info("Nenhuma conta corrente cadastrada ainda.")
        else:
            cont_cards = st.container()

            cont_charts = st.container()
            with cont_charts:
                charts = st.columns(2)

            _legend_layout = dict(
                orientation="h",
                yanchor="top", y=-0.05,
                xanchor="center", x=0.5,
                bordercolor="silver", borderwidth=1,
            )

            qtd_total = len(itens_contas)
            qtd_corrente = sum(1 for c in itens_contas if c.get("tipo") == "CORRENTE")
            qtd_poupanca = sum(1 for c in itens_contas if c.get("tipo") == "POUPANCA")
            saldo_total = sum(float(c.get("saldo_inicial") or 0) for c in itens_contas)

            # ----- distribuição por tipo -----

            contas_by_tipo_cc = pd.DataFrame(
                {"Tipo": ["Corrente", "Poupança"], "Quantidade": [qtd_corrente, qtd_poupanca]}
            )

            fig_cc1 = px.pie(
                contas_by_tipo_cc,
                names="Tipo",
                values="Quantidade",
                title="Distribuição por Tipo",
                color="Tipo",
                color_discrete_map={"Corrente": "#0068C9", "Poupança": "#2E7D32"},
                hole=0.4,
            )
            fig_cc1.update_traces(textinfo="value+percent", textposition="inside")
            fig_cc1.update_layout(showlegend=True, legend=_legend_layout, height=420)
            charts[0].plotly_chart(fig_cc1, width='stretch')

            # ----- distribuição por moeda -----

            df_cc = pd.DataFrame(itens_contas)
            contas_by_moeda = df_cc.groupby("moeda").size().reset_index(name="Quantidade")

            fig_cc2 = px.pie(
                contas_by_moeda,
                names="moeda",
                values="Quantidade",
                title="Distribuição por Moeda",
                color="moeda",
                color_discrete_map={"BRL": "#2E7D32", "USD": "#0068C9", "EUR": "#FF9800"},
                hole=0.4,
            )
            fig_cc2.update_traces(textinfo="value+percent", textposition="inside")
            fig_cc2.update_layout(showlegend=True, legend=_legend_layout, height=420)
            charts[1].plotly_chart(fig_cc2, width='stretch')

            # ----- cards -----

            with cont_cards:
                _render_inline_cards([
                    {"title": "Contas ativas", "value": qtd_total, "text_color": "#2E7D32", "background_color": "#E8F5E9", "border_color": "#2E7D32"},
                    {"title": "Correntes", "value": qtd_corrente, "text_color": "#0068C9", "background_color": "#cce1f4", "border_color": "#0068C9"},
                    {"title": "Poupanças", "value": qtd_poupanca, "text_color": "#2E7D32", "background_color": "#E8F5E9", "border_color": "#2E7D32"},
                    {"title": "Saldo inicial total", "value": _formatar_moeda(saldo_total), "text_color": "#333333", "background_color": "#F5F5F5", "border_color": "#757575"},
                ])

            charts2 = st.columns(2)

            # ----- saldo por banco -----

            saldo_by_banco = df_cc.groupby("banco")["saldo_inicial"].sum().reset_index(name="Saldo")
            saldo_by_banco = saldo_by_banco.sort_values("Saldo", ascending=False)

            fig_cc3 = px.bar(
                saldo_by_banco,
                x="banco",
                y="Saldo",
                title="Saldo inicial por Banco",
                color="banco",
                text="Saldo",
            )
            fig_cc3.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            fig_cc3.update_layout(height=420, showlegend=False)
            charts2[0].plotly_chart(fig_cc3, width='stretch')

            fig_cc4 = px.bar(
                saldo_by_banco,
                y="banco",
                x="Saldo",
                title="Saldo inicial por Banco",
                orientation="h",
                color="banco",
                text="Saldo",
            )
            fig_cc4.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            fig_cc4.update_layout(height=420, showlegend=False)
            charts2[1].plotly_chart(fig_cc4, width='stretch')

            # ----- gráficos hierárquicos -----

            fig_cc5 = px.treemap(
                df_cc,
                path=["banco", "nome"],
                color="tipo",
                color_discrete_map={"CORRENTE": "#0068C9", "POUPANCA": "#2E7D32"},
                title="[Treemap] Banco / Conta",
            )
            fig_cc5.update_layout(height=800)
            st.plotly_chart(fig_cc5, width='stretch')

            fig_cc6 = px.sunburst(
                df_cc,
                path=["banco", "nome"],
                color="tipo",
                color_discrete_map={"CORRENTE": "#0068C9", "POUPANCA": "#2E7D32"},
                title="[Sunburst] Banco / Conta",
            )
            fig_cc6.update_layout(height=800)
            st.plotly_chart(fig_cc6, width='stretch')

    # ---------- BASE DE DADOS ----------

    with tabs[2]:
        with st.expander("Plano de Contas (somente contas ativas)"):
            st.write(pd.DataFrame(itens_plano_contas))

        with st.expander("Contas Correntes (somente contas ativas)"):
            st.write(pd.DataFrame(itens_contas))

render_dashboard()
					