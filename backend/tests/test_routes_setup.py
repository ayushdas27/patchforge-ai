import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_setup_status_endpoint():
    response = client.get("/api/setup/status")
    assert response.status_code == 200
    data = response.json()
    assert "configured" in data
    assert "base_url" in data
    assert "model" in data
    assert "key_status" in data

@patch("app.services.nebius_client.OpenAI")
def test_setup_test_connection_mocked(mock_openai):
    mock_inst = MagicMock()
    mock_openai.return_value = mock_inst
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = "pong"
    mock_inst.chat.completions.create.return_value = mock_resp

    with patch("app.config.settings.nebius_api_key", "sk-neb-test-token-12345"):
        response = client.post("/api/setup/test-connection", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["response_sample"] == "pong"
