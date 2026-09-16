
import pytest

from config import settings
from logger import setup_logger
from models import Usuario
from routers.auth import _login_attempts
from security import get_password_hash


@pytest.fixture(autouse=True)
def limpar_rate_limit():
    """O rate limit é global (módulo) — limpa entre testes."""
    _login_attempts.clear()
    yield
    _login_attempts.clear()


async def _criar_usuario(
    session, email="admin@admin.com", senha="admin123", ativo=True
):
    usuario = Usuario(
        nome="Administrador",
        email=email,
        senha_hash=get_password_hash(senha),
        ativo=ativo,
    )
    session.add(usuario)
    await session.commit()
    await session.refresh(usuario)
    return usuario


# ----- 401 padronizado: inexistente, inativo ou senha errada -----

@pytest.mark.asyncio
async def test_login_usuario_inexistente_retorna_401(client):
    resp = await client.post(
        "/api/v1/auth/token",
        data={"username": "naoexiste@teste.com", "password": "qualquer"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_senha_errada_retorna_401(client, session):
    await _criar_usuario(session)
    resp = await client.post(
        "/api/v1/auth/token",
        data={"username": "admin@admin.com", "password": "senhaerrada"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_usuario_inativo_retorna_401(client, session):
    await _criar_usuario(session, ativo=False)
    resp = await client.post(
        "/api/v1/auth/token",
        data={"username": "admin@admin.com", "password": "admin123"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_valido_retorna_token(client, session):
    await _criar_usuario(session)
    resp = await client.post(
        "/api/v1/auth/token",
        data={"username": "admin@admin.com", "password": "admin123"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


# ----- Rate limiting: 5 tentativas / 5 minutos -----

@pytest.mark.asyncio
async def test_rate_limit_bloqueia_apos_5_tentativas(client, session):
    await _criar_usuario(session)
    for _ in range(5):
        resp = await client.post(
            "/api/v1/auth/token",
            data={"username": "admin@admin.com", "password": "senhaerrada"},
        )
        assert resp.status_code == 401

    resp = await client.post(
        "/api/v1/auth/token",
        data={"username": "admin@admin.com", "password": "senhaerrada"},
    )
    assert resp.status_code == 429


# ----- /register protegido -----

@pytest.mark.asyncio
async def test_register_em_producao_retorna_404(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    resp = await client.post(
        "/api/v1/auth/register",
        json={"nome": "Novo", "email": "novo@teste.com", "senha": "senha123"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_register_em_dev_cria_usuario(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"nome": "Novo", "email": "novo@teste.com", "senha": "senha123"},
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_register_senha_curta_retorna_422(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"nome": "Novo", "email": "novo@teste.com", "senha": "123"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_email_duplicado_retorna_409(client, session):
    await _criar_usuario(session)
    resp = await client.post(
        "/api/v1/auth/register",
        json={"nome": "Outro", "email": "admin@admin.com", "senha": "senha123"},
    )
    assert resp.status_code == 409


# ----- /me exige token válido -----

@pytest.mark.asyncio
async def test_me_sem_token_retorna_401(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_com_token_retorna_usuario(client, session):
    await _criar_usuario(session)
    login = await client.post(
        "/api/v1/auth/token",
        data={"username": "admin@admin.com", "password": "admin123"},
    )
    token = login.json()["access_token"]

    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "admin@admin.com"


# ----- Logger: diagnose/backtrace desligados em produção -----

@pytest.mark.asyncio
async def test_setup_logger_roda_em_producao(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    setup_logger()  # não deve lançar exceção
    assert True


@pytest.mark.asyncio
async def test_setup_logger_roda_em_dev(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    setup_logger()
    assert True