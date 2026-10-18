import ast
from pathlib import Path

import pytest

from app.core.owner_bootstrap import (
    CONFIGURATION_ERROR,
    owner_bootstrap_users,
)


def test_optional_migration_bootstrap_skips_safely_without_secret(monkeypatch):
    monkeypatch.delenv("PLATFORM_OWNER_PRIMARY_BOOTSTRAP_PASSWORD", raising=False)
    monkeypatch.delenv("PLATFORM_OWNER_SECONDARY_BOOTSTRAP_PASSWORD", raising=False)
    assert owner_bootstrap_users() == []


def test_explicit_reconciliation_fails_closed_without_secret(monkeypatch):
    monkeypatch.delenv("PLATFORM_OWNER_PRIMARY_BOOTSTRAP_PASSWORD", raising=False)
    monkeypatch.delenv("PLATFORM_OWNER_SECONDARY_BOOTSTRAP_PASSWORD", raising=False)
    with pytest.raises(RuntimeError, match=f"^{CONFIGURATION_ERROR}$"):
        owner_bootstrap_users(required=True)


def test_governed_secret_source_supplies_both_owners(monkeypatch):
    monkeypatch.setenv("PLATFORM_OWNER_PRIMARY_BOOTSTRAP_PASSWORD", "governed-primary-value")
    monkeypatch.setenv("PLATFORM_OWNER_SECONDARY_BOOTSTRAP_PASSWORD", "governed-secondary-value")
    users = owner_bootstrap_users()
    assert len(users) == 2
    assert {user["password"] for user in users} == {
        "governed-primary-value",
        "governed-secondary-value",
    }


def test_current_tree_has_no_hardcoded_bootstrap_passwords():
    root = Path(__file__).resolve().parents[1]
    matches = []
    for path in [*root.joinpath("app").rglob("*.py"), *root.joinpath("alembic").rglob("*.py"), *root.joinpath("scripts").rglob("*.py")]:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Dict):
                continue
            for key, value in zip(node.keys, node.values):
                if (
                    isinstance(key, ast.Constant)
                    and key.value == "password"
                    and isinstance(value, ast.Constant)
                    and isinstance(value.value, str)
                ):
                    matches.append(str(path.relative_to(root)))
    assert matches == []
