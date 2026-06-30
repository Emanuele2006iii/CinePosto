"""
Ping the three cinema endpoints and report their status.

Usage (from CinemaScarper root):
    python healthcheck.py

Exit code 0 = all OK, 1 = at least one failure.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import sys
import time

import requests

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[0]))

from scraper.config import (
    DEFAULT_USER_AGENT,
    POSTMOD_CINEMA_URL,
    THE_SPACE_AUTH_URL,
    UCI_PROGRAMMING_URL,
)

TIMEOUT = 10

UA = DEFAULT_USER_AGENT


@dataclass
class CheckResult:
    cinema: str
    endpoint: str
    ok: bool
    status: int | None
    elapsed_ms: int
    error: str | None = None


def _get(cinema: str, url: str, **kwargs) -> CheckResult:
    t0 = time.monotonic()
    try:
        resp = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": UA}, **kwargs)
        elapsed = int((time.monotonic() - t0) * 1000)
        ok = resp.status_code < 400
        return CheckResult(cinema=cinema, endpoint=url, ok=ok, status=resp.status_code, elapsed_ms=elapsed)
    except Exception as exc:
        elapsed = int((time.monotonic() - t0) * 1000)
        return CheckResult(cinema=cinema, endpoint=url, ok=False, status=None, elapsed_ms=elapsed, error=str(exc))


def _post(cinema: str, url: str, **kwargs) -> CheckResult:
    t0 = time.monotonic()
    try:
        resp = requests.post(url, timeout=TIMEOUT, headers={"User-Agent": UA, "Accept": "application/json"}, **kwargs)
        elapsed = int((time.monotonic() - t0) * 1000)
        ok = resp.status_code < 400
        return CheckResult(cinema=cinema, endpoint=url, ok=ok, status=resp.status_code, elapsed_ms=elapsed)
    except Exception as exc:
        elapsed = int((time.monotonic() - t0) * 1000)
        return CheckResult(cinema=cinema, endpoint=url, ok=False, status=None, elapsed_ms=elapsed, error=str(exc))


def run_checks() -> list[CheckResult]:
    today = date.today().isoformat()
    return [
        _get("PostModernissimo", POSTMOD_CINEMA_URL),
        _post("The Space (auth)", THE_SPACE_AUTH_URL, json={}),
        _get("UCI", UCI_PROGRAMMING_URL.format(date=today)),
    ]


def print_report(results: list[CheckResult]) -> None:
    print(f"\n{'Cinema':<25} {'Status':>6}  {'Time':>7}  Result")
    print("-" * 60)
    for r in results:
        status_str = str(r.status) if r.status else "ERR"
        mark = "OK" if r.ok else "FAIL"
        print(f"{r.cinema:<25} {status_str:>6}  {r.elapsed_ms:>5}ms  {mark}")
        if r.error:
            print(f"  {'':25} {r.error}")
    print()


if __name__ == "__main__":
    results = run_checks()
    print_report(results)
    if any(not r.ok for r in results):
        print("One or more endpoints are down.")
        sys.exit(1)
    print("All endpoints OK.")
