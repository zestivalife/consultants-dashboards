import unittest
from types import SimpleNamespace
from unittest.mock import patch

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.security.fiteatsy_delegation import issue_fiteatsy_delegation


class FiteatsyDelegationTokenTest(unittest.TestCase):
    def test_token_is_short_lived_and_exactly_permission_bound(self):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        private_key = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
        public_key = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
        settings = SimpleNamespace(
            fiteatsy_delegation_private_key=private_key,
            fiteatsy_delegation_key_id="phase-c-key",
            fiteatsy_delegation_issuer="zestiva-platform",
            fiteatsy_delegation_audience="fiteatsy-backend",
            fiteatsy_delegation_ttl_seconds=180,
        )
        with patch("app.security.fiteatsy_delegation.get_settings", return_value=settings):
            token = issue_fiteatsy_delegation(
                subject="owner-123",
                permissions=["fiteatsy.qa.admin.create"],
                purpose="qa_provisioning",
                actor_type="platform_owner",
            )
        payload = jwt.decode(token, public_key, algorithms=["RS256"], audience="fiteatsy-backend", issuer="zestiva-platform")
        self.assertEqual(payload["sub"], "owner-123")
        self.assertEqual(payload["actor_type"], "platform_owner")
        self.assertEqual(payload["purpose"], "qa_provisioning")
        self.assertEqual(payload["permissions"], ["fiteatsy.qa.admin.create"])
        self.assertEqual(payload["exp"] - payload["iat"], 180)
        self.assertTrue(payload["jti"])
        self.assertEqual(jwt.get_unverified_header(token)["kid"], "phase-c-key")


if __name__ == "__main__":
    unittest.main()
