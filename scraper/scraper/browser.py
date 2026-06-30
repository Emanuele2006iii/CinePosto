"""CloakBrowser singleton: anti-fingerprint Chromium via Playwright, used as fallback for bot-protected sites."""
from __future__ import annotations

import logging
import time

from scraper.config import (
    CLOAKBROWSER_FINGERPRINT_SEED,
    CLOAKBROWSER_HEADLESS,
    CLOAKBROWSER_PAGE_TIMEOUT,
)

logger = logging.getLogger(__name__)

_browser_instance = None
_page_instance = None


def get_browser():
    global _browser_instance
    if _browser_instance is not None:
        try:
            page = _browser_instance.new_page()
            page.close()
            return _browser_instance
        except Exception:
            _browser_instance = None

    try:
        from cloakbrowser import launch

        logger.info("Launching CloakBrowser (headless=%s, seed=%s)", CLOAKBROWSER_HEADLESS, CLOAKBROWSER_FINGERPRINT_SEED)
        _browser_instance = launch(
            headless=CLOAKBROWSER_HEADLESS,
            humanize=True,
            args=[
                f"--fingerprint={CLOAKBROWSER_FINGERPRINT_SEED}",
                "--disable-gpu",
                "--disable-software-rasterizer",
            ],
        )
        return _browser_instance
    except ImportError:
        logger.error("cloakbrowser not installed. Run: pip install cloakbrowser")
        raise
    except Exception as exc:
        logger.error("CloakBrowser launch failed: %s", exc, exc_info=True)
        _browser_instance = None
        raise


def new_page(browser=None):
    if browser is None:
        browser = get_browser()
    page = browser.new_page()
    page.set_default_timeout(CLOAKBROWSER_PAGE_TIMEOUT)
    return page


def close_browser():
    global _browser_instance
    if _browser_instance is not None:
        try:
            _browser_instance.close()
        except Exception as exc:
            logger.warning("Error closing CloakBrowser: %s", exc)
        _browser_instance = None


def fetch_page_html(url: str, wait_for: str = "body", timeout: int = CLOAKBROWSER_PAGE_TIMEOUT) -> str:
    browser = get_browser()
    page = new_page(browser)
    try:
        logger.info("CloakBrowser navigating to %s", url)
        page.goto(url, timeout=timeout)
        if wait_for:
            page.wait_for_selector(wait_for, timeout=timeout)
        time.sleep(1)
        html = page.content()
        return html
    finally:
        try:
            page.close()
        except Exception:
            pass
