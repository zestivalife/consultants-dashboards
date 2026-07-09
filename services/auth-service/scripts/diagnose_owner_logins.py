#!/usr/bin/env python3
"""Runtime diagnostics for production owner-account login issues.

Run this inside the auth-service container/runtime:
    python scripts/diagnose_owner_logins.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

import httpx
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.config import get_settings
from app.core.security import verify_password

OWNER_USERS = [
    {"email": "lalitppaunikar26@gmail.com", "password": "Lalit@123"},
    {"email": "zestivapriyanshi@gmail.com", "password": "Priyanshi@123"},
]
LOGIN_URL = "https://api.nuetra.in/api/v1/auth/login"


def summarize_database_url(database_url: str) -> dict[str, str | bool]:
    parsed = urlsplit(database_url)
    return {
        "scheme": parsed.scheme,
        "host": parsed.hostname or "",
        "port": str(parsed.port or ""),
        "database": parsed.path.lstrip("/"),
        "username_present": bool(parsed.username),
        "password_present": bool(parsed.password),
    }


async def fetch_db_state() -> dict:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)

    try:
        async with engine.connect() as conn:
            has_is_active = bool(
                await conn.scalar(
                    sa.text(
                        """
                        SELECT EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_name = 'users'
                              AND column_name = 'is_active'
                        )
                        """
                    )
                )
            )

            alembic_head = await conn.scalar(sa.text("SELECT version_num FROM alembic_version LIMIT 1"))
            superuser_row = await conn.execute(
                sa.text("SELECT id, name FROM roles WHERE name = 'superuser' LIMIT 1")
            )
            superuser = superuser_row.mappings().first()

            user_state = []
            for owner in OWNER_USERS:
                select_sql = """
                    SELECT
                        u.id,
                        u.email,
                        u.role_id,
                        r.name AS role_name,
                        u.is_verified,
                        u.failed_login_attempts,
                        u.lock_until,
                        u.password_hash
                        {is_active_select}
                    FROM users u
                    LEFT JOIN roles r ON r.id = u.role_id
                    WHERE u.email = :email
                    LIMIT 1
                """.format(
                    is_active_select=", u.is_active" if has_is_active else ""
                )
                result = await conn.execute(sa.text(select_sql), {"email": owner["email"]})
                row = result.mappings().first()

                if row is None:
                    user_state.append(
                        {
                            "email": owner["email"],
                            "exists": False,
                            "password_verifies": False,
                        }
                    )
                    continue

                password_hash = row["password_hash"]
                user_state.append(
                    {
                        "email": row["email"],
                        "exists": True,
                        "id": str(row["id"]),
                        "role_id": str(row["role_id"]) if row["role_id"] else None,
                        "role_name": row["role_name"],
                        "is_verified": bool(row["is_verified"]),
                        "is_active": bool(row["is_active"]) if has_is_active else "column-missing",
                        "failed_login_attempts": int(row["failed_login_attempts"] or 0),
                        "lock_until": row["lock_until"].isoformat() if row["lock_until"] else None,
                        "password_hash_present": bool(password_hash),
                        "password_verifies": bool(password_hash) and verify_password(owner["password"], password_hash),
                    }
                )

            return {
                "database_url_target": summarize_database_url(settings.database_url),
                "alembic_head": alembic_head,
                "superuser_role": (
                    {"id": str(superuser["id"]), "name": superuser["name"]}
                    if superuser
                    else None
                ),
                "users": user_state,
            }
    finally:
        await engine.dispose()


async def fetch_live_login_state() -> list[dict]:
    results = []
    async with httpx.AsyncClient(timeout=httpx.Timeout(20.0, connect=10.0)) as client:
        for owner in OWNER_USERS:
            try:
                response = await client.post(
                    LOGIN_URL,
                    json={"email": owner["email"], "password": owner["password"]},
                    headers={"Content-Type": "application/json"},
                )
                payload = response.json()
            except Exception as exc:  # pragma: no cover - debug path
                results.append(
                    {
                        "email": owner["email"],
                        "login_success": False,
                        "status_code": 0,
                        "message": str(exc),
                    }
                )
                continue

            results.append(
                {
                    "email": owner["email"],
                    "login_success": response.status_code == 200,
                    "status_code": response.status_code,
                    "message": payload.get("message") if isinstance(payload, dict) else None,
                    "error": payload.get("error") if isinstance(payload, dict) else None,
                }
            )
    return results


async def main() -> None:
    db_state, login_state = await asyncio.gather(fetch_db_state(), fetch_live_login_state())
    print(
        json.dumps(
            {
                "database": db_state["database_url_target"],
                "alembic_head": db_state["alembic_head"],
                "superuser_role": db_state["superuser_role"],
                "users": db_state["users"],
                "live_login": login_state,
            },
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
