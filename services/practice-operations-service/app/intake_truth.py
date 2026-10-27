def meaningful_intake_answer(value):
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return any(meaningful_intake_answer(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(meaningful_intake_answer(item) for item in value)
    return True


def calculate_intake_truth(question_answers):
    rows = list(question_answers)
    answered = sum(1 for row in rows if meaningful_intake_answer(row.get("answer")))
    missing_required = [
        row.get("question_key")
        for row in rows
        if row.get("required") and not meaningful_intake_answer(row.get("answer"))
    ]
    total = len(rows)
    return {
        "answered": answered,
        "total": total,
        "completion_percent": round((answered / max(total, 1)) * 100),
        "missing_required": [key for key in missing_required if key],
    }
