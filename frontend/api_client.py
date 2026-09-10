from typing import Any, Optional
import httpx
import streamlit as st

API_BASE_URL = "http://localhost:8000/api/v1"

class APIClient:
    @staticmethod
    def _get_headers() -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        token = st.session_state.get("access_token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    @classmethod
    def login(cls, username: str, password: str) -> bool:
        """Autentica o usuário na API FastAPI usando OAuth2 Password Flow."""
        try:
            response = httpx.post(
                f"{API_BASE_URL}/auth/token",
                data={"username": username, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                st.session_state["access_token"] = data["access_token"]
                
                # Busca dados do usuário logado
                me_response = httpx.get(
                    f"{API_BASE_URL}/auth/me",
                    headers={"Authorization": f"Bearer {data['access_token']}"},
                    timeout=10.0
                )
                if me_response.status_code == 200:
                    st.session_state["user"] = me_response.json()
                    st.session_state["authenticated"] = True
                    return True
            return False
        except httpx.RequestError:
            st.error("Erro de conexão com o servidor da API.")
            return False

    @classmethod
    def logout(cls) -> None:
        """Limpa as informações de autenticação da sessão."""
        st.session_state["access_token"] = None
        st.session_state["user"] = None
        st.session_state["authenticated"] = False

    @classmethod
    def get(cls, endpoint: str, params: Optional[dict] = None) -> Optional[Any]:
        try:
            response = httpx.get(
                f"{API_BASE_URL}{endpoint}",
                headers=cls._get_headers(),
                params=params,
                timeout=10.0
            )
            if response.status_code == 401:
                cls.logout()
                st.rerun()
            return response.json() if response.status_code == 200 else None
        except httpx.RequestError:
            return None
