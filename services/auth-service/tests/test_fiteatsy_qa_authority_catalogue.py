from scripts.reconcile_auth_schema import (
    FITEATSY_OWNER_PERMISSION_KEYS,
    PERMISSION_SEEDS,
    ROLE_PERMISSION_MAP,
)


def test_governed_fiteatsy_permissions_exist_exactly_once():
    keys = [seed[0] for seed in PERMISSION_SEEDS]
    assert keys.count("fiteatsy.qa.identity.create") == 1
    assert keys.count("fiteatsy.qa.session.issue") == 1
    assert FITEATSY_OWNER_PERMISSION_KEYS == {
        "fiteatsy.qa.identity.create",
        "fiteatsy.qa.session.issue",
    }


def test_governed_fiteatsy_permissions_belong_only_to_platform_owner():
    assert FITEATSY_OWNER_PERMISSION_KEYS <= set(ROLE_PERMISSION_MAP["platform_owner"])
    for role, permissions in ROLE_PERMISSION_MAP.items():
        if role == "platform_owner":
            continue
        assert FITEATSY_OWNER_PERMISSION_KEYS.isdisjoint(permissions), role
