import unittest
from unittest.mock import patch

from app.routers.fiteatsy_bridge import _assert_owner_authority


class State:
    user_role = "platform_owner"
    user_id = "owner-1"
    token_payload = {
        "sub": "owner-1",
        "role": "platform_owner",
        "products": ["Fiteatsy"],
        "permissions": ["fiteatsy.qa.identity.create"],
    }


class Request:
    state = State()


class FiteatsyBridgeAuthorityTest(unittest.TestCase):
    def test_entitled_owner_with_operation_permission_is_allowed(self):
        payload, denied = _assert_owner_authority(Request(), "fiteatsy.qa.identity.create")
        self.assertIsNotNone(payload)
        self.assertIsNone(denied)

    def test_owner_without_fiteatsy_entitlement_is_denied(self):
        Request.state.token_payload = {**State.token_payload, "products": ["Nuetra"]}
        payload, denied = _assert_owner_authority(Request(), "fiteatsy.qa.identity.create")
        self.assertIsNone(payload)
        self.assertEqual(denied.status_code, 403)
        Request.state.token_payload = State.token_payload

    def test_owner_without_operation_permission_is_denied(self):
        Request.state.token_payload = {**State.token_payload, "permissions": []}
        payload, denied = _assert_owner_authority(Request(), "fiteatsy.qa.identity.create")
        self.assertIsNone(payload)
        self.assertEqual(denied.status_code, 403)
        Request.state.token_payload = State.token_payload

    def test_consultant_is_denied_even_with_entitlement(self):
        Request.user_role = "consultant"
        payload, denied = _assert_owner_authority(Request(), "fiteatsy.qa.identity.create")
        self.assertIsNone(payload)
        self.assertEqual(denied.status_code, 403)
        Request.user_role = "platform_owner"


if __name__ == "__main__":
    unittest.main()
