from types import SimpleNamespace

import pytest

from app.core.exceptions import AppException
from app.core import recaptcha


@pytest.mark.asyncio
async def test_recaptcha_rejects_missing_server_configuration(monkeypatch):
    monkeypatch.setattr(recaptcha, "get_settings", lambda: SimpleNamespace(
        app_env="production", recaptcha_secret_key="", recaptcha_verify_url="https://example.invalid",
        recaptcha_expected_hostname="consultant.example.com",
    ))
    with pytest.raises(AppException) as error:
        await recaptcha.verify_recaptcha("token")
    assert error.value.status_code == 503


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [
    {"success": False, "error-codes": ["timeout-or-duplicate"]},
    {"success": True, "hostname": "wrong.example.com"},
])
async def test_recaptcha_rejects_invalid_expired_or_wrong_host_tokens(monkeypatch, payload):
    class Response:
        def raise_for_status(self):
            return None
        def json(self):
            return payload
    class Client:
        async def __aenter__(self): return self
        async def __aexit__(self, *_args): return None
        async def post(self, *_args, **_kwargs): return Response()
    monkeypatch.setattr(recaptcha, "get_settings", lambda: SimpleNamespace(
        app_env="production", recaptcha_secret_key="secret", recaptcha_verify_url="https://verify.example.com",
        recaptcha_expected_hostname="consultant.example.com",
    ))
    monkeypatch.setattr(recaptcha.httpx, "AsyncClient", lambda **_kwargs: Client())
    with pytest.raises(AppException) as error:
        await recaptcha.verify_recaptcha("token")
    assert error.value.status_code == 422


@pytest.mark.asyncio
async def test_recaptcha_accepts_server_verified_token_for_expected_host(monkeypatch):
    captured = {}
    class Response:
        def raise_for_status(self): return None
        def json(self): return {"success": True, "hostname": "consultant.example.com"}
    class Client:
        async def __aenter__(self): return self
        async def __aexit__(self, *_args): return None
        async def post(self, url, **kwargs):
            captured.update(url=url, data=kwargs["data"])
            return Response()
    monkeypatch.setattr(recaptcha, "get_settings", lambda: SimpleNamespace(
        app_env="production", recaptcha_secret_key="secret", recaptcha_verify_url="https://verify.example.com",
        recaptcha_expected_hostname="consultant.example.com",
    ))
    monkeypatch.setattr(recaptcha.httpx, "AsyncClient", lambda **_kwargs: Client())
    await recaptcha.verify_recaptcha("safe-token", "192.0.2.1")
    assert captured == {"url": "https://verify.example.com", "data": {
        "secret": "secret", "response": "safe-token", "remoteip": "192.0.2.1",
    }}
