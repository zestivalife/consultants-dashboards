from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.fiteatsy_connections import ALLOWED_SCOPES, decode_fiteatsy_identity, generate_connection_pin, pin_verifier, verify_pin


def test_pin_is_human_readable_high_entropy_and_never_ambiguous():
    pins = {generate_connection_pin() for _ in range(200)}
    assert len(pins) == 200
    assert all(len(pin) == 8 and not set(pin) & set("01IO") for pin in pins)


def test_pin_verifier_normalizes_and_does_not_reveal_pin():
    verifier = pin_verifier("ab cd-2345", "pepper")
    assert verifier == pin_verifier("ABCD-2345", "pepper")
    assert "ABCD" not in verifier
    assert verify_pin("ab cd-2345", verifier, "pepper")
    assert not verify_pin("ABCD-2346", verifier, "pepper")


def test_identity_assertion_requires_fiteatsy_actor():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = datetime.now(timezone.utc)
    claims = {"sub":"user-1","actor_type":"FITEATSY_USER","iss":"fiteatsy","aud":"zestiva","iat":now,"exp":now+timedelta(minutes=5)}
    token = jwt.encode(claims, key, algorithm="RS256")
    assert decode_fiteatsy_identity(token, key.public_key(), "fiteatsy", "zestiva")["sub"] == "user-1"
    claims["actor_type"] = "CONSULTANT"
    with pytest.raises(jwt.InvalidTokenError):
        decode_fiteatsy_identity(jwt.encode(claims, key, algorithm="RS256"), key.public_key(), "fiteatsy", "zestiva")


def test_scopes_are_explicit_and_minimal():
    assert ALLOWED_SCOPES == {"PROFILE","HEALTH_SUMMARY","MEASUREMENTS","BIOMARKERS","DIET_PLANS","APPOINTMENTS"}
