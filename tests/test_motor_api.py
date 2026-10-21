"""Integração HTTP das sprints com dados temporários e regras originais."""
import shutil
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def settings(tmp_path):
    data = tmp_path / "motor"
    data.mkdir()
    for name in ("equipments.json", "telemetry_history.csv", "event_history.csv"):
        shutil.copy2(ROOT / "data" / name, data / name)
    return Settings(tmp_path / "chat.sqlite3", motor_data_dir=data)


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as client:
        yield client


def login(client, username="motor_aluno"):
    payload = {"usuario": username, "senha": "senha-ficticia-cp6"}
    assert client.post("/auth/register", json=payload).status_code == 201
    token = client.post("/auth/login", json=payload).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def equipment_payload():
    return {"tag": "QA-099", "modelo": "W22", "fabricante": "WEG", "potencia": 15,
        "unidade_potencia": "kW", "tensao": 380, "corrente_nominal": 28.5,
        "rotacao_nominal": 1750, "local_instalacao": "Área de testes",
        "status_operacional": "Operacional", "observacoes": "Cadastro fictício", "confirmar": True}


@pytest.mark.parametrize("method,path", [
    ("GET", "/motor/equipamentos"), ("POST", "/motor/equipamentos"), ("GET", "/motor/painel"),
    ("GET", "/motor/equipamentos/MTR-001"), ("POST", "/motor/equipamentos/MTR-001/demo"),
    ("POST", "/motor/equipamentos/MTR-001/leituras"), ("GET", "/motor/equipamentos/MTR-001/sensores"),
])
def test_motor_routes_require_authentication(client, method, path):
    assert client.request(method, path, json=equipment_payload() if path.endswith("equipamentos") else None).status_code == 401


def test_cadastro_confirmation_uniqueness_and_shared_fleet(client):
    first, second = login(client), login(client, "outro_aluno")
    payload = equipment_payload()
    assert client.post("/motor/equipamentos", headers=first, json={**payload, "confirmar": False}).status_code == 422
    assert client.post("/motor/equipamentos", headers=first, json=payload).status_code == 201
    assert client.post("/motor/equipamentos", headers=first, json={**payload, "tag": "qa-099"}).status_code == 409
    assert any(item["tag"] == "QA-099" for item in client.get("/motor/equipamentos", headers=second).json())
    assert client.get("/conversas", headers=second).json() == []
    assert client.post("/motor/equipamentos", headers=first, json={**payload, "tag": "../bad"}).status_code == 422
    assert client.post("/motor/equipamentos", headers=first, json={**payload, "potencia": 0}).status_code == 422


def test_demo_transitions_are_consistent_and_reruns_do_not_duplicate_events(client, settings):
    headers = login(client)
    data_dir = settings.motor_data_dir
    originals = {path.name: path.read_bytes() for path in data_dir.iterdir() if path.is_file()}
    first = client.get("/motor/painel", headers=headers).json()
    second = client.get("/motor/painel", headers=headers).json()
    assert first["snapshots"] == second["snapshots"]
    before = len(first["eventos"])
    critical = client.post("/motor/equipamentos/MTR-001/demo", headers=headers)
    assert critical.status_code == 201
    snapshot = critical.json()["snapshot"]
    assert snapshot["status"] == "Crítico"
    assert snapshot["reading"]["vibracao_mm_s"] == 7.8
    detail = client.get("/motor/equipamentos/MTR-001", headers=headers).json()
    assert detail["snapshot"]["inference_id"] == snapshot["inference_id"]
    for _ in range(2):
        panel = client.get("/motor/painel", headers=headers).json()
        assert len(panel["eventos"]) == before + 1
    healthy = client.post("/motor/equipamentos/MTR-001/demo", headers=headers).json()["snapshot"]
    assert healthy["status"] == "Saudável"
    assert healthy["reading"]["vibracao_mm_s"] == 3.2
    assert len(client.get("/motor/painel", headers=headers).json()["eventos"]) == before + 2
    assert all((data_dir / name).read_bytes() == content for name, content in originals.items())


def test_equipment_reading_and_history_survive_restart(settings):
    with TestClient(create_app(settings)) as client:
        headers = login(client)
        assert client.post("/motor/equipamentos", headers=headers, json=equipment_payload()).status_code == 201
        result = client.post("/motor/equipamentos/QA-099/leituras", headers=headers)
        assert result.status_code == 201
        reading_id = result.json()["snapshot"]["reading_id"]
    with TestClient(create_app(settings)) as restarted:
        detail = restarted.get("/motor/equipamentos/QA-099", headers=headers)
        assert detail.status_code == 200
        assert detail.json()["snapshot"]["reading_id"] == reading_id
        assert any(item["reading_id"] == reading_id for item in detail.json()["historico"])


def test_chat_uses_same_motor_snapshot_as_dashboard(client):
    headers = login(client)
    snapshot = client.post("/motor/equipamentos/MTR-001/demo", headers=headers).json()["snapshot"]
    conversation = client.post("/conversas", headers=headers, json={}).json()["id"]
    result = client.post(f"/conversas/{conversation}/mensagens", headers=headers,
                         json={"conteudo": "Como está o MTR-001?"})
    assert result.status_code == 201
    answer = result.json()["resposta"]["conteudo"]
    for field in ("tag", "status", "source", "timestamp", "reading_id"):
        assert str(snapshot[field]) in answer
    assert "sem LLM" in answer
    other = login(client, "outro_usuario")
    assert client.get(f"/conversas/{conversation}", headers=other).status_code == 404


def test_raw_sensor_conversion_and_missing_equipment(client):
    headers = login(client)
    rows = client.get("/motor/equipamentos/MTR-001/sensores", headers=headers).json()["tabela"]
    assert [row["sensor"] for row in rows] == ["Temperatura", "Corrente", "Rotação"]
    assert all("1023" in row["formula"] for row in rows)
    assert client.get("/motor/equipamentos/INEXISTENTE", headers=headers).status_code == 404
    assert client.post("/motor/equipamentos/INEXISTENTE/demo", headers=headers).status_code == 404


def test_corrupt_motor_source_fails_closed_without_overwriting(client, settings):
    headers = login(client)
    source = settings.motor_data_dir / "equipments.json"
    source.write_text("invalid-json", encoding="utf-8")
    response = client.get("/motor/equipamentos", headers=headers)
    assert response.status_code == 503
    assert source.read_text(encoding="utf-8") == "invalid-json"


def test_frontend_does_not_import_backend_or_access_persistence():
    import ast
    for path in (ROOT / "frontend").rglob("*.py"):
        if ".venv" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith(("src", "app", "sqlite3")), path
            if isinstance(node, ast.Import):
                assert not any(alias.name.startswith(("src", "sqlite3", "backend")) for alias in node.names), path
