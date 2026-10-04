import pytest

from app.core.exceptions import AppException
from app.core.mobile_identity import canonical_mobile, provider_mobile


@pytest.mark.parametrize(
    ("raw", "canonical"),
    [
        ("+91 97620 06688", "+919762006688"),
        ("9762006688", "+919762006688"),
        ("919762006688", "+919762006688"),
        ("+919762006688", "+919762006688"),
        ("+91-97620-06688", "+919762006688"),
    ],
)
def test_mobile_format_variants_share_one_canonical_identity(raw, canonical):
    assert canonical_mobile(raw) == canonical
    assert provider_mobile(raw) == canonical.removeprefix("+")


@pytest.mark.parametrize("raw", ["", "123", "+abc", "1" * 16])
def test_invalid_mobile_fails_closed(raw):
    with pytest.raises(AppException):
        canonical_mobile(raw)
