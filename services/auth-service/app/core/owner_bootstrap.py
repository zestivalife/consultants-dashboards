"""Governed Platform Owner bootstrap credential resolution.

Historical migrations use optional mode so schema upgrades never depend on
credential availability. Explicit operational commands use required mode and
fail closed with a stable, non-secret error code.
"""

from __future__ import annotations

import os


CONFIGURATION_ERROR = "PLATFORM_OWNER_BOOTSTRAP_CONFIGURATION_MISSING"


def owner_bootstrap_users(*, required: bool = False) -> list[dict[str, object]]:
    primary = os.getenv("PLATFORM_OWNER_PRIMARY_BOOTSTRAP_PASSWORD")
    secondary = os.getenv("PLATFORM_OWNER_SECONDARY_BOOTSTRAP_PASSWORD")
    if not primary or not secondary:
        if required:
            raise RuntimeError(CONFIGURATION_ERROR)
        return []
    return [
        {
            "id": "66f4d9d8-6f1f-4d39-a101-5355d5950001",
            "email": "zestivapriyanshi@gmail.com",
            "password": primary,
            "first_name": "Priyanshi",
            "last_name": None,
        },
        {
            "id": "66f4d9d8-6f1f-4d39-a101-5355d5950002",
            "email": "lalitppaunikar26@gmail.com",
            "password": secondary,
            "first_name": "Lalit",
            "last_name": "Paunikar",
        },
    ]
