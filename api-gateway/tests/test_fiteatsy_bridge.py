import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from pydantic import ValidationError
from starlette.requests import Request

from app.routers.fiteatsy_bridge import (
    QaAdminProvisionRequest,
    _assert_owner_authority,
    issue_qa_session,
    provision_qa_admin,
    provision_qa_client,
)


def owner_request(*, role="platform_owner", permissions=None, products=None, user_id="owner-123", idempotency_key="phase-c-admin", path="/api/v1/platform/fiteatsy/qa-admins"):
    headers = []
    if idempotency_key is not None:
        headers.append((b"idempotency-key", idempotency_key.encode()))
    request = Request({"type": "http", "method": "POST", "path": path, "headers": headers})
    request.state.user_id = user_id
    request.state.user_role = role
    request.state.token_payload = {
        "sub": user_id,
        "role": role,
        "permissions": permissions or [],
        "products": products or [],
    }
    return request


class FakeResponse:
    status_code = 201
    is_success = True

    def json(self):
        return {
            "user": {"id": "qa-admin-1", "role": "admin", "accountPurpose": "QA_TEST"},
            "idempotentReplay": False,
            "handoff": "one_time_exchange",
            "exchange": {"code": "opaque-code", "targetUserId": "qa-admin-1", "purpose": "qa_admin_session_handoff"},
        }


class FakeHttpClient:
    request = AsyncMock(return_value=FakeResponse())

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FiteatsyOwnerBridgeTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        FakeHttpClient.request.reset_mock()

    def test_qa_admin_contract_forbids_arbitrary_role_or_account_purpose(self):
        with self.assertRaises(ValidationError):
            QaAdminProvisionRequest.model_validate({
                "name": "Phase C Admin",
                "email": "qa-admin@example.test",
                "mobileNumber": "+919876543210",
                "reason": "Phase C",
                "role": "super_admin",
            })
        with self.assertRaises(ValidationError):
            QaAdminProvisionRequest.model_validate({
                "name": "Phase C Admin",
                "email": "qa-admin@example.test",
                "mobileNumber": "+919876543210",
                "reason": "Phase C",
                "account_purpose": "PRODUCTION_USER",
            })

    def test_owner_authority_requires_exact_role_entitlement_and_permission(self):
        permission = "fiteatsy.qa.admin.create"
        valid = owner_request(role="platform_owner", permissions=[permission], products=["fiteatsy"])
        payload, denied = _assert_owner_authority(valid, permission)
        self.assertIsNotNone(payload)
        self.assertIsNone(denied)

        for request in (
            owner_request(role="superuser", permissions=[permission], products=["fiteatsy"]),
            owner_request(role="consultant", permissions=[permission], products=["fiteatsy"]),
            owner_request(role="senior_consultant", permissions=[permission], products=["fiteatsy"]),
            owner_request(role="admin", permissions=[permission], products=["fiteatsy"]),
            owner_request(role="client", permissions=[permission], products=["fiteatsy"]),
            owner_request(role="platform_owner", permissions=[], products=["fiteatsy"]),
            owner_request(role="platform_owner", permissions=[permission], products=[]),
            owner_request(role="platform_owner", permissions=[permission], products=["unrelated-product"]),
            owner_request(role="platform_owner", permissions=[permission], products=["fiteatsy"], user_id=""),
        ):
            payload, denied = _assert_owner_authority(request, permission)
            self.assertIsNone(payload)
            self.assertEqual(denied.status_code, 403)

    async def test_qa_admin_bridge_uses_exact_delegation_and_server_to_server_contract(self):
        permission = "fiteatsy.qa.admin.create"
        request = owner_request(role="platform_owner", permissions=[permission], products=["fiteatsy"])
        body = QaAdminProvisionRequest(
            name="Phase C Admin",
            email="qa-admin@example.test",
            mobileNumber="+919876543210",
            reason="Phase C acceptance",
        )
        settings = SimpleNamespace(fiteatsy_service_url="https://fiteatsy.example")
        with (
            patch("app.routers.fiteatsy_bridge.get_settings", return_value=settings),
            patch("app.routers.fiteatsy_bridge.issue_fiteatsy_delegation", return_value="signed-server-token") as issue,
            patch("app.routers.fiteatsy_bridge.httpx.AsyncClient", FakeHttpClient),
        ):
            response = await provision_qa_admin(request, body)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertEqual(response.headers["Referrer-Policy"], "no-referrer")
        response_body = json.loads(response.body)
        self.assertNotIn("signed-server-token", json.dumps(response_body))
        issue.assert_called_once_with(
            subject="owner-123",
            permissions=[permission],
            purpose="qa_provisioning",
            actor_type="platform_owner",
        )
        call = FakeHttpClient.request.await_args
        self.assertEqual(call.args[0], "POST")
        self.assertEqual(call.args[1], "https://fiteatsy.example/v1/internal/delegated/qa-admins")
        self.assertEqual(call.kwargs["headers"]["X-Zestiva-Delegation"], "signed-server-token")
        self.assertEqual(call.kwargs["headers"]["Idempotency-Key"], "phase-c-admin")
        self.assertEqual(call.kwargs["json"], body.model_dump())

    async def test_missing_idempotency_key_is_denied_before_signing(self):
        permission = "fiteatsy.qa.admin.create"
        request = owner_request(role="platform_owner", permissions=[permission], products=["fiteatsy"], idempotency_key=None)
        body = QaAdminProvisionRequest(name="Phase C Admin", email="qa-admin@example.test", mobileNumber="+919876543210", reason="Phase C acceptance")
        with patch("app.routers.fiteatsy_bridge.issue_fiteatsy_delegation") as issue:
            response = await provision_qa_admin(request, body)
        self.assertEqual(response.status_code, 400)
        issue.assert_not_called()

    async def test_governed_identity_creation_uses_exact_permission_and_audit_context(self):
        permission = "fiteatsy.qa.identity.create"
        request = owner_request(
            permissions=[permission],
            products=["fiteatsy"],
            idempotency_key="qa-client-1",
            path="/api/v1/platform/fiteatsy/qa-clients",
        )
        body = {"name": "Synthetic QA Client", "accountPurpose": "QA_TEST"}
        settings = SimpleNamespace(fiteatsy_service_url="https://fiteatsy.example")
        with (
            patch("app.routers.fiteatsy_bridge.get_settings", return_value=settings),
            patch("app.routers.fiteatsy_bridge.issue_fiteatsy_delegation", return_value="signed-server-token") as issue,
            patch("app.routers.fiteatsy_bridge.httpx.AsyncClient", FakeHttpClient),
            patch("app.routers.fiteatsy_bridge.logger.info") as audit,
        ):
            response = await provision_qa_client(request, body)

        self.assertEqual(response.status_code, 201)
        issue.assert_called_once_with(
            subject="owner-123",
            permissions=[permission],
            purpose="qa_provisioning",
            actor_type="platform_owner",
        )
        self.assertEqual(FakeHttpClient.request.await_args.args[1], "https://fiteatsy.example/v1/internal/delegated/qa-clients")
        self.assertEqual(audit.call_count, 2)
        self.assertEqual(audit.call_args_list[0].kwargs["operation"], "qa_client_provision")
        self.assertEqual(audit.call_args_list[1].kwargs["succeeded"], True)

    async def test_governed_qa_session_uses_existing_audited_downstream_contract(self):
        permission = "fiteatsy.qa.session.issue"
        request = owner_request(
            permissions=[permission],
            products=["fiteatsy"],
            idempotency_key="qa-session-1",
            path="/api/v1/platform/fiteatsy/qa-identities/qa-user-1/session",
        )
        body = {"reason": "Reports V2 governed QA"}
        settings = SimpleNamespace(fiteatsy_service_url="https://fiteatsy.example")
        with (
            patch("app.routers.fiteatsy_bridge.get_settings", return_value=settings),
            patch("app.routers.fiteatsy_bridge.issue_fiteatsy_delegation", return_value="signed-server-token") as issue,
            patch("app.routers.fiteatsy_bridge.httpx.AsyncClient", FakeHttpClient),
            patch("app.routers.fiteatsy_bridge.logger.info") as audit,
        ):
            response = await issue_qa_session(request, "qa-user-1", body)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertEqual(response.headers["Referrer-Policy"], "no-referrer")
        issue.assert_called_once_with(
            subject="owner-123",
            permissions=[permission],
            purpose="qa_session",
            actor_type="platform_owner",
        )
        self.assertEqual(
            FakeHttpClient.request.await_args.args[1],
            "https://fiteatsy.example/v1/internal/delegated/qa-identities/qa-user-1/session",
        )
        self.assertEqual(audit.call_count, 2)
        self.assertEqual(audit.call_args_list[0].kwargs["operation"], "qa_session_issue")

if __name__ == "__main__":
    unittest.main()
