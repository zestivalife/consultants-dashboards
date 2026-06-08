"""Active Performance Score computation.

Components: energy_balance, body_support, nourishment, recovery.
Derived from profile data (BMI, body fat, lifestyle).
"""

from typing import Any


def _energy_balance(weight: float | None, height: float | None, activity_level: str | None) -> float:
    if not weight or not height:
        return 0.0
    height_m = height / 100.0 if height > 3 else height
    bmi = weight / (height_m ** 2)
    base = 50.0 if 18.5 <= bmi <= 24.9 else 30.0
    if activity_level and activity_level.lower() in ("active", "very_active", "high"):
        base += 30.0
    elif activity_level:
        base += 15.0
    return min(100.0, base)


def _body_support(body_fat: float | None, arm: float | None, thigh: float | None) -> float:
    score = 0.0
    if body_fat is not None:
        score += 50.0 if body_fat < 25 else 25.0
    measurements = [v for v in (arm, thigh) if v is not None and v > 0]
    if measurements:
        score += min(50.0, sum(measurements) / len(measurements) * 2)
    return min(100.0, score)


def _nourishment(water: float | None, food_type: str | None) -> float:
    score = 0.0
    if water and water >= 2.0:
        score += 50.0
    elif water:
        score += 25.0
    if food_type and food_type.lower() in ("balanced", "vegetarian", "mediterranean"):
        score += 50.0
    elif food_type:
        score += 25.0
    return min(100.0, score)


def _recovery(sleep: float | None, exercise_freq: int | None) -> float:
    score = 0.0
    if sleep and 7 <= sleep <= 9:
        score += 50.0
    elif sleep and sleep > 0:
        score += 25.0
    if exercise_freq and exercise_freq >= 3:
        score += 50.0
    elif exercise_freq:
        score += 25.0
    return min(100.0, score)


def compute(profile: dict[str, Any]) -> dict[str, float]:
    p = profile.get("profile") or {}
    m = profile.get("measurements") or {}
    lb = profile.get("lifestyle") or {}

    energy = _energy_balance(p.get("weight"), p.get("height"), lb.get("activity_level"))
    body = _body_support(p.get("body_fat_percent"), m.get("arm_circumference"), m.get("thigh_circumference"))
    nourish = _nourishment(lb.get("water_intake"), lb.get("food_type"))
    recov = _recovery(lb.get("sleep_duration"), lb.get("exercise_frequency"))

    total = (energy + body + nourish + recov) / 4.0

    return {
        "energy_balance": round(energy, 2),
        "body_support": round(body, 2),
        "nourishment": round(nourish, 2),
        "recovery": round(recov, 2),
        "active_performance_score": round(total, 2),
    }
