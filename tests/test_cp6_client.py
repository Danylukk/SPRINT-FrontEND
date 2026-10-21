import importlib.util
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

path = Path(__file__).resolve().parents[1] / "frontend/services/api_client.py"
spec = importlib.util.spec_from_file_location("cp6_api_client", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
APIClient, APIError = module.APIClient, module.APIError


def test_http_is_centralized_with_timeout_and_bearer():
    response = Mock(ok=True, status_code=200)
    response.json.return_value = []
    with patch.object(module.requests, "request", return_value=response) as request:
        assert APIClient("opaque-token", "http://example.test", 3).list_conversations() == []
        request.assert_called_once_with("GET", "http://example.test/conversas", json=None,
                                        headers={"Authorization": "Bearer opaque-token"}, timeout=3)


@pytest.mark.parametrize("status", [401, 404, 409, 422, 503, 500])
def test_errors_are_friendly_and_hide_internal_body(status):
    response = Mock(ok=False, status_code=status, text="SECRET traceback")
    with patch.object(module.requests, "request", return_value=response):
        with pytest.raises(APIError) as error:
            APIClient().list_conversations()
        assert error.value.status_code == status
        assert "SECRET" not in str(error.value)
        assert "traceback" not in str(error.value)


@pytest.mark.parametrize("error", [requests.Timeout(), requests.ConnectionError(), requests.RequestException()])
def test_network_errors_do_not_retry_writes(error):
    with patch.object(module.requests, "request", side_effect=error) as request:
        with pytest.raises(APIError):
            APIClient().send_message(1, "Olá")
        assert request.call_count == 1


def test_invalid_json_is_friendly():
    response = Mock(ok=True, status_code=200)
    response.json.side_effect = ValueError("invalid")
    with patch.object(module.requests, "request", return_value=response):
        with pytest.raises(APIError, match="resposta inválida"):
            APIClient().health()
