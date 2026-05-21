#!/usr/bin/env python3
"""Smoke test against deployed Pulseboard API. Run: python scripts/smoke_test_live.py"""

from __future__ import annotations

import os
import sys
import uuid

import httpx

API_BASE = os.getenv("SMOKE_API_BASE", "https://analytics-platform-2-kpih.onrender.com/api/v1")
ROOT = os.getenv("SMOKE_ROOT", "https://analytics-platform-2-kpih.onrender.com")


def ok(label: str, condition: bool, detail: str = "") -> bool:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}" + (f" — {detail}" if detail else ""))
    return condition


def main() -> int:
    print(f"Smoke testing {ROOT}\n")
    passed = 0
    total = 0

    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
        total += 1
        r = client.get(f"{ROOT}/health")
        passed += ok("Health", r.status_code == 200 and r.json().get("status") == "ok", r.text[:80])

        total += 1
        r = client.get(f"{ROOT}/metrics")
        passed += ok("Metrics", r.status_code == 200, r.text[:80])

        total += 1
        r = client.get(f"{ROOT}/openapi.json")
        passed += ok("OpenAPI", r.status_code == 200 and "paths" in r.json())

        email = f"smoke_{uuid.uuid4().hex[:8]}@example.com"
        password = "SmokeTest123!"
        org = f"Smoke Org {uuid.uuid4().hex[:6]}"

        total += 1
        r = client.post(
            f"{API_BASE}/auth/signup",
            json={"email": email, "password": password, "organization_name": org, "role": "Viewer"},
        )
        passed += ok("Signup", r.status_code == 201, f"status={r.status_code}")

        total += 1
        r = client.post(
            f"{API_BASE}/auth/login",
            data={"username": email, "password": password},
        )
        token = r.json().get("access_token") if r.status_code == 200 else None
        passed += ok("Login", bool(token))

        if not token:
            print("\nStopping — auth failed.")
            print(f"\n{passed}/{total} checks passed")
            return 1

        headers = {"Authorization": f"Bearer {token}"}

        total += 1
        r = client.get(f"{API_BASE}/auth/me", headers=headers)
        passed += ok("Me", r.status_code == 200 and r.json().get("email") == email)

        total += 1
        r = client.get(f"{API_BASE}/dashboards/", headers=headers)
        passed += ok("Dashboards list", r.status_code == 200)

        total += 1
        r = client.get(f"{API_BASE}/dashboards/templates", headers=headers)
        passed += ok("Dashboard templates", r.status_code == 200 and len(r.json()) >= 1)

        total += 1
        r = client.get(f"{API_BASE}/alerts/", headers=headers)
        passed += ok("Alerts list", r.status_code == 200)

        total += 1
        r = client.get(f"{API_BASE}/events/recent", headers=headers)
        passed += ok("Recent events", r.status_code == 200)

        total += 1
        r = client.post(
            f"{API_BASE}/dashboards/",
            headers=headers,
            json={"name": "Smoke Dashboard", "description": "auto", "is_public": False, "refresh_interval_seconds": 60},
        )
        passed += ok("Create dashboard", r.status_code == 201, f"status={r.status_code}")

    print(f"\n{passed}/{total} checks passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
