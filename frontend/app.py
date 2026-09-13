import streamlit as st
from logger import setup_logger, logger

from api_client import APIClient
api_client = APIClient()


st.set_page_config(
    page_title="Sistema Financeiro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializa o estado de autenticação
# TODO: verificacao de autenticacao e recuperar usuario nao deveriam ser funcoes da classe APIClient, preservando os controles de sessao?
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user" not in st.session_state:
    st.session_state["user"] = None

# Componente de Cabeçalho Superior
def render_header():
    if st.session_state["authenticated"] and st.session_state["user"] and 1==3:
        user_name = st.session_state["user"].get("nome", "Usuário")
        col_title, col_user = st.columns([4, 1])
        with col_user:
            st.caption(f"👤 **{user_name}**")

# Definição das Páginas para Roteamento
def setup_navigation():
    if not st.session_state["authenticated"]:
        return st.navigation([
            st.Page("views/login.py", title="Login", icon="🔑")
        ])

    return st.navigation({
        "Menu Principal": [
            st.Page("views/dashboard.py", title="Dashboard", icon="📊", default=True),
            st.Page("views/titulos.py", title="Contas a Pagar", icon="📄"),
        ],
    })

# Menu Lateral (Sidebar)
def render_sidebar():
    if st.session_state["authenticated"]:
        
        with st.sidebar:
            st.title("⚙️ Sistema Financeiro")
            user_name = st.session_state["user"].get("nome", "Usuário") # st.session_state['user'].get('email')
            st.caption(f"👤 **{user_name}**")
            if st.button("Sair / Logout", use_container_width=True, type="secondary"):
                APIClient.logout()
                st.rerun()

# Execução da Aplicação
def main():
#    setup_logger()
    nav = setup_navigation()
    render_sidebar()
    render_header()
    nav.run()

if __name__ == "__main__":
    main()