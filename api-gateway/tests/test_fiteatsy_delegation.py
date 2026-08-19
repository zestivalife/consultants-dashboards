import time
import unittest
from unittest.mock import patch

import jwt

from app.config import Settings
from app.security.fiteatsy_delegation import issue_fiteatsy_delegation


class FiteatsyDelegationIssuerTest(unittest.TestCase):
    def test_contract_claims_and_rsa_header(self):
        private_key = "-----BEGIN PRIVATE KEY-----\nTEST-ONLY\n-----END PRIVATE KEY-----"
        settings = Settings(
            fiteatsy_delegation_private_key=private_key,
            fiteatsy_delegation_key_id="zestiva-2026-01",
            fiteatsy_delegation_ttl_seconds=180,
        )
        with patch("app.security.fiteatsy_delegation.get_settings", return_value=settings), patch(
            "app.security.fiteatsy_delegation.jwt.encode", return_value="signed-token"
        ) as encode:
            token = issue_fiteatsy_delegation(
                subject="owner-123",
                permissions=["fiteatsy:qa_provisioning", "fiteatsy:qa_provisioning"],
                purpose="qa_provisioning",
                actor_type="platform_owner",
            )
        self.assertEqual(token, "signed-token")
        payload = encode.call_args.args[0]
        self.assertEqual(payload["iss"], "zestiva-platform")
        self.assertEqual(payload["aud"], "fiteatsy-backend")
        self.assertEqual(payload["sub"], "owner-123")
        self.assertEqual(payload["product"], "fiteatsy")
        self.assertEqual(payload["permissions"], ["fiteatsy:qa_provisioning"])
        self.assertEqual(payload["purpose"], "qa_provisioning")
        self.assertEqual(payload["actor_type"], "platform_owner")
        self.assertTrue(payload["jti"])
        self.assertGreaterEqual(payload["exp"] - payload["iat"], 179)
        self.assertEqual(encode.call_args.kwargs["algorithm"], "RS256")
        self.assertEqual(encode.call_args.kwargs["headers"]["kid"], "zestiva-2026-01")

    def test_ttl_is_short_and_configured(self):
        settings = Settings(fiteatsy_delegation_private_key="key", fiteatsy_delegation_key_id="k", fiteatsy_delegation_ttl_seconds=60)
        with patch("app.security.fiteatsy_delegation.get_settings", return_value=settings), patch("app.security.fiteatsy_delegation.jwt.encode", return_value="token") as encode:
            issue_fiteatsy_delegation(subject="s", permissions=["p"], purpose="x", actor_type="service")
        payload = encode.call_args.args[0]
        self.assertLessEqual(payload["exp"] - int(time.time()), 60)


if __name__ == "__main__":
    unittest.main()
