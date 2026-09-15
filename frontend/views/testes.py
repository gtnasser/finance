import streamlit as st
from api_client import APIClient, API_BASE_URL, API_BASE_PREFIX
import httpx
import time

st.set_page_config(page_title="Painel de Testes", page_icon="🧪", layout="wide")

st.subheader("🧪 Laboratório de Testes da API")
st.markdown("Página dedicada a validações de chamadas e integrações com o backend.")

# Inicializa o cliente HTTP da API
api_client = APIClient()

# --- STATUS DA SESSÃO ATUAL ---
with st.expander("ℹ️ Estado Atual da Sessão"):
    if st.session_state.get("user"):
        st.info(f"**user:** `{st.session_state.get('user')}`")
    if st.session_state.get("token"):
        st.info(f"**token ativo:** `{st.session_state.get('token')}`")
    if st.session_state.get("cod"):
        st.info(f"**status_code:** `{st.session_state.get('cod')}`")

st.divider()

# --- TESTE 1: Geração de Token - chamada direta na API ---
st.write(f"**1. Autenticar Usuário**")

def get_token1() -> bool: 
    with st.spinner("Obtendo token..."):
        try:
            data = {"username": username1, "password": password1}
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            response = httpx.request(
                "POST", 
                f"{API_BASE_URL}{API_BASE_PREFIX}/auth/token", 
                data=data, headers=headers,
                timeout=10)

            st.session_state["token_val1"] = ""
            st.session_state["msg_val1"] = ""
            if response.status_code == 200:
                st.session_state["token_val1"] = response.json().get("access_token")
                st.session_state["msg_val1"] = f"✅ [HTTP {response.status_code}] concluído."
                return True
            elif response.status_code == 401:
                st.session_state["msg_val1"] = f"⚠️ [HTTP {response.status_code}] Sessão expirada ou não autorizada."
                return False
            else:
                st.session_state["msg_val1"] = f"⚠️ [HTTP {response.status_code}] Falha na chamada: {response.text}"
                return False

        except httpx.RequestError as exc:
            st.error(f"❌ Falha na chamada a API {exc.request.url}: {exc}")
            return False

def auth_user1() -> bool: 

    with st.spinner("Autenticando Usuário..."):
        try:
            data = {"username": username1, "password": password1}
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            token = st.session_state["token_val1"]
            if token:
                headers["Authorization"] = f"Bearer {token}"
            response = httpx.request("GET", f"{API_BASE_URL}{API_BASE_PREFIX}/auth/me", data=data, headers=headers)

            st.session_state["msg_val1"] = ""
            if response.status_code == 200:
                st.session_state["msg_val1"] = f"✅ [HTTP {response.status_code}] Autenticado. {response.json()}"
                return True
            else:
                st.session_state["msg_val1"] = f"⚠️ [HTTP {response.status_code}] Falha na chamada: {response.text}"
                return False

        except httpx.RequestError as exc:
            st.error(f"❌ Falha na chamada a API {exc.request.url}: {exc}")
            return False

with st.form("form1"):
    col1 = st.columns(2)
    with col1[0]:
        username1 = st.text_input("Usuário / E-mail", value="admin@admin.com")
    with col1[1]:
        password1 = st.text_input("Senha", type="password", value="admin123")

    btn_submit1C = st.form_submit_button(f"🔑 Autenticar Usuário (Solicitar Novo Token)", use_container_width=True)# , on_click=get_token)
    if btn_submit1C:
        if get_token1():
            auth_user1()

    btn_submit1A = st.form_submit_button(f"🔑 Solicitar Token (`POST {API_BASE_PREFIX}/auth/token`)", use_container_width=True)# , on_click=get_token)
    if btn_submit1A:
        get_token1()

    btn_submit1B = st.form_submit_button(f"🔑 Autenticar Usuário (`GET {API_BASE_PREFIX}/auth/me`)", use_container_width=True)# , on_click=get_token)
    if btn_submit1B:
        auth_user1()

    token1 = st.text_area(label="Token", height=130, key="token_val1")
    msg1 = st.text_area(label="Result", height=100, key="msg_val1")


# --- TESTE 2: ---
