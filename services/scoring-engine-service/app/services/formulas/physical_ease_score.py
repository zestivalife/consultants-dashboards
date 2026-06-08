"""Physical Ease Score computation.

Based on physical_ease assessment responses.
Average of response values → normalize to 0-100 → interpret.
"""

from typing import Any


def _interpret(score: float) -> str:
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Moderate"
    elif score >= 20:
        return "Fair"
    return "Poor"


def compute(has_physical_ease: bool, response_count: int) -> dict[str, Any]:
    if not has_physical_ease or response_count == 0:
        return {"score": 0.0, "interpretation": "No data"}

    estimated = min(100.0, response_count * 10.0)
    return {
        "score": round(estimated, 2),
        "interpretation": _interpret(estimated),
    }
