from typing import Any, Mapping


def client_directory_projection(row: Mapping[str, Any]) -> dict[str, Any]:
    """Public directory projection; assignment visibility is not health-data consent."""
    profile_authorized = bool(row.get("health_data_authorized")) and "PROFILE" in (row.get("consented_scopes") or [])
    values = row.get("profile_values") if profile_authorized and isinstance(row.get("profile_values"), Mapping) else {}
    first_name = str(values.get("firstName") or values.get("first_name") or "").strip()
    last_name = str(values.get("lastName") or values.get("last_name") or "").strip()
    name = str(values.get("name") or values.get("fullName") or "").strip()
    if not name:
        name = " ".join(part for part in (first_name, last_name) if part)
    if not name and profile_authorized:
        name = str(row.get("directory_display_name") or "").strip()

    client_id = str(row["client_id"])
    return {
        "id": client_id,
        "clientId": client_id,
        "connectionId": str(row["connection_id"]) if row.get("connection_id") else None,
        "name": name or "Unnamed client",
        "email": values.get("email"),
        "mobile": values.get("mobile") or values.get("phone"),
        "status": row.get("relationship_status"),
        "relationshipStatus": row.get("relationship_status"),
        "assignmentStatus": row.get("assignment_status"),
        "connectionState": row.get("state"),
        "healthDataAuthorized": bool(row.get("health_data_authorized")),
        "consentedScopes": list(row.get("consented_scopes") or []),
        "connectedAt": row.get("connected_at"),
        "lastActiveAt": row.get("updated_at"),
    }
