import pytest

from models import Usuario
from security import get_password_hash

# ----- Helpers -----

async def _criar_usuario(session, email="admin@admin.com", senha="admin123"):
    usuario = Usuario(
        nome="Administrador",
        email=email,
        senha_hash=get_password_hash(senha),
        ativo=True,
    )
    session.add(usuario)
    await session.commit()
    await session.refresh(usuario)
    return usuario

async def _auth_headers(client, session):
    """Cria um usuário e retorna os headers com Bearer token."""
    await _criar_usuario(session)
    login = await client.post(
        "/api/v1/auth/token",
        data={"username": "admin@admin.com", "password": "admin123"},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def _plano_payload(**kwargs):
    payload = {
        "codigo": "1",
        "descricao": "Ativo",
        "tipo": "ATIVO",
        "natureza": "DEVEDORA",
        "sintetica": True,
        "parent_id": None,
        "ativo": True,
    }
    payload.update(kwargs)
    return payload

def _conta_payload(**kwargs):
    payload = {
        "nome": "Conta Principal",
        "banco": "001",
        "agencia": "1234",
        "numero": "56789-0",
        "tipo": "CORRENTE",
        "moeda": "BRL",
        "saldo_inicial": "0.00",
        "data_saldo_inicial": "2026-01-01",
        "plano_conta_id": None,
        "ativo": True,
    }
    payload.update(kwargs)
    return payload

# ----- Autenticação obrigatória -----

@pytest.mark.asyncio
async def test_crud_exige_token(client):
    resp = await client.get("/api/v1/plano-contas")
    assert resp.status_code == 401

    resp = await client.post("/api/v1/plano-contas", json=_plano_payload())
    assert resp.status_code == 401

# ----- Plano de contas: criar -----

@pytest.mark.asyncio
async def test_criar_plano_conta(client, session):
    headers = await _auth_headers(client, session)
    resp = await client.post(
        "/api/v1/plano-contas", json=_plano_payload(), headers=headers
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] is not None
    assert data["codigo"] == "1"

@pytest.mark.asyncio
async def test_criar_plano_conta_duplicado_retorna_409(client, session):
    headers = await _auth_headers(client, session)
    await client.post("/api/v1/plano-contas", json=_plano_payload(), headers=headers)
    resp = await client.post(
        "/api/v1/plano-contas", json=_plano_payload(), headers=headers
    )
    assert resp.status_code == 409

@pytest.mark.asyncio
async def test_criar_plano_conta_invalido_retorna_422(client, session):
    headers = await _auth_headers(client, session)
    resp = await client.post(
        "/api/v1/plano-contas", json={"codigo": "1"}, headers=headers
    )
    assert resp.status_code == 422

# ----- Plano de contas: listar -----

@pytest.mark.asyncio
async def test_listar_plano_contas_vazio(client, session):
    headers = await _auth_headers(client, session)
    resp = await client.get("/api/v1/plano-contas", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["items"] == []

@pytest.mark.asyncio
async def test_listar_plano_contas_com_itens(client, session):
    headers = await _auth_headers(client, session)
    await client.post("/api/v1/plano-contas", json=_plano_payload(), headers=headers)
    await client.post(
        "/api/v1/plano-contas",
        json=_plano_payload(codigo="2", descricao="Passivo", natureza="CREDORA"),
        headers=headers,
    )
    resp = await client.get("/api/v1/plano-contas", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 2

# ----- Plano de contas: obter por id -----

@pytest.mark.asyncio
async def test_obter_plano_conta_por_id(client, session):
    headers = await _auth_headers(client, session)
    criado = await client.post(
        "/api/v1/plano-contas", json=_plano_payload(), headers=headers
    )
    id_ = criado.json()["id"]

    resp = await client.get(f"/api/v1/plano-contas/{id_}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["codigo"] == "1"

@pytest.mark.asyncio
async def test_obter_plano_conta_inexistente_retorna_404(client, session):
    headers = await _auth_headers(client, session)
    resp = await client.get("/api/v1/plano-contas/9999", headers=headers)
    assert resp.status_code == 404

# ----- Plano de contas: atualizar -----

@pytest.mark.asyncio
async def test_atualizar_plano_conta(client, session):
    headers = await _auth_headers(client, session)
    criado = await client.post(
        "/api/v1/plano-contas", json=_plano_payload(), headers=headers
    )
    id_ = criado.json()["id"]

    resp = await client.put(
        f"/api/v1/plano-contas/{id_}",
        json={"descricao": "Ativo Total"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["descricao"] == "Ativo Total"

@pytest.mark.asyncio
async def test_atualizar_plano_conta_para_ciclo_retorna_422(client, session):
    headers = await _auth_headers(client, session)
    raiz = await client.post(
        "/api/v1/plano-contas", json=_plano_payload(), headers=headers
    )
    filho = await client.post(
        "/api/v1/plano-contas",
        json=_plano_payload(
            codigo="1.1", descricao="Filho", parent_id=raiz.json()["id"]
        ),
        headers=headers,
    )

    # Mover a raiz para baixo do filho cria ciclo na hierarquia
    resp = await client.put(
        f"/api/v1/plano-contas/{raiz.json()['id']}",
        json={"parent_id": filho.json()["id"]},
        headers=headers,
    )
    assert resp.status_code == 422

# ----- Plano de contas: excluir -----

@pytest.mark.asyncio
async def test_excluir_plano_conta(client, session):
    headers = await _auth_headers(client, session)
    criado = await client.post(
        "/api/v1/plano-contas", json=_plano_payload(), headers=headers
    )
    id_ = criado.json()["id"]

    resp = await client.delete(f"/api/v1/plano-contas/{id_}", headers=headers)
    assert resp.status_code == 204

    # Some da listagem (soft delete)
    lista = await client.get("/api/v1/plano-contas", headers=headers)
    assert lista.json()["items"] == []

@pytest.mark.asyncio
async def test_excluir_plano_conta_com_filhos_retorna_422(client, session):
    headers = await _auth_headers(client, session)
    raiz = await client.post(
        "/api/v1/plano-contas", json=_plano_payload(), headers=headers
    )
    await client.post(
        "/api/v1/plano-contas",
        json=_plano_payload(
            codigo="1.1", descricao="Filho", parent_id=raiz.json()["id"]
        ),
        headers=headers,
    )

    resp = await client.delete(
        f"/api/v1/plano-contas/{raiz.json()['id']}", headers=headers
    )
    assert resp.status_code == 422

# ----- Conta corrente: criar -----

@pytest.mark.asyncio
async def test_criar_conta_corrente(client, session):
    headers = await _auth_headers(client, session)
    plano = await client.post(
        "/api/v1/plano-contas",
        json=_plano_payload(sintetica=False),
        headers=headers,
    )
    resp = await client.post(
        "/api/v1/contas",
        json=_conta_payload(plano_conta_id=plano.json()["id"]),
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["banco"] == "001"

@pytest.mark.asyncio
async def test_criar_conta_corrente_em_plano_sintetico_retorna_422(client, session):
    headers = await _auth_headers(client, session)
    plano = await client.post(
        "/api/v1/plano-contas",
        json=_plano_payload(sintetica=True),
        headers=headers,
    )
    resp = await client.post(
        "/api/v1/contas",
        json=_conta_payload(plano_conta_id=plano.json()["id"]),
        headers=headers,
    )
    assert resp.status_code == 422

@pytest.mark.asyncio
async def test_criar_conta_corrente_duplicada_retorna_409(client, session):
    headers = await _auth_headers(client, session)
    plano = await client.post(
        "/api/v1/plano-contas",
        json=_plano_payload(sintetica=False),
        headers=headers,
    )
    payload = _conta_payload(plano_conta_id=plano.json()["id"])
    await client.post("/api/v1/contas", json=payload, headers=headers)
    resp = await client.post("/api/v1/contas", json=payload, headers=headers)
    assert resp.status_code == 409

# ----- Conta corrente: listar e obter -----

@pytest.mark.asyncio
async def test_listar_contas_correntes(client, session):
    headers = await _auth_headers(client, session)
    plano = await client.post(
        "/api/v1/plano-contas",
        json=_plano_payload(sintetica=False),
        headers=headers,
    )
    await client.post(
        "/api/v1/contas",
        json=_conta_payload(plano_conta_id=plano.json()["id"]),
        headers=headers,
    )
    resp = await client.get("/api/v1/contas", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 1

@pytest.mark.asyncio
async def test_obter_conta_corrente_por_id(client, session):
    headers = await _auth_headers(client, session)
    plano = await client.post(
        "/api/v1/plano-contas",
        json=_plano_payload(sintetica=False),
        headers=headers,
    )
    criada = await client.post(
        "/api/v1/contas",
        json=_conta_payload(plano_conta_id=plano.json()["id"]),
        headers=headers,
    )
    resp = await client.get(f"/api/v1/contas/{criada.json()['id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["numero"] == "56789-0"

# ----- Conta corrente: atualizar -----

@pytest.mark.asyncio
async def test_atualizar_conta_corrente(client, session):
    headers = await _auth_headers(client, session)
    plano = await client.post(
        "/api/v1/plano-contas",
        json=_plano_payload(sintetica=False),
        headers=headers,
    )
    criada = await client.post(
        "/api/v1/contas",
        json=_conta_payload(plano_conta_id=plano.json()["id"]),
        headers=headers,
    )
    resp = await client.put(
        f"/api/v1/contas/{criada.json()['id']}",
        json={"nome": "Conta PJ"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["nome"] == "Conta PJ"
