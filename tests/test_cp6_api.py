"""Contratos reais FastAPI + SQLite temporário (sem mock de persistência)."""
import sqlite3
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.core.config import Settings
from app.core.security import token_digest
from app.main import create_app


@pytest.fixture
def database(tmp_path):
    return tmp_path / "chat.sqlite3"


@pytest.fixture
def client(database):
    with TestClient(create_app(Settings(database))) as client:
        yield client


def account(client, name="alice"):
    credentials = {"usuario": name, "senha": "senha-ficticia-cp6"}
    assert client.post("/auth/register", json=credentials).status_code == 201
    response = client.post("/auth/login", json=credentials)
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create(client, headers):
    response = client.post("/conversas", headers=headers, json={})
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.parametrize("method,path,payload", [
    ("get", "/conversas", None), ("post", "/conversas", {}),
    ("get", "/conversas/1", None), ("post", "/conversas/1/mensagens", {"conteudo": "Olá"}),
    ("get", "/auth/me", None), ("post", "/auth/logout", None),
])
def test_every_protected_route_requires_token(client, method, path, payload):
    response = client.request(method, path, json=payload)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert client.request(method, path, json=payload,
                          headers={"Authorization": "Bearer invalid"}).status_code == 401


def test_registration_login_and_revocation(client, database):
    headers = account(client)
    assert client.get("/auth/me", headers=headers).json()["usuario"] == "alice"
    assert client.post("/auth/register", json={"usuario": "ALICE", "senha": "abcdefgh"}).status_code == 409
    for username in ["alice", "nobody"]:
        assert client.post("/auth/login", json={"usuario": username, "senha": "wrongpass"}).status_code == 401
    with sqlite3.connect(database) as db:
        stored = db.execute("SELECT password_hash FROM users").fetchone()[0]
        token_hash = db.execute("SELECT token_hash FROM sessions").fetchone()[0]
    assert stored.startswith("pbkdf2_sha256$")
    assert "senha-ficticia-cp6" not in stored
    assert token_hash == token_digest(headers["Authorization"][7:])
    assert client.post("/auth/logout", headers=headers).status_code == 204
    assert client.get("/conversas", headers=headers).status_code == 401


def test_expired_session(client, database):
    headers = account(client)
    with sqlite3.connect(database) as db:
        db.execute("UPDATE sessions SET expires_at = ?", (time.time() - 1,))
    assert client.get("/conversas", headers=headers).status_code == 401


def test_multiple_conversations_and_cross_account_isolation(client):
    alice = account(client)
    bob = account(client, "bob")
    first, second = create(client, alice), create(client, alice)
    response = client.post(f"/conversas/{first}/mensagens", headers=alice, json={"conteudo": "O que é API?"})
    assert response.status_code == 201
    assert response.json()["mensagem_usuario"]["papel"] == "user"
    assert response.json()["resposta"]["papel"] == "assistant"
    assert response.json()["modelo"] == "motor-assistant-rules-v1"
    assert len(client.get(f"/conversas/{first}", headers=alice).json()["mensagens"]) == 2
    assert client.get(f"/conversas/{second}", headers=alice).json()["mensagens"] == []
    assert len(client.get("/conversas", headers=alice).json()) == 2
    assert client.get("/conversas", headers=bob).json() == []
    for id_ in [first, 9999]:
        assert client.get(f"/conversas/{id_}", headers=bob).status_code == 404
        assert client.post(f"/conversas/{id_}/mensagens", headers=bob,
                           json={"conteudo": "Tentar acesso"}).status_code == 404
    assert client.post(f"/conversas/{first}/mensagens?user_id=1", headers=bob,
                       json={"conteudo": "Spoof", "user_id": 1}).status_code == 422
    assert client.get(f"/conversas/{first}?user_id=1", headers={**bob, "X-User-ID": "1"}).status_code == 404


@pytest.mark.parametrize("payload", [{"conteudo": ""}, {"conteudo": "   "},
    {"conteudo": "x" * 4001}, {}, {"conteudo": 12}, {"conteudo": "x", "role": "assistant"}])
def test_invalid_message_is_422_and_does_not_persist(client, payload):
    headers = account(client)
    conversation_id = create(client, headers)
    assert client.post(f"/conversas/{conversation_id}/mensagens", headers=headers, json=payload).status_code == 422
    assert client.get(f"/conversas/{conversation_id}", headers=headers).json()["mensagens"] == []


@pytest.mark.parametrize("credentials", [
    {"usuario": "ab", "senha": "abcdefgh"}, {"usuario": "a b", "senha": "abcdefgh"},
    {"usuario": "alice", "senha": "short"}, {"usuario": "alice", "senha": "x" * 129},
    {"usuario": "alice", "senha": "abcdefgh", "id": 1},
])
def test_invalid_registration(client, credentials):
    assert client.post("/auth/register", json=credentials).status_code == 422


def test_persistence_after_application_restart(database):
    settings = Settings(database)
    with TestClient(create_app(settings)) as first:
        headers = account(first)
        conversation_id = create(first, headers)
        assert first.post(f"/conversas/{conversation_id}/mensagens", headers=headers,
                          json={"conteudo": "Persistência"}).status_code == 201
    with TestClient(create_app(settings)) as restarted:
        detail = restarted.get(f"/conversas/{conversation_id}", headers=headers).json()
        assert len(detail["mensagens"]) == 2
        assert detail["titulo"] == "Persistência"
        assert restarted.post(f"/conversas/{conversation_id}/mensagens", headers=headers,
                              json={"conteudo": "Continuar"}).status_code == 201
        assert len(restarted.get(f"/conversas/{conversation_id}", headers=headers).json()["mensagens"]) == 4


def test_provider_failure_is_503_without_partial_messages(database):
    with TestClient(create_app(Settings(database, llm_provider="unavailable"))) as client:
        headers = account(client)
        conversation_id = create(client, headers)
        response = client.post(f"/conversas/{conversation_id}/mensagens", headers=headers,
                               json={"conteudo": "Olá"})
        assert response.status_code == 503
        assert "indisponível" in response.json()["detail"]
        assert client.get(f"/conversas/{conversation_id}", headers=headers).json()["mensagens"] == []
        assert client.get("/health").json()["status"] == "degraded"


def test_pair_is_atomic_when_second_insert_fails(client, database):
    headers = account(client)
    conversation_id = create(client, headers)
    with sqlite3.connect(database) as db:
        db.executescript("""CREATE TRIGGER fail_answer BEFORE INSERT ON messages
            WHEN NEW.role = 'assistant' BEGIN SELECT RAISE(ABORT, 'forced test failure'); END;""")
    assert client.post(f"/conversas/{conversation_id}/mensagens", headers=headers,
                       json={"conteudo": "Mensagem"}).status_code == 503
    assert client.get(f"/conversas/{conversation_id}", headers=headers).json()["mensagens"] == []


def test_health_docs_and_schema(client):
    assert client.get("/health").json() == {"status": "ok", "provider": "simulated", "modelo": "motor-assistant-rules-v1"}
    assert client.get("/docs").status_code == 200
    schema = client.get("/openapi.json").json()
    for path in schema["paths"].values():
        for operation in path.values():
            assert operation["summary"]
    assert "HTTPBearer" in schema["components"]["securitySchemes"]


def test_echo_provider_switch(database):
    with TestClient(create_app(Settings(database, llm_provider="echo"))) as client:
        headers = account(client)
        conversation_id = create(client, headers)
        result = client.post(f"/conversas/{conversation_id}/mensagens", headers=headers,
                             json={"conteudo": "Olá"}).json()
        assert result["modelo"] == "echo-v1"
        assert result["resposta"]["conteudo"] == "[Bot eco simulado] Você escreveu: Olá"
