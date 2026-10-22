from datetime import datetime, timedelta, timezone

import jwt
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import get_settings
from app.middleware.jwt import JWTMiddleware


def _app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(JWTMiddleware)

    @app.get("/protected")
    async def protected():
        return {"ok": True}

    return app


def _token(*, password_change_required: bool) -> str:
    settings = get_settings()
    return jwt.encode(
        {
            "sub": "00000000-0000-0000-0000-000000000001",
            "role": "internal_super_admin",
            "password_change_required": password_change_required,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def test_temporary_internal_admin_session_cannot_reach_workspace_routes():
    response = TestClient(_app()).get(
        "/protected",
        headers={"Authorization": f"Bearer {_token(password_change_required=True)}"},
    )
    assert response.status_code == 403
    assert response.json()["error"] == "Password change required"


def test_permanent_internal_admin_session_continues_to_workspace_routes():
    response = TestClient(_app()).get(
        "/protected",
        headers={"Authorization": f"Bearer {_token(password_change_required=False)}"},
    )
    assert response.status_code == 200
