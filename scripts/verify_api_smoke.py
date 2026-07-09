#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request


BASE_URL = os.getenv("GATEWAY_URL", "").rstrip("/")
if not BASE_URL:
    print("GATEWAY_URL is required")
    sys.exit(2)


def request(
    method: str,
    path: str,
    payload: dict | None = None,
    token: str | None = None,
    expected: tuple[int, ...] = (200,),
    content_type: str = "application/json",
) -> dict:
    headers = {"Accept": "application/json"}
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        headers["Content-Type"] = content_type
        data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(f"{BASE_URL}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            body = response.read().decode("utf-8")
            parsed = json.loads(body) if body else {}
            if response.status not in expected:
                raise RuntimeError(f"{method} {path} expected {expected}, got {response.status}: {body}")
            print(f"PASS {method} {path} -> {response.status}")
            return parsed
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if exc.code not in expected:
            raise RuntimeError(f"{method} {path} expected {expected}, got {exc.code}: {body}") from exc
        print(f"PASS {method} {path} -> {exc.code}")
        return json.loads(body) if body else {}


def main() -> int:
    stamp = int(time.time())
    email = f"railway-smoke-{stamp}@example.com"
    password = "NuetraSmoke!234"

    register_payload = {
        "email": email,
        "password": password,
        "role": "consultant",
        "companyName": "Nuetra QA",
        "location": "IN",
        "employees": 25,
        "industry": "healthcare",
    }
    register = request("POST", "/api/v1/auth/register", register_payload, expected=(201,))
    otp_code = register["data"]["otp_code"]

    request("POST", "/api/v1/auth/verify-otp", {"email": email, "otp": otp_code})
    login = request("POST", "/api/v1/auth/login", {"email": email, "password": password})
    access_token = login["data"]["tokens"]["access_token"]
    user_id = login["data"]["user"]["id"]

    request("GET", "/api/v1/auth/me", token=access_token)

    profile_payload = {
        "profile": {
            "age": 34,
            "sex": "male",
            "height": 178,
            "weight": 81,
            "body_fat_percent": 23,
        },
        "measurements": {
            "arm_circumference": 31,
            "thigh_circumference": 52,
            "calf_circumference": 36,
        },
        "biomarkers": {
            "vitamin_d": 28,
            "hba1c": 5.7,
            "tsh": 2.4,
            "b12": 390,
        },
        "lifestyle": {
            "activity_level": "moderate",
            "exercise_frequency": 4,
            "daily_steps": 9000,
            "sleep_duration": 7.2,
            "sleep_consistency": 7,
            "stress_level": 4,
            "water_intake": 2.8,
            "food_type": "vegetarian",
        },
        "nutrition": {
            "meal_frequency": 3,
            "protein_intake": "medium",
            "water_intake": 2.8,
            "food_source": "home-cooked",
            "target_protein": 120,
            "target_fat": 55,
            "target_carbs": 180,
            "target_calories": 2100,
        },
        "goals": [
            {"goal_type": "better_energy", "is_primary": True},
            {"goal_type": "weight_loss", "is_primary": False},
        ],
    }
    request("POST", "/api/v1/profile", profile_payload, token=access_token, expected=(201,))
    request("GET", "/api/v1/profile/me", token=access_token)
    request(
        "PUT",
        "/api/v1/profile/me",
        {"profile": {"weight": 79.5}, "goals": [{"goal_type": "better_sleep", "is_primary": True}]},
        token=access_token,
    )
    request("GET", "/api/v1/profile/onboarding-status", token=access_token)

    assessment_payload = {"answers": [{"question_id": 1, "response_value": 3}, {"question_id": 2, "response_value": 4}]}
    request("POST", "/api/v1/assessments/pss10", assessment_payload, token=access_token, expected=(201,))
    request("POST", "/api/v1/assessments/physical-ease", assessment_payload, token=access_token, expected=(201,))
    request("GET", "/api/v1/assessments/history", token=access_token)

    diet_plan = request(
        "POST",
        "/api/v1/nutrition/diet-plan",
        {
            "name": f"Smoke Test Plan {stamp}",
            "description": "Railway smoke test diet plan",
            "calorie_target": 2100,
            "protein_target": 120,
            "fat_target": 55,
            "carb_target": 180,
            "meals": [
                {
                    "meal_type": "breakfast",
                    "meal_name": "Oats Bowl",
                    "calories": 450,
                    "protein": 20,
                    "carbs": 55,
                    "fats": 12,
                }
            ],
        },
        token=access_token,
        expected=(201,),
    )
    plan_id = diet_plan["data"]["id"]
    request("GET", "/api/v1/nutrition/templates", token=access_token)
    request(
        "POST",
        "/api/v1/nutrition/assign",
        {"user_id": user_id, "diet_plan_id": plan_id},
        token=access_token,
        expected=(201,),
    )
    request("GET", "/api/v1/nutrition/my-plan", token=access_token)

    request("POST", "/api/v1/scoring/compute?force=true", token=access_token, expected=(200, 201))
    request("GET", "/api/v1/scoring/me", token=access_token)
    request("GET", "/api/v1/scoring/timeline", token=access_token)

    print("\nAPI smoke test completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
