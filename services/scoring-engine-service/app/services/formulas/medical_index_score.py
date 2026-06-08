"""Medical Index Score computation.

Each biomarker is scored individually against reference ranges,
then aggregated into a medical_index (0-100).
"""

from typing import Any

REFERENCE_RANGES: dict[str, tuple[float, float]] = {
    "vitamin_d": (30.0, 100.0),
    "hba1c": (4.0, 5.6),
    "tsh": (0.4, 4.0),
    "b12": (200.0, 900.0),
    "hdl": (40.0, 60.0),
    "ldl": (0.0, 100.0),
    "triglycerides": (0.0, 150.0),
    "ferritin": (20.0, 200.0),
    "hemoglobin": (12.0, 17.0),
    "crp": (0.0, 3.0),
}


def _score_biomarker(value: float | None, low: float, high: float) -> float:
    if value is None:
        return 0.0
    if low <= value <= high:
        return 100.0
    if value < low:
        diff = low - value
        return max(0.0, 100.0 - diff * 5)
    diff = value - high
    return max(0.0, 100.0 - diff * 5)


def compute(biomarkers: dict[str, Any] | None) -> dict[str, float]:
    if not biomarkers:
        return {
            "vitamin_d": 0.0, "hba1c": 0.0, "thyroid": 0.0, "b12": 0.0,
            "lipid_profile": 0.0, "ferritin": 0.0, "hemoglobin": 0.0,
            "crp": 0.0, "medical_index": 0.0,
        }

    vd = _score_biomarker(biomarkers.get("vitamin_d"), *REFERENCE_RANGES["vitamin_d"])
    hba = _score_biomarker(biomarkers.get("hba1c"), *REFERENCE_RANGES["hba1c"])
    tsh = _score_biomarker(biomarkers.get("tsh"), *REFERENCE_RANGES["tsh"])
    b12 = _score_biomarker(biomarkers.get("b12"), *REFERENCE_RANGES["b12"])

    hdl_s = _score_biomarker(biomarkers.get("hdl"), *REFERENCE_RANGES["hdl"])
    ldl_s = _score_biomarker(biomarkers.get("ldl"), *REFERENCE_RANGES["ldl"])
    trig_s = _score_biomarker(biomarkers.get("triglycerides"), *REFERENCE_RANGES["triglycerides"])
    lipid = (hdl_s + ldl_s + trig_s) / 3.0

    fer = _score_biomarker(biomarkers.get("ferritin"), *REFERENCE_RANGES["ferritin"])
    hgb = _score_biomarker(biomarkers.get("hemoglobin"), *REFERENCE_RANGES["hemoglobin"])
    crp_val = _score_biomarker(biomarkers.get("crp"), *REFERENCE_RANGES["crp"])

    all_scores = [vd, hba, tsh, b12, lipid, fer, hgb, crp_val]
    non_zero = [s for s in all_scores if s > 0]
    medical_index = sum(non_zero) / len(non_zero) if non_zero else 0.0

    return {
        "vitamin_d": round(vd, 2),
        "hba1c": round(hba, 2),
        "thyroid": round(tsh, 2),
        "b12": round(b12, 2),
        "lipid_profile": round(lipid, 2),
        "ferritin": round(fer, 2),
        "hemoglobin": round(hgb, 2),
        "crp": round(crp_val, 2),
        "medical_index": round(medical_index, 2),
    }
