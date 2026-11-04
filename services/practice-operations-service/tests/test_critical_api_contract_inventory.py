import json
from pathlib import Path
import re

from app.main import app


REPO = Path(__file__).resolve().parents[3]
CONTRACTS = REPO / "nuetra-frontend" / "contracts"


def _canonical(path: str) -> str:
    return re.sub(r"\{[^/]+\}", "{}", path).rstrip("/") or "/"


def test_inventory_operations_are_registered_by_fastapi_with_exact_methods():
    inventory = json.loads((CONTRACTS / "provider-route-inventory.json").read_text())
    registered = {
        (method, _canonical(route.path))
        for route in app.routes
        for method in getattr(route, "methods", set())
    }
    expected = {
        (operation["method"], _canonical(operation["path"]))
        for operation in inventory["operations"]
        if operation["provider"] == "practice-operations"
    }
    assert expected <= registered, f"Missing registered operations: {sorted(expected - registered)}"


def test_gateway_registers_the_required_practice_operations_mapping():
    inventory = json.loads((CONTRACTS / "provider-route-inventory.json").read_text())
    gateway_config = (REPO / "api-gateway" / "app" / "config.py").read_text()
    for prefix in inventory["gateway_prefixes"]:
        assert f'{{"prefix": "{prefix}"' in gateway_config


def test_cross_repository_snapshot_is_pinned_to_verified_fiteatsy_sha():
    registry = json.loads((CONTRACTS / "external-consultant-api-registry.json").read_text())
    inventory = json.loads((CONTRACTS / "provider-route-inventory.json").read_text())
    expected = "f7762c1eed4c3026913028742655d6c3f5a6e38e"
    assert registry["provider_baselines"]["fiteatsy"] == expected
    assert inventory["generated_from"]["fiteatsy"] == expected
    fiteatsy_operations = [item for item in inventory["operations"] if item["provider"] == "fiteatsy"]
    assert {(item["method"], item["path"]) for item in fiteatsy_operations} == {
        ("GET", "/v1/internal/external-consultant-access/{userId}/health-context"),
        ("GET", "/v1/platform/nutrition-plan"),
    }
