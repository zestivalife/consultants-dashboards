from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)


def test_hash_password_produces_different_hashes():
    h1 = hash_password("MyP@ss123")
    h2 = hash_password("MyP@ss123")
    assert h1 != h2, "bcrypt should produce unique salts"


def test_verify_password_correct():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("secret123")
    assert verify_password("wrong", hashed) is False


def test_access_token_round_trip():
    token = create_access_token(subject="user-abc", extra_claims={"role": "member"})
    payload = decode_access_token(token)
    assert payload["sub"] == "user-abc"
    assert payload["role"] == "member"
    assert payload["type"] == "access"


def test_refresh_token_is_random():
    t1 = generate_refresh_token()
    t2 = generate_refresh_token()
    assert t1 != t2
    assert len(t1) > 20


def test_hash_token_deterministic():
    raw = "some-random-token"
    assert hash_token(raw) == hash_token(raw)
    assert hash_token(raw) != hash_token("different")
