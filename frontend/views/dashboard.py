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


def _card_html(titulo: str, valor: int, cor_texto: str, cor_fundo: str, cor_borda: str) -> str:
    """Define um card com titulo (linhas superior), valor (linha inferior), e cores de texto, fundo e borda customizáveis""" 
    return f"""
    <div style="background-color:{cor_fundo}; border-left:6px solid {cor_borda};
                padding:20px; border-radius:10px; text-align:center;
                box-shadow:0 2px 6px rgba(0,0,0,0.08);">
        <div style="font-size:14px; color:#555; margin-bottom:4px;">{titulo}</div>
        <div style="font-size:36px; font-weight:700; color:{cor_texto};">{valor}</div>
    </div>
    """

def _render_inline_cards(cards: list):
    """Cria uma sequência de cards dispostos horizontalmente e retorna o container"""
    if len(cards) > 0:
        container = st.container()
        cols = container.columns(len(cards))
        for card, col in zip(cards, cols):
            html = _card_html(
                card["title"],
                card["value"],
                card["text_color"],
                card["background_color"],
                card["border_color"]
            )
            col.markdown(html, unsafe_allow_html=True)
        return container
    return None

def render_dashboard() -> None:
    st.subheader("📊 Visão Geral")

    tabs = st.tabs(
        ["Plano de Contas", "Contas Corrente", "Base de Dados"]
    )


    # ---------- PLANO DE CONTAS ----------

    with tabs[0]:
        st.markdown("#### Plano de Contas")

        itens_plano_contas, erro = _carregar_plano_ativos()

        # trata retorno
        if erro:
            st.error(f"Falha no processamento da consulta ao plano de contas: {erro}")
        elif not itens_plano_contas:
            st.info("Nenhuma conta cadastrada no plano de contas ainda.")
        else:

            # Define a disposicao na tela
            cont_cards = st.container()

            cont_charts = st.container()
            with cont_charts:
                charts = st.columns(2)

            # formata legenda acima do grafico
            _legend_layout = dict(
                    orientation="h", # horizontal
        #            yanchor="bottom", y=0.97, # posição acima do grafico
                    yanchor="top", y=-0.05, # posição abaixo do gráfico
                    xanchor="center", x=0.5, # centralizar
                    bordercolor="silver", borderwidth=1, # borda
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

            qtd_credito = sum(1 for c in itens_plano_contas if c.get("ativo") and c.get("natureza")=="CREDORA")
            qtd_debito = sum(1 for c in itens_plano_contas if c.get("ativo") and c.get("natureza")=="DEVEDORA")

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
                {"title":"Contas ativas", "value":qtd_total, "text_color":"#2E7D32", "background_color":"#E8F5E9", "border_color":"#2E7D32"},
                {"title":"Contas Analíticas", "value":qtd_analitica, "text_color":"#734de3", "background_color":"#e3dbf9", "border_color":"#734de3"},
                {"title":"Contas de Crédito", "value":qtd_credito, "text_color":"#0068C9", "background_color":"#cce1f4", "border_color":"#0068C9"},
                {"title":"Contas de Débito", "value":qtd_debito, "text_color":"#C62828", "background_color":"#FFEBEE", "border_color":"#C62828"}
            ])

            charts2 = st.columns(2)


            # ----- distribuição por tipo

            df = pd.DataFrame(itens_plano_contas)
            contas_by_tipo = df.groupby("tipo").size().reset_index(name="Quantidade")

            fig11 = px.bar(
                contas_by_tipo,
                x="tipo",
                y="Quantidade",
                title="Distribuição por Tipo",
                color="tipo",
                text="Quantidade"
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
                text="Quantidade"
            )
            fig12.update_traces(textposition="outside")
            fig12.update_layout(height=420, showlegend=False)
            charts2[1].plotly_chart(fig12, width='stretch')


            # Gráfico hierárquico (treemap)

            fig13 = px.treemap(
                df,
                path=["tipo","descricao"],
                #values="codigo", 
                #color="tipo", color_discrete_map={"ATIVO": "#0068C9", "PASSIVO": "#C62828"},
                color="tipo", color_discrete_map={
                    "ATIVO": "#0068C9", "DESPESA": "#C62828",
                    "RECEITA": "#2E7D32", "PASSIVO": "#FF9800",
                    },

                title="[Treemap] Tipo / Descrição",
            )
            fig13.update_layout(height=800)
            st.plotly_chart(fig13, width='stretch')


            # Gráfico hierárquico circular

            fig14 = px.sunburst(
                df,
                path=["tipo","descricao"],
                #values="codigo", 
                color="tipo", color_discrete_map={
                    "ATIVO": "#0068C9", "DESPESA": "#C62828",
                    "RECEITA": "#2E7D32", "PASSIVO": "#FF9800",
                    },
                title="[Sunburst] Tipo / Descrição"
            )
            fig14.update_layout(height=800)
            st.plotly_chart(fig14, width='stretch')


    # ---------- CONTA CORRENTE ----------

    with tabs[1]:

        None

    # ---------- DADOS ----------

    with tabs[2]:

        with st.expander("Plano de Contas (somente contas ativas)"):
            st.write(pd.DataFrame(itens_plano_contas))

render_dashboard()