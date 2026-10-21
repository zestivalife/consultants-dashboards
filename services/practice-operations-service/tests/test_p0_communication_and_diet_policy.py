import pytest

from app.communications import InvalidPhone, normalize_phone
from app.diet_plan_policy import can_publish_independently


@pytest.mark.parametrize(("value","country","e164","recipient"),[
    ("9876598765","IN","+919876598765","919876598765"),
    ("+919876598765",None,"+919876598765","919876598765"),
    ("919876598765","IN","+919876598765","919876598765"),
    ("00919876598765",None,"+919876598765","919876598765"),
    ("+14155552671",None,"+14155552671","14155552671"),
])
def test_phone_normalization(value,country,e164,recipient):
    assert normalize_phone(value,country)==(e164,recipient)


@pytest.mark.parametrize("value,country",[("9876", "IN"),("9876598765",None),("+123",None)])
def test_phone_normalization_rejects_ambiguous_or_invalid_values(value,country):
    with pytest.raises(InvalidPhone):normalize_phone(value,country)


def test_verified_experience_controls_independent_publication():
    assert can_publish_independently(verification_state="VERIFIED",experience_years=1,plan_status="SAVED",actor_is_author=True)
    assert can_publish_independently(verification_state="VERIFIED",experience_years=12,plan_status="SAVED",actor_is_author=True)
    assert not can_publish_independently(verification_state="VERIFIED",experience_years=0,plan_status="SAVED",actor_is_author=True)
    assert not can_publish_independently(verification_state="UNVERIFIED",experience_years=10,plan_status="SAVED",actor_is_author=True)
    assert not can_publish_independently(verification_state="VERIFIED",experience_years=10,plan_status="DRAFT",actor_is_author=True)
    assert not can_publish_independently(verification_state="VERIFIED",experience_years=10,plan_status="SAVED",actor_is_author=False)
