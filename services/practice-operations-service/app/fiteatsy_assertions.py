"""Strict verification for assertions issued by Fiteatsy.

Production rotations use an explicit ``kid`` to public-key mapping. The legacy
single-key setting remains available only when no keyring is configured so a
keyring-capable release can be deployed before the signing key is changed.
"""
import json
from collections.abc import Mapping
from typing import Any

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def parse_public_keyring(raw_keyring: str | None) -> dict[str, str]:
    if not raw_keyring or not raw_keyring.strip():
        return {}
    try:
        value = json.loads(raw_keyring)
    except json.JSONDecodeError as exc:
        raise ValueError("EXTERNAL_FITEATSY_INBOUND_PUBLIC_KEYS must be valid JSON") from exc
    if not isinstance(value, dict) or not value:
        raise ValueError("EXTERNAL_FITEATSY_INBOUND_PUBLIC_KEYS must be a non-empty object")

    keyring: dict[str, str] = {}
    for key_id, public_key in value.items():
        if not isinstance(key_id, str) or not key_id.strip():
            raise ValueError("Fiteatsy assertion key identifiers must be non-empty strings")
        if not isinstance(public_key, str):
            raise ValueError(f"Fiteatsy assertion public key {key_id!r} is not a PEM public key")
        normalized_key = public_key.replace("\\n", "\n").strip()
        try:
            loaded_key = serialization.load_pem_public_key(normalized_key.encode("utf-8"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Fiteatsy assertion public key {key_id!r} is not a PEM public key") from exc
        if not isinstance(loaded_key, rsa.RSAPublicKey) or loaded_key.key_size < 2048:
            raise ValueError(f"Fiteatsy assertion public key {key_id!r} must be an RSA key of at least 2048 bits")
        keyring[key_id.strip()] = normalized_key
    return keyring


def select_assertion_key(
    token: str,
    *,
    keyring: Mapping[str, str],
    legacy_public_key: Any | None,
) -> Any:
    try:
        header: dict[str, Any] = jwt.get_unverified_header(token)
    except jwt.PyJWTError:
        raise
    if header.get("alg") != "RS256":
        raise jwt.InvalidAlgorithmError("Fiteatsy assertions must use RS256")

    if keyring:
        key_id = header.get("kid")
        if not isinstance(key_id, str) or not key_id:
            raise jwt.InvalidTokenError("Fiteatsy assertion key identifier is required")
        selected = keyring.get(key_id)
        if not selected:
            raise jwt.InvalidTokenError("Fiteatsy assertion key identifier is not trusted")
        return selected

    if not legacy_public_key:
        raise jwt.InvalidTokenError("Fiteatsy assertion verifier is not configured")
    if isinstance(legacy_public_key, str):
        return legacy_public_key.replace("\\n", "\n").strip()
    return legacy_public_key


def decode_fiteatsy_assertion(
    token: str,
    *,
    keyring: Mapping[str, str],
    legacy_public_key: Any | None,
    issuer: str,
    audience: str,
    required_claims: list[str],
) -> dict:
    public_key = select_assertion_key(
        token,
        keyring=keyring,
        legacy_public_key=legacy_public_key,
    )
    return jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        issuer=issuer,
        audience=audience,
        options={"require": required_claims},
    )
