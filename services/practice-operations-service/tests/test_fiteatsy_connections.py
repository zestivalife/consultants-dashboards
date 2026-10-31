from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from app.config import get_settings
from app.fiteatsy_connections import ALLOWED_SCOPES, PinPreview, PinRedeem, create_assignment_roster_delegation, create_fiteatsy_delegation, decode_fiteatsy_identity, generate_connection_pin, pin_status_error, pin_verifier, verify_pin


def test_pin_is_six_digit_numeric_and_unique_across_sample():
    pins = {generate_connection_pin() for _ in range(50)}
    assert len(pins) == 50
    assert all(len(pin) == 6 and pin.isdigit() for pin in pins)


def test_pin_verifier_normalizes_and_does_not_reveal_pin():
    verifier = pin_verifier("ab cd-2345", "pepper")
    assert verifier == pin_verifier("ABCD-2345", "pepper")
    assert "ABCD" not in verifier
    assert verify_pin("ab cd-2345", verifier, "pepper")
    assert not verify_pin("ABCD-2346", verifier, "pepper")


def test_identity_assertion_requires_fiteatsy_actor():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = datetime.now(timezone.utc)
    claims = {"sub":"user-1","actor_type":"FITEATSY_USER","purpose":"consultant_connection","iss":"fiteatsy","aud":"zestiva","iat":now,"exp":now+timedelta(minutes=5)}
    token = jwt.encode(claims, key, algorithm="RS256")
    assert decode_fiteatsy_identity(token, key.public_key(), "fiteatsy", "zestiva")["sub"] == "user-1"
    claims["actor_type"] = "CONSULTANT"
    with pytest.raises(jwt.InvalidTokenError):
        decode_fiteatsy_identity(jwt.encode(claims, key, algorithm="RS256"), key.public_key(), "fiteatsy", "zestiva")


def test_identity_assertion_rejects_login_or_missing_purpose():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = datetime.now(timezone.utc)
    common = {"sub":"user-1","actor_type":"FITEATSY_USER","iss":"fiteatsy","aud":"zestiva","iat":now,"exp":now+timedelta(minutes=5)}
    for purpose in (None, "login_pin"):
        claims = {**common, **({} if purpose is None else {"purpose": purpose})}
        with pytest.raises(jwt.InvalidTokenError):
            decode_fiteatsy_identity(jwt.encode(claims, key, algorithm="RS256"), key.public_key(), "fiteatsy", "zestiva")


def test_connection_contract_requires_explicit_pin_purpose():
    assert PinPreview.model_validate({"pin":"012345","purpose":"CONSULTANT_CONNECTION_PIN"}).pin == "012345"
    assert PinRedeem.model_validate({"pin":"012345","purpose":"CONSULTANT_CONNECTION_PIN","consent_version":"external-consultant-v1","accepted_scopes":["PROFILE"]}).pin == "012345"
    with pytest.raises(ValueError):
        PinPreview.model_validate({"pin":"012345","purpose":"LOGIN_PIN"})


def test_scopes_are_explicit_and_minimal():
    assert ALLOWED_SCOPES == {"PROFILE","HEALTH_SUMMARY","MEASUREMENTS","BIOMARKERS","DIET_PLANS","APPOINTMENTS"}


def test_pin_lifecycle_errors_are_distinct():
    now = datetime.now(timezone.utc)
    capture = lambda _request, status, code, message: (status, code, message)
    common = {"expires_at": now + timedelta(minutes=5), "attempt_count": 0, "max_attempts": 8}
    assert pin_status_error(None, capture, None, now)[1] == "CONNECTION_PIN_INVALID"
    assert pin_status_error(None, capture, {**common, "status": "REDEEMED"}, now)[1] == "CONNECTION_PIN_ALREADY_USED"
    assert pin_status_error(None, capture, {**common, "status": "REVOKED"}, now)[1] == "CONNECTION_PIN_REVOKED"
    assert pin_status_error(None, capture, {**common, "status": "PENDING", "expires_at": now - timedelta(seconds=1)}, now)[1] == "CONNECTION_PIN_EXPIRED"


def test_outbound_delegation_is_short_lived_and_connection_bound(monkeypatch):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    monkeypatch.setenv("EXTERNAL_FITEATSY_OUTBOUND_PRIVATE_KEY", pem)
    monkeypatch.setenv("EXTERNAL_FITEATSY_OUTBOUND_KEY_ID", "phase2-test")
    monkeypatch.setenv("EXTERNAL_FITEATSY_BACKEND_URL", "https://fiteatsy.invalid")
    get_settings.cache_clear()
    token = create_fiteatsy_delegation({"id": "connection-1", "tenant_id": "tenant-1", "consultant_id": "consultant-1", "fiteatsy_user_id": "user-1", "consented_scopes": ["PROFILE"]}, "fiteatsy.external.health.read", "external_consultant_health")
    claims = jwt.decode(token, key.public_key(), algorithms=["RS256"], audience="fiteatsy-backend", issuer="zestiva-platform")
    assert claims["connection_id"] == "connection-1"
    assert claims["fiteatsy_user_id"] == "user-1"
    assert claims["scopes"] == ["PROFILE"]
    assert claims["exp"] - claims["iat"] == 60
    get_settings.cache_clear()


def test_assignment_roster_delegation_uses_canonical_external_identity(monkeypatch):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    monkeypatch.setenv("EXTERNAL_FITEATSY_OUTBOUND_PRIVATE_KEY", pem)
    monkeypatch.setenv("EXTERNAL_FITEATSY_OUTBOUND_KEY_ID", "phase2-test")
    get_settings.cache_clear()
    user_id = "f7d1587f-4dc6-47f0-b95c-bb8472e99136"
    token = create_assignment_roster_delegation({"user_id": user_id, "tenant_id": "tenant-1"})
    claims = jwt.decode(token, key.public_key(), algorithms=["RS256"], audience="fiteatsy-backend", issuer="zestiva-platform")
    assert claims["sub"] == f"ext_{user_id}"
    assert claims["actor_type"] == "EXTERNAL_CONSULTANT"
    assert claims["permissions"] == ["fiteatsy.external.assignment.read"]
    assert claims["purpose"] == "external_consultant_assignment_roster"
    assert claims["exp"] - claims["iat"] == 60
    get_settings.cache_clear()


def test_assignment_roster_delegation_prefers_provisioned_fiteatsy_identity(monkeypatch):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    monkeypatch.setenv("EXTERNAL_FITEATSY_OUTBOUND_PRIVATE_KEY", pem)
    monkeypatch.setenv("EXTERNAL_FITEATSY_OUTBOUND_KEY_ID", "phase2-test")
    get_settings.cache_clear()
    auth_user_id = "f7d1587f-4dc6-47f0-b95c-bb8472e99136"
    mapped_id = "ext_8d3b48b8-a8f7-42e2-b1ef-b36ac2c9bc20"
    token = create_assignment_roster_delegation({
        "user_id": auth_user_id,
        "tenant_id": "tenant-1",
        "fiteatsy_professional_id": mapped_id,
    })
    claims = jwt.decode(token, key.public_key(), algorithms=["RS256"], audience="fiteatsy-backend", issuer="zestiva-platform")
    assert claims["sub"] == mapped_id
    get_settings.cache_clear()


@pytest.mark.parametrize("mapped_id", ["8d3b48b8-a8f7-42e2-b1ef-b36ac2c9bc20", "ext_not-a-uuid"])
def test_assignment_roster_delegation_rejects_invalid_mapped_identity(monkeypatch, mapped_id):
    monkeypatch.setenv("EXTERNAL_FITEATSY_OUTBOUND_PRIVATE_KEY", "unused")
    get_settings.cache_clear()
    with pytest.raises((ValueError, TypeError)):
        create_assignment_roster_delegation({
            "user_id": "f7d1587f-4dc6-47f0-b95c-bb8472e99136",
            "tenant_id": "tenant-1",
            "fiteatsy_professional_id": mapped_id,
        })
    get_settings.cache_clear()
