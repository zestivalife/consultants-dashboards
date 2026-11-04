import ast
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[3]
SERVICES = ("assessment-service", "nutrition-service", "scoring-engine-service")


def validate_pool_timeout_contract(config_source: str, session_source: str) -> list[str]:
    config = ast.parse(config_source)
    session = ast.parse(session_source)
    declared = {
        node.target.id
        for node in ast.walk(config)
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    }
    uses_timeout = any(
        isinstance(node, ast.keyword)
        and node.arg == "pool_timeout"
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "db_pool_timeout"
        for node in ast.walk(session)
    )
    failures = []
    if not uses_timeout:
        failures.append("database engine does not pass pool_timeout")
    if "db_pool_timeout" not in declared:
        failures.append("Settings does not declare db_pool_timeout")
    return failures


@pytest.mark.parametrize("service", SERVICES)
def test_database_pool_timeout_contract_is_complete(service):
    root = REPO / "services" / service / "app"
    failures = validate_pool_timeout_contract(
        (root / "config.py").read_text(),
        (root / "db" / "session.py").read_text(),
    )
    assert not failures, f"{service}: {failures}"


def test_negative_fixture_removing_db_pool_timeout_fails_contract():
    root = REPO / "services" / "assessment-service" / "app"
    config = (root / "config.py").read_text()
    broken = "\n".join(line for line in config.splitlines() if "db_pool_timeout:" not in line)
    failures = validate_pool_timeout_contract(broken, (root / "db" / "session.py").read_text())
    assert failures == ["Settings does not declare db_pool_timeout"]
