from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "app" / "main.py").read_text()


def test_literal_practice_collections_precede_legacy_resource_catch_all():
    """P12-P50 collection roots must not be swallowed by /{resource}."""
    repair = MAIN[MAIN.index("def _prefer_literal_practice_collection_routes") :]
    assert 'f"{prefix}{{resource}}"' in repair
    assert 'f"{prefix}{{resource}}/{{item_id}}"' in repair
    assert "[*specific_routes, *catch_all_routes]" in repair
    assert repair.rstrip().endswith("_prefer_literal_practice_collection_routes()")


def test_all_accepted_literal_collection_roots_remain_declared():
    roots = {
        "packages",
        "client-packages",
        "renewal-signals",
        "resources",
        "automations",
        "team",
        "referrals",
        "progress-reports",
        "forms",
        "form-assignments",
        "consents",
        "documents",
        "leads",
        "locations",
        "calendar-sync",
        "subscription",
        "notification-centre",
        "notification-preferences",
        "global-search",
        "recent-work",
    }
    for root in roots:
        assert f'/api/v1/practice-operations/{root}"' in MAIN
