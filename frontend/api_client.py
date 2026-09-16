import httpx
import streamlit as st
from logger import logger

API_BASE_URL = "http://localhost:8000"
API_BASE_PREFIX = "/api/v1"


class APIClient:


    def __init__(self, base_url: str = API_BASE_URL + API_BASE_PREFIX):
        """Construtor da classe"""
        self.base_url = base_url


    # ----- BASE PARA CHAMADAS API -----
    
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


    # ----- AUTENTICAÇÃO -----

    def login(self, username: str, password: str) -> dict | None:
        """Autentica o usuário usando OAuth2 Password Flow (Form Data)."""
        data = {"username": username, "password": password}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        response = self._request("POST", "/auth/token", data=data, headers=headers)
        
        if response.status_code == 200:
            
            # Grava o token no cofre da sessão do Streamlit
            token_data = response.json()
            st.session_state["token"] = token_data.get("access_token")
            
            # Busca e armazena os dados do usuário autenticado (nome, perfil, etc)
            user_response = self._request("GET", "/auth/me")
            if user_response.status_code == 200:
                st.session_state["user"] = user_response.json()
                st.session_state["authenticated"] = True
                logger.info(f"👤 Usuário conectado: {username}")
                
            return token_data

        logger.error(f"👤 Usuário não autenticado: {username}")
        return None

    def logout(self):
        """Limpa credenciais e dados de sessão."""
        st.session_state.pop("token", None)
        st.session_state.pop("user", None)
        st.session_state["authenticated"] = False
        logger.info("🔒 Sessão encerrada.")


    # ----- PLANO DE CONTAS -----

    def listar_plano_contas(self, limit: int = 50, offset: int = 0) -> dict:
        """Lista o plano de contas (retorna envelope paginado: items/total/limit/offset)."""
        resp = self._request(
            "GET", "/plano-contas", params={"limit": limit, "offset": offset}
        )
        return resp.json()

    def criar_plano_conta(self, payload: dict) -> dict:
        """Cria uma conta no plano de contas."""
        resp = self._request("POST", "/plano-contas", json=payload)
        return resp.json()

    def atualizar_plano_conta(self, id_: int, payload: dict) -> dict:
        """Atualiza uma conta do plano de contas."""
        resp = self._request("PUT", f"/plano-contas/{id_}", json=payload)
        return resp.json()

    def excluir_plano_conta(self, id_: int) -> bool:
        """Exclui (soft delete) uma conta do plano de contas. Retorna True se 204."""
        resp = self._request("DELETE", f"/plano-contas/{id_}")
        return resp.status_code == 204


    # ----- CONTA CORRENTE -----

    def listar_contas(self, limit: int = 50, offset: int = 0) -> dict:
        """Lista as contas correntes (retorna envelope paginado: items/total/limit/offset)."""
        resp = self._request(
            "GET", "/contas", params={"limit": limit, "offset": offset}
        )
        return resp.json()

    def criar_conta(self, payload: dict) -> dict:
        """Cria uma conta corrente."""
        resp = self._request("POST", "/contas", json=payload)
        return resp.json()

    def atualizar_conta(self, id_: int, payload: dict) -> dict:
        """Atualiza uma conta corrente."""
        resp = self._request("PUT", f"/contas/{id_}", json=payload)
        return resp.json()

    def excluir_conta(self, id_: int) -> bool:
        """Exclui (soft delete) uma conta corrente. Retorna True se 204."""
        resp = self._request("DELETE", f"/contas/{id_}")
        return resp.status_code == 204


    # ----- CONTAS BANCÁRIAS ----- 

    ver=""" 
    def listar_contas(self):
        response = self._request("GET", "/contas")
        response.raise_for_status()
        return response.json()

    def criar_conta(self, token: str, nome: str, tipo: str, saldo_inicial: float):
        payload = {
            "nome": nome,
            "tipo": tipo,
            "saldo_inicial": saldo_inicial
        }
        return self._request("POST", "/contas", json=payload, token=token)

    def atualizar_conta(self, token: str, conta_id: str, nome: str, tipo: str, saldo_inicial: float):
        payload = {
            "nome": nome,
            "tipo": tipo,
            "saldo_inicial": saldo_inicial
        }
        return self._request("PUT", f"/contas/{conta_id}", json=payload, token=token)

    def deletar_conta(self, token: str, conta_id: str):
        return self._request("DELETE", f"/contas/{conta_id}", token=token)
"""
