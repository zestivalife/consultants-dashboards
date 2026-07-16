import pytest

from app.core.password_policy import WeakPasswordException, validate_password


def test_valid_password():
    validate_password("StrongP4ssword!")


def test_too_short():
    with pytest.raises(WeakPasswordException, match="12 characters"):
        validate_password("Ab1")


def test_no_uppercase():
    with pytest.raises(WeakPasswordException, match="uppercase"):
        validate_password("alllowercase1!")


def test_no_lowercase():
    with pytest.raises(WeakPasswordException, match="lowercase"):
        validate_password("ALLUPPERCASE1!")


def test_no_digit():
    with pytest.raises(WeakPasswordException, match="digit"):
        validate_password("NoDigitsHere!")


def test_no_special_character():
    with pytest.raises(WeakPasswordException, match="special"):
        validate_password("NoSpecial123")


def test_common_password():
    with pytest.raises(WeakPasswordException, match="commonly used"):
        validate_password("Password123!")


def test_multiple_failures():
    with pytest.raises(WeakPasswordException) as exc_info:
        validate_password("short")
    assert len(exc_info.value.reasons) >= 2
