import pytest
from pydantic import ValidationError

from app.contracts import GovernedDietOptionUpdate


def valid_payload():
    return {
        "expected_version": 3,
        "meal_head": "LUNCH",
        "components": [{"food_id": "food-1", "serving_id": "serving-1", "multiplier": 1}],
    }


def test_governed_option_contract_accepts_only_complete_versioned_options():
    value = GovernedDietOptionUpdate.model_validate(valid_payload())
    assert value.expected_version == 3
    assert value.components[0].multiplier == 1


@pytest.mark.parametrize("change", [
    {"expected_version": 0},
    {"meal_head": "BRUNCH"},
    {"components": []},
    {"components": [{"food_id": "", "serving_id": "serving-1", "multiplier": 1}]},
    {"components": [{"food_id": "food-1", "serving_id": "", "multiplier": 1}]},
    {"components": [{"food_id": "food-1", "serving_id": "serving-1", "multiplier": 0}]},
])
def test_governed_option_contract_rejects_partial_or_invalid_mutations(change):
    payload = valid_payload()
    payload.update(change)
    with pytest.raises(ValidationError):
        GovernedDietOptionUpdate.model_validate(payload)
