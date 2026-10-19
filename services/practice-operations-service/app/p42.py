"""P42 provider-neutral calendar synchronisation policy."""

PROVIDERS = {"GOOGLE", "MICROSOFT"}


def provider_state(provider: str, configured: bool) -> str:
    if provider not in PROVIDERS:
        raise ValueError("Unsupported calendar provider")
    return "CONNECTED" if configured else "NOT_CONFIGURED"


def project_busy_block(row: dict) -> dict:
    """Public/practitioner projection deliberately omits provider event detail."""
    return {
        "id": str(row["id"]),
        "starts_at": row["starts_at"],
        "ends_at": row["ends_at"],
        "visibility": "BUSY",
        "source_type": "EXTERNAL_BUSY",
    }


def external_change_action(kind: str) -> str:
    if kind not in {"RESCHEDULE", "CANCEL"}:
        raise ValueError("Unsupported external calendar change")
    return "PRACTITIONER_CONFIRMATION_REQUIRED"
