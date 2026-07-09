#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


SERVICES = {
    "api-gateway": os.getenv("GATEWAY_URL"),
    "auth-service": os.getenv("AUTH_SERVICE_URL"),
    "profile-service": os.getenv("PROFILE_SERVICE_URL"),
    "assessment-service": os.getenv("ASSESSMENT_SERVICE_URL"),
    "scoring-engine-service": os.getenv("SCORING_SERVICE_URL"),
    "nutrition-service": os.getenv("NUTRITION_SERVICE_URL"),
}


def fetch_json(url: str) -> tuple[int, dict | str]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=15) as response:
        body = response.read().decode("utf-8")
        try:
            return response.status, json.loads(body)
        except json.JSONDecodeError:
            return response.status, body


def main() -> int:
    failures: list[str] = []

    for service, base_url in SERVICES.items():
        if not base_url:
            print(f"SKIP {service}: URL not provided")
            continue

        for path in ("/health", "/ready"):
            url = base_url.rstrip("/") + path
            try:
                status, payload = fetch_json(url)
                print(f"PASS {service} {path} -> {status}")
                print(json.dumps(payload, indent=2, sort_keys=True) if isinstance(payload, dict) else payload)
                if path == "/health" and status != 200:
                    failures.append(f"{service} health returned {status}")
                if path == "/ready" and status not in (200, 503):
                    failures.append(f"{service} ready returned unexpected status {status}")
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                print(f"FAIL {service} {path} -> {exc.code}\n{body}")
                failures.append(f"{service} {path} returned {exc.code}")
            except Exception as exc:
                print(f"FAIL {service} {path} -> {exc}")
                failures.append(f"{service} {path} error: {exc}")

    if failures:
        print("\nHealth verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nHealth verification completed without detected failures.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
