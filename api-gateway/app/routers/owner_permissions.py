OWNER_ACCESS_RULES: tuple[tuple[str, str, set[str]], ...] = (
    ("/api/v1/owner/people-access/summary", "GET", {"users.read"}),
    ("/api/v1/owner/people-access/metadata", "GET", {"users.read"}),
    ("/api/v1/owner/people-access/invitations", "GET", {"users.read"}),
    ("/api/v1/owner/people-access/invitations", "POST", {"users.invite"}),
    ("/api/v1/owner/people-access/invitations/", "POST", {"users.invite"}),
    ("/api/v1/owner/people-access/invitations/*/regenerate-link", "POST", {"users.invite"}),
    ("/api/v1/owner/people-access/roles", "POST", {"settings.manage"}),
    ("/api/v1/owner/people-access/roles/", "POST", {"settings.manage"}),
    ("/api/v1/owner/people-access/roles/", "PATCH", {"settings.manage"}),
    ("/api/v1/owner/people-access/users/bulk-actions", "POST", {"users.edit", "users.invite"}),
    ("/api/v1/owner/people-access/exports/users", "GET", {"users.export"}),
    ("/api/v1/owner/people-access/users/import", "POST", {"users.import"}),
    ("/api/v1/owner/people-access/users/*/products", "PUT", {"users.edit"}),
    ("/api/v1/owner/people-access/users/*/packages", "PUT", {"packages.manage"}),
    ("/api/v1/owner/people-access/users/*/services", "PUT", {"services.manage"}),
    ("/api/v1/owner/people-access/users/*/sessions/*/revoke", "POST", {"users.force_logout"}),
    ("/api/v1/owner/people-access/users/*/force-logout", "POST", {"users.force_logout"}),
    ("/api/v1/owner/people-access/users/", "PATCH", {"users.edit"}),
    ("/api/v1/owner/people-access/users/", "GET", {"users.read"}),
    ("/api/v1/owner/people-access/users/", "POST", {"users.edit"}),
    ("/api/v1/owner/people-access/users/", "PUT", {"users.edit"}),
    ("/api/v1/owner/people-access/users", "POST", {"users.create"}),
    ("/api/v1/owner/people-access/users", "GET", {"users.read"}),
    ("/api/v1/owner/people-access/organizations", "POST", {"organizations.manage"}),
    ("/api/v1/owner/master-data/categories", "GET", {"master_data.read"}),
    ("/api/v1/owner/master-data/categories", "POST", {"master_data.create"}),
    ("/api/v1/owner/master-data/categories/", "PATCH", {"master_data.edit"}),
    ("/api/v1/owner/master-data/categories/", "DELETE", {"master_data.delete"}),
    ("/api/v1/owner/master-data/categories/*/restore", "POST", {"master_data.restore"}),
    ("/api/v1/owner/master-data/items", "GET", {"master_data.read"}),
    ("/api/v1/owner/master-data/items", "POST", {"master_data.create"}),
    ("/api/v1/owner/master-data/items/import", "POST", {"master_data.import"}),
    ("/api/v1/owner/master-data/items/export", "GET", {"master_data.export"}),
    ("/api/v1/owner/master-data/items/", "PATCH", {"master_data.edit"}),
    ("/api/v1/owner/master-data/items/", "DELETE", {"master_data.delete"}),
    ("/api/v1/owner/master-data/items/*/restore", "POST", {"master_data.restore"}),
)


def _path_matches(pattern: str, path: str) -> bool:
    if "*" not in pattern:
        return path.startswith(pattern)

    path_parts = [part for part in path.split("/") if part]
    pattern_parts = [part for part in pattern.split("/") if part]
    return len(path_parts) == len(pattern_parts) and all(
        expected == "*" or expected == actual
        for expected, actual in zip(pattern_parts, path_parts)
    )


def required_owner_permissions(path: str, method: str) -> set[str]:
    normalized_method = method.upper()
    for pattern, allowed_method, permissions in OWNER_ACCESS_RULES:
        if normalized_method == allowed_method and _path_matches(pattern, path):
            return permissions
    return set()
