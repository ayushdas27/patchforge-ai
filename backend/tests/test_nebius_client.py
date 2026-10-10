import pytest
from unittest.mock import MagicMock, patch
from app.services.nebius_client import NebiusClient
from app.security.redaction import redact_secrets, mask_api_key

def test_mask_api_key():
    assert mask_api_key(None) == "Not Set"
    assert mask_api_key("") == "Not Set"
    assert mask_api_key("12345") == "****"
    assert mask_api_key("sk-neb-abcdef1234567890") == "sk-n...7890"

def test_redact_secrets():
    raw_log = "Error with Authorization: Bearer sk-neb-supersecretkey12345 in call"
    redacted = redact_secrets(raw_log)
    assert "sk-neb-supersecretkey12345" not in redacted
    assert "[REDACTED]" in redacted

def test_nebius_client_missing_key():
    client = NebiusClient(api_key="")
    result = client.test_connection()
    assert result["success"] is False
    assert result["key_status"] == "Missing"
    assert "Missing NEBIUS_API_KEY" in result["error"]

@patch("app.services.nebius_client.OpenAI")
def test_nebius_client_success_mock(mock_openai):
    mock_instance = MagicMock()
    mock_openai.return_value = mock_instance
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = "pong"
    mock_instance.chat.completions.create.return_value = mock_resp

    client = NebiusClient(api_key="sk-neb-mockkey-for-unit-tests-12345")
    result = client.test_connection()
    assert result["success"] is True
    assert result["response_sample"] == "pong"
    assert "sk-n...2345" in result["key_status"]
