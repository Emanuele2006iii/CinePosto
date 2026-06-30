"""Shared HTTP helper: retry_request with exponential backoff, 403 non-retried."""
from __future__ import annotations

import logging
import time

import requests

from scraper.config import REQUEST_RETRY, REQUEST_TIMEOUT, RETRY_BACKOFF

logger = logging.getLogger(__name__)


def retry_request(
    method: str,
    url: str,
    session: requests.Session,
    label: str = "",
    **kwargs,
) -> requests.Response:
    last_exc = None
    for attempt in range(1, REQUEST_RETRY + 1):
        try:
            resp = getattr(session, method)(url, timeout=REQUEST_TIMEOUT, **kwargs)
            if resp.status_code == 403:
                logger.error("%s 403 Forbidden for %s — not retrying (permanent block)", label, url)
                resp.raise_for_status()  # raises and exits; line below never reached
            resp.raise_for_status()
            return resp
        except requests.HTTPError as exc:
            last_exc = exc
            if exc.response is not None and exc.response.status_code == 403:
                raise
            logger.warning("%s retry %d/%d for %s: %s", label, attempt, REQUEST_RETRY, url, exc)
            if attempt < REQUEST_RETRY:
                time.sleep(RETRY_BACKOFF**attempt)
        except requests.RequestException as exc:
            last_exc = exc
            logger.warning("%s retry %d/%d for %s: %s", label, attempt, REQUEST_RETRY, url, exc)
            if attempt < REQUEST_RETRY:
                time.sleep(RETRY_BACKOFF**attempt)
    raise last_exc
