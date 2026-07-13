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
    """Ritorna l'istanza CloakBrowser condivisa, lanciandola al primo uso.

    Singleton: il lancio di Chromium costa secondi, riusiamo lo stesso browser
    per tutta la run. Se l'istanza esistente è morta (il test new_page fallisce)
    viene rilanciata. Il fingerprint è fissato da CLOAKBROWSER_FINGERPRINT_SEED
    per avere un'identità browser stabile tra le run.
    """
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
    """Apre una pagina con il timeout di default configurato (CLOAKBROWSER_PAGE_TIMEOUT)."""
    if browser is None:
        browser = get_browser()
    page = browser.new_page()
    page.set_default_timeout(CLOAKBROWSER_PAGE_TIMEOUT)
    return page


def close_browser():
    """Chiude il singleton a fine run (best-effort) e azzera il riferimento."""
    global _browser_instance
    if _browser_instance is not None:
        try:
            _browser_instance.close()
        except Exception as exc:
            logger.warning("Error closing CloakBrowser: %s", exc)
        _browser_instance = None


def fetch_page_html(url: str, wait_for: str = "body", timeout: int = CLOAKBROWSER_PAGE_TIMEOUT) -> str:
    """Carica una pagina nel browser reale e ritorna l'HTML renderizzato.

    Fallback per i siti che bloccano requests o renderizzano via JavaScript.
    `wait_for` = selettore CSS che segnala "contenuto pronto"; lo sleep(1)
    successivo lascia assestare eventuali fetch client-side residui.
    """
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
