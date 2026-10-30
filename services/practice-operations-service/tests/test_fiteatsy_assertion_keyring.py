from datetime import datetime, timedelta, timezone
import json

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.fiteatsy_assertions import decode_fiteatsy_assertion, parse_public_keyring


def key_pair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private_key, public_key


def token(private_key, key_id=None, algorithm="RS256"):
    now = datetime.now(timezone.utc)
    headers = {"kid": key_id} if key_id else None
    return jwt.encode(
        {"sub": "fiteatsy-user", "iss": "fiteatsy", "aud": "practice-operations", "iat": now, "exp": now + timedelta(minutes=5)},
        private_key,
        algorithm=algorithm,
        headers=headers,
    )


def decode(value, keyring, legacy=None):
    return decode_fiteatsy_assertion(
        value,
        keyring=keyring,
        legacy_public_key=legacy,
        issuer="fiteatsy",
        audience="practice-operations",
        required_claims=["exp", "iat", "iss", "aud", "sub"],
    )


def test_keyring_accepts_old_and_new_keys_during_overlap():
    old_private, old_public = key_pair()
    new_private, new_public = key_pair()
    keyring = {"old-2026": old_public, "new-2026": new_public}
    assert decode(token(old_private, "old-2026"), keyring)["sub"] == "fiteatsy-user"
    assert decode(token(new_private, "new-2026"), keyring)["sub"] == "fiteatsy-user"


def test_keyring_rejects_missing_unknown_and_removed_key_ids():
    private_key, public_key = key_pair()
    with pytest.raises(jwt.InvalidTokenError, match="identifier is required"):
        decode(token(private_key), {"trusted": public_key})
    with pytest.raises(jwt.InvalidTokenError, match="not trusted"):
        decode(token(private_key, "unknown"), {"trusted": public_key})
    with pytest.raises(jwt.InvalidTokenError, match="not trusted"):
        decode(token(private_key, "retired"), {"replacement": public_key})


def test_keyring_does_not_fall_back_to_legacy_key():
    private_key, public_key = key_pair()
    _, replacement_public = key_pair()
    with pytest.raises(jwt.InvalidTokenError, match="not trusted"):
        decode(token(private_key, "legacy"), {"replacement": replacement_public}, legacy=public_key)


def test_keyring_rejects_non_rs256_algorithm_before_key_selection():
    value = jwt.encode(
        {"sub": "fiteatsy-user"},
        "not-a-production-secret",
        algorithm="HS256",
        headers={"kid": "trusted"},
    )
    _, public_key = key_pair()
    with pytest.raises(jwt.InvalidAlgorithmError, match="must use RS256"):
        decode(value, {"trusted": public_key})


def test_legacy_single_key_mode_remains_compatible_without_keyring():
    private_key, public_key = key_pair()
    assert decode(token(private_key), {}, legacy=public_key)["sub"] == "fiteatsy-user"


def test_keyring_parser_normalizes_pem_and_rejects_invalid_configuration():
    _, public_key = key_pair()
    escaped = public_key.replace("\n", "\\n")
    assert parse_public_keyring(json.dumps({"rotation-1": escaped}))["rotation-1"].startswith("-----BEGIN PUBLIC KEY-----")
    for invalid in ("[]", "{}", '{"": "bad"}', '{"key": "bad"}', "not-json"):
        with pytest.raises(ValueError):
            parse_public_keyring(invalid)

    weak_private = rsa.generate_private_key(public_exponent=65537, key_size=1024)
    weak_public = weak_private.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    with pytest.raises(ValueError, match="at least 2048 bits"):
        parse_public_keyring(json.dumps({"weak": weak_public}))
