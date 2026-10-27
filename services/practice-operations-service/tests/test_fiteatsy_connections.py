from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from app.config import get_settings
from app.contracts import AppointmentStatusUpdate
from app.fiteatsy_connections import ALLOWED_SCOPES, create_fiteatsy_delegation, decode_fiteatsy_identity, generate_connection_pin, pin_status_error, pin_verifier, validate_canonical_plan_content, verify_pin


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
    claims = {"sub":"user-1","actor_type":"FITEATSY_USER","iss":"fiteatsy","aud":"zestiva","iat":now,"exp":now+timedelta(minutes=5)}
    token = jwt.encode(claims, key, algorithm="RS256")
    assert decode_fiteatsy_identity(token, key.public_key(), "fiteatsy", "zestiva")["sub"] == "user-1"
    claims["actor_type"] = "CONSULTANT"
    with pytest.raises(jwt.InvalidTokenError):
        decode_fiteatsy_identity(jwt.encode(claims, key, algorithm="RS256"), key.public_key(), "fiteatsy", "zestiva")


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


def test_external_plan_requires_all_canonical_meal_sections():
    content = {
        "nutritionSnapshot": {}, "dailyTargets": {}, "hydrationRhythm": [],
        "weeklySuccessGuide": [], "smartSubstitutions": [], "supplementsAndClinicalNotes": [],
        "mealPlan": {key: {"options": [{"id": f"{key}-1", "meal": "Verified meal", "components": [{"foodId": "verified-food-id"}]}]} for key in (
            "earlyMorning", "breakfast", "midMorningSnack", "lunch", "eveningSnack", "dinner", "bedtimeNutrition"
        )},
    }
    validate_canonical_plan_content(content)
    del content["mealPlan"]["dinner"]
    with pytest.raises(ValueError, match="canonical Fiteatsy nutrition contract"):
        validate_canonical_plan_content(content)


def test_canonical_appointment_update_accepts_reschedule_version_and_follow_up():
    now = datetime.now(timezone.utc)
    update = AppointmentStatusUpdate(status="CONFIRMED", starts_at=now + timedelta(days=1), expected_updated_at=now, follow_up_notes="Review adherence next session")
    assert update.starts_at is not None
    assert update.expected_updated_at == now
    assert update.follow_up_notes == "Review adherence next session"
