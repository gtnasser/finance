import streamlit as st

from api_client import APIClient
api_client = APIClient()


st.set_page_config(
    page_title="Sistema Financeiro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializa o estado de autenticação
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user" not in st.session_state:
    st.session_state["user"] = None

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
            st.Page("views/plano_contas.py", title="Plano de Contas", icon="📚"),
            st.Page("views/conta_corrente.py", title="Conta Corrente", icon="🏦"),
        ],
        "Cadastros": [st.Page("views/contas.py", title="Contas Bancárias", icon="💰")],
        "Desenvolvimento": [st.Page("views/testes.py", title="Painel de Testes", icon="🧪")],
    })

# Menu Lateral (Sidebar)
def render_sidebar():
    if st.session_state["authenticated"]:
        
        with st.sidebar:
            st.title("⚙️ Sistema Financeiro")
            user_name = st.session_state["user"].get("nome", "Usuário")
            st.caption(f"👤 **{user_name}**")
            if st.button("Sair / Logout", use_container_width=True, type="secondary"):
                api_client.logout()
                st.rerun()

# Execução da Aplicação
def main():
    nav = setup_navigation()
    render_sidebar()
    nav.run()

if __name__ == "__main__":
    main()