from app.intake_truth import calculate_intake_truth, meaningful_intake_answer


def test_empty_values_are_not_counted_as_answers():
    for value in (None, "", "   ", [], {}, ["  "], {"value": ""}):
        assert meaningful_intake_answer(value) is False


def test_false_and_zero_are_valid_answers():
    assert meaningful_intake_answer(False) is True
    assert meaningful_intake_answer(0) is True


def test_completion_and_required_truth_are_value_based():
    result = calculate_intake_truth([
        {"question_key": "name", "required": True, "answer": "Priyanshi"},
        {"question_key": "allergies", "required": True, "answer": []},
        {"question_key": "notes", "required": False, "answer": ""},
        {"question_key": "consent", "required": True, "answer": False},
    ])
    assert result == {
        "answered": 2,
        "total": 4,
        "completion_percent": 50,
        "missing_required": ["allergies"],
    }
