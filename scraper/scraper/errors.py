"""Atomic write of per-run errors to errors.json, with deduplication by date."""
from __future__ import annotations

from datetime import datetime
import json
import logging
import os

from scraper.config import ERRORS_JSON
from scraper.models import CinemaError

logger = logging.getLogger(__name__)


def make_error(
    cinema: str,
    exc: Exception,
    phase: str,
    url: str | None = None,
    detail: str | None = None,
) -> CinemaError:
    """Costruisce un CinemaError dall'eccezione, con timestamp corrente."""
    return CinemaError(
        cinema=cinema,
        timestamp=datetime.now().isoformat(),
        exception=type(exc).__name__,
        phase=phase,
        url=url,
        detail=detail if detail is not None else str(exc),
    )


def _write_atomic_errors(data: dict) -> None:
    """Scrive errors.json con pattern tmp-then-replace: mai un file mezzo scritto su disco."""
    tmp = str(ERRORS_JSON) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, str(ERRORS_JSON))


def write_errors(errors: list[CinemaError], today: str) -> None:
    """Aggiorna errors.json con gli errori della run odierna.

    Gli errori di run precedenti nella stessa data vengono sostituiti (non
    accumulati); con zero errori la giornata viene ripulita e marcata con
    `last_clean_date` — così il monitoraggio distingue "tutto ok" da "non ha girato".
    """
    if not errors:
        if ERRORS_JSON.exists():
            try:
                with open(ERRORS_JSON, encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = {"errors": []}

            existing["errors"] = [
                e for e in existing.get("errors", [])
                if not e.get("timestamp", "").startswith(today)
            ]
            existing["last_clean_date"] = today
            _write_atomic_errors(existing)
        return

    try:
        if ERRORS_JSON.exists():
            with open(ERRORS_JSON, encoding="utf-8") as f:
                existing = json.load(f)
        else:
            existing = {"errors": []}

        new_errors = [e.to_dict() for e in errors]
        existing["errors"] = [
            e for e in existing.get("errors", [])
            if not e.get("timestamp", "").startswith(today)
        ] + new_errors
        existing["last_error_date"] = today
        existing["last_error_timestamp"] = datetime.now().isoformat()

        _write_atomic_errors(existing)
        logger.info("Wrote %d errors to %s", len(new_errors), ERRORS_JSON)
    except Exception as exc:
        logger.error("Failed to write errors.json: %s", exc, exc_info=True)
