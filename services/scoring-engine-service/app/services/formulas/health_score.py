"""Health Score computation.

Components: BMI, WHR (waist-hip approximation from body fat), muscle,
stress (from PSS-10 count), lifestyle (from lifestyle_baseline).
Each sub-score is 0–100; total is the weighted average.
"""

from typing import Any


def _bmi(weight: float | None, height: float | None) -> float:
    if not weight or not height or height <= 0:
        return 0.0
    height_m = height / 100.0 if height > 3 else height
    bmi = weight / (height_m ** 2)
    if 18.5 <= bmi <= 24.9:
        return 100.0
    elif bmi < 18.5:
        return max(0.0, 100.0 - (18.5 - bmi) * 10)
    else:
        return max(0.0, 100.0 - (bmi - 24.9) * 5)


def _whr(body_fat_percent: float | None) -> float:
    if body_fat_percent is None:
        return 0.0
    if body_fat_percent < 15:
        return 100.0
    elif body_fat_percent <= 25:
        return 80.0
    elif body_fat_percent <= 35:
        return 50.0
    return 20.0


def _muscle(arm: float | None, thigh: float | None, calf: float | None) -> float:
    values = [v for v in (arm, thigh, calf) if v is not None and v > 0]
    if not values:
        return 0.0
    avg = sum(values) / len(values)
    return min(100.0, avg * 3)


def _stress_from_pss(has_pss: bool) -> float:
    return 60.0 if has_pss else 0.0


def _lifestyle(baseline: dict[str, Any] | None) -> float:
    if not baseline:
        return 0.0
    score = 0.0
    steps = baseline.get("daily_steps") or 0
    score += min(30.0, steps / 333.0)
    sleep = baseline.get("sleep_duration") or 0
    if 7 <= sleep <= 9:
        score += 30.0
    elif sleep > 0:
        score += 15.0
    water = baseline.get("water_intake") or 0
    score += min(20.0, water * 8)
    freq = baseline.get("exercise_frequency") or 0
    score += min(20.0, freq * 5)
    return min(100.0, score)


def compute(profile: dict[str, Any], has_pss: bool = False) -> dict[str, float]:
    p = profile.get("profile") or {}
    m = profile.get("measurements") or {}
    lb = profile.get("lifestyle") or {}

    bmi_score = _bmi(p.get("weight"), p.get("height"))
    whr_score = _whr(p.get("body_fat_percent"))
    muscle_score = _muscle(m.get("arm_circumference"), m.get("thigh_circumference"), m.get("calf_circumference"))
    stress_score = _stress_from_pss(has_pss)
    lifestyle_score = _lifestyle(lb)

    weights = [0.25, 0.15, 0.15, 0.20, 0.25]
    components = [bmi_score, whr_score, muscle_score, stress_score, lifestyle_score]
    total = sum(w * c for w, c in zip(weights, components))

    return {
        "bmi_score": round(bmi_score, 2),
        "whr_score": round(whr_score, 2),
        "muscle_score": round(muscle_score, 2),
        "stress_score": round(stress_score, 2),
        "lifestyle_score": round(lifestyle_score, 2),
        "total_health_score": round(total, 2),
    }
