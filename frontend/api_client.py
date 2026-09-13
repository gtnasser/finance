from logger import logger
#from typing import Any, Optional
import httpx
import streamlit as st

API_BASE_URL = "http://localhost:8000"
API_BASE_PREFIX = "/api/v1"


class APIClient:
    def __init__(self, base_url: str = API_BASE_URL+API_BASE_PREFIX):
        """Construtor da classe"""
        self.base_url = base_url

    @property
    def token(self) -> str | None:
        """Busca dinamicamente o token JWT salvo na sessão do Streamlit."""
        return st.session_state.get("token")

    def _get_headers(self) -> dict:
        """Monta os cabeçalhos das requisições injetando o Bearer Token se disponível."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """
        Interceptador centralizador de requisições HTTP.
        Grava logs de saída, tempo de resposta e falhas no Loguru.
        Trata a expiração de token (401) e força o logout com st.rerun().
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        # Mescla os headers padrões com possíveis headers customizados passados nos kwargs
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))

        logger.info(f"🌐 [HTTP OUT] {method.upper()} -> {endpoint}")

        try:
            response = httpx.request(method, url, headers=headers, **kwargs)
            # Trata token expirado/inválido de forma centralizada
            if response.status_code == 401:
                logger.warning(
                    "⚠️ Sessão expirada ou não autorizada (401). Realizando logout."
                )
                self.logout()
                st.rerun()

            if response.is_error:
                logger.warning(
                    f"⚠️ [HTTP {response.status_code}] Falha na chamada {method.upper()} {endpoint}: {response.text}"
                )
            else:
                logger.success(
                    f"✅ [HTTP {response.status_code}] {method.upper()} {endpoint} concluído."
                )
            return response

        except httpx.RequestError as exc:
            logger.error(
                f"❌ [HTTP ERROR] Falha de conexão ao acessar {exc.request.url}: {exc}"
            )
            raise exc


    # --- MÉTODOS DE AUTENTICAÇÃO ---

    def login(self, username: str, password: str) -> dict | None:
        """Autentica o usuário usando OAuth2 Password Flow (Form Data)."""
        data = {"username": username, "password": password}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        response = self._request("POST", "/auth/token", data=data, headers=headers)
        
        if response.status_code == 200:
            token_data = response.json()
            
            # Grava o token no cofre da sessão do Streamlit
            st.session_state["token"] = token_data.get("access_token")
            
            # Busca e armazena os dados do usuário autenticado (nome, perfil, etc)
            user_response = self._request("GET", "/auth/me")
            if user_response.status_code == 200:
                st.session_state["user"] = user_response.json()
                logger.info(f"👤 Usuário conectado: {username}")
                
            return token_data

        logger.error(f"👤 Usuário não autenticado: {username}")
        return None

    def logout(self):
        """Limpa credenciais e dados de sessão."""
        st.session_state.pop("token", None)
        st.session_state.pop("user", None)
        logger.info("🔒 Sessão encerrada.")

    # --- MÉTODOS DE NEGÓCIO (EXEMPLOS...) ---

    def get_titulos(self) -> list[dict]:
        """Obtém a lista de títulos a pagar."""
        response = self._request("GET", "/titulos/")
        return response.json() if response.status_code == 200 else []

    def criar_titulo(self, dados: dict) -> dict | None:
        """Cadastra um novo título a pagar."""
        response = self._request("POST", "/titulos/", json=dados)
        return response.json() if response.status_code == 201 else None

