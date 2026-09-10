import streamlit as st
from api_client import APIClient

def render_login_page():
#    st.title("🔑 Acesso ao Sistema")
#    st.subheader("Gestão de Contas a Pagar & Caixa")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("form_login", clear_on_submit=False):
            st.subheader("🔑 Login - Gestão de Contas a Pagar & Caixa")
            st.divider()
            email = st.text_input("E-mail", placeholder="usuario@empresa.com")
            senha = st.text_input("Senha", type="password")
            btn_submit = st.form_submit_button("Entrar", use_container_width=True)

            if btn_submit:
                if not email or not senha:
                    st.warning("Preencha todos os campos.")
                else:
                    with st.spinner("Autenticando..."):
                        if APIClient.login(email, senha):
                            st.success("Login realizado com sucesso!")
                            st.rerun()
                        else:
                            st.error("Credenciais inválidas ou erro no servidor.")

render_login_page()