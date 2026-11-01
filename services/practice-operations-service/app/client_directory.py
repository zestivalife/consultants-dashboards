from typing import Any, Mapping


def client_directory_projection(row: Mapping[str, Any]) -> dict[str, Any]:
    """Public consultant projection for one tenant-authorised connected client."""
    values = row.get("profile_values") if isinstance(row.get("profile_values"), Mapping) else {}
    first_name = str(values.get("firstName") or values.get("first_name") or "").strip()
    last_name = str(values.get("lastName") or values.get("last_name") or "").strip()
    name = str(values.get("name") or values.get("fullName") or "").strip()
    if not name:
        name = " ".join(part for part in (first_name, last_name) if part)

    client_id = str(row["client_id"])
    return {
        "id": client_id,
        "clientId": client_id,
        "connectionId": str(row["connection_id"]),
        "name": name or "Unnamed client",
        "email": values.get("email"),
        "mobile": values.get("mobile") or values.get("phone"),
        "status": row.get("state"),
        "consentedScopes": list(row.get("consented_scopes") or []),
        "connectedAt": row.get("connected_at"),
        "lastActiveAt": row.get("updated_at"),
    }
