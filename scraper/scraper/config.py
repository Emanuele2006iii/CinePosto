"""Runtime configuration: paths, URLs, API constants, and timezone helpers."""
from __future__ import annotations

from datetime import date, datetime, timedelta
import os
from pathlib import Path
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
HISTORY_DIR = OUTPUT_DIR / "history"
CACHE_DIR = OUTPUT_DIR / "cache"
MOVIES_JSON = OUTPUT_DIR / "movies.json"
ERRORS_JSON = OUTPUT_DIR / "errors.json"
CINEMAS_JSON = OUTPUT_DIR / "cinemas.json"

# Coordinate approssimate - verificare prima del deploy della mappa
CINEMA_LOCATIONS: dict[str, dict] = {
    "postmodernissimo": {
        "name": "PostModernissimo",
        # Verificato dal sito ufficiale postmodernissimo.com (2026-07-02)
        "address": "Via del Carmine 4, 06121 Perugia PG",
        "city": "Perugia",
        "region": "Umbria",
        "lat": 43.1129,
        "lon": 12.3933,
        "website": "https://www.postmodernissimo.com",
    },
    "the-space-corciano": {
        "name": "The Space Cinema Corciano",
        # Verificato dal sito ufficiale thespacecinema.it (2026-07-02)
        "address": "Via Pierluigi Nervi, 06073 Corciano PG",
        "city": "Corciano",
        "region": "Umbria",
        "lat": 43.0990,
        "lon": 12.3144,
        "website": "https://www.thespacecinema.it",
    },
    "uci-perugia": {
        "name": "UCI Cinemas Perugia",
        # Indirizzo indicato da Emanuele (2026-07-02). Verificare su Maps.
        "address": "Viale Centova 1D, 06100 Perugia PG",
        "city": "Perugia",
        "region": "Umbria",
        "lat": 43.0965,
        "lon": 12.3554,
        "website": "https://ucicinemas.it",
    },
}
SCRAPER_LOG = BASE_DIR / "scraper.log"
WIKIDATA_CACHE = BASE_DIR / ".wikidata_cache.json"

# CinePosto scraper operates in Italian local time. The server may run in UTC,
# so we always compute "today" in Europe/Rome regardless of the host timezone.
# Configurable via the SCRAPER_TZ env var for future deployment in other regions.
SCRAPER_TZ = ZoneInfo(os.environ.get("SCRAPER_TZ", "Europe/Rome"))

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

FILMS_JSON = OUTPUT_DIR / "films.json"
SHOWINGS_JSON = OUTPUT_DIR / "showings.json"

CITY = "Perugia"

THE_SPACE_CINEMA_ID = 1027  # venue ID from the TheSpace API (hardcoded for cinema/corciano)
THE_SPACE_CINEMA_NAME = "The Space Cinema Corciano"
THE_SPACE_CINEMA_SLUG = "the-space-corciano"
THE_SPACE_BASE_URL = "https://www.thespacecinema.it"
THE_SPACE_API_BASE = f"{THE_SPACE_BASE_URL}/api/microservice"
THE_SPACE_AUTH_URL = f"{THE_SPACE_API_BASE}/auth/token"
THE_SPACE_FILMS_URL = f"{THE_SPACE_API_BASE}/showings/cinemas/{THE_SPACE_CINEMA_ID}/films"
THE_SPACE_FILM_DETAIL_URL = f"{THE_SPACE_BASE_URL}/film/{{film_slug}}"
THE_SPACE_CINEMA_URL = f"{THE_SPACE_BASE_URL}/cinema/corciano/al-cinema"

UCI_CINEMA_NAME = "UCI Cinemas Perugia"
UCI_CINEMA_SLUG = "uci-perugia"
UCI_BASE_URL = "https://ucicinemas.it"
UCI_CINEMA_URL = f"{UCI_BASE_URL}/cinema/perugia/"
# Undocumented Cloud Run backend — reverse-engineered from XHR traffic. May change on redeployment.
UCI_API_BASE = "https://myuci---uci-backend-production-nfluwp7wga-oc.a.run.app"
UCI_PROGRAMMING_URL = f"{UCI_API_BASE}/api/theatres/uci-cinemas-perugia/programming/{{date}}"

POSTMOD_CINEMA_NAME = "PostModernissimo"
POSTMOD_CINEMA_SLUG = "postmodernissimo"
POSTMOD_BASE_URL = "https://www.postmodernissimo.com"
POSTMOD_CINEMA_URL = POSTMOD_BASE_URL
REQUEST_TIMEOUT = 30

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)
REQUEST_RETRY = 3
RETRY_BACKOFF = 2

CLOAKBROWSER_FINGERPRINT_SEED = int(os.environ.get("CLOAKBROWSER_FINGERPRINT_SEED", "42069"))
CLOAKBROWSER_HEADLESS = os.environ.get("CLOAKBROWSER_HEADLESS", "true").lower() == "true"
CLOAKBROWSER_PAGE_TIMEOUT = 30000  # milliseconds (Playwright timeout unit)

SCHEDULE_INTERVAL_HOURS = 24
REMOVAL_THRESHOLD_DAYS = 7  # days without showings → "rimosso"; 2× this value → permanent purge
SCRAPER_RETRY_DELAY = 300  # seconds before retrying a failed connector (5 min — outlasts most CDN TTLs)

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
# Wikimedia policy: identifica un endpoint contattabile reale.
WIKIDATA_USER_AGENT = "CinePosto/1.0 (https://github.com/Emanuele2006iii/CinePosto; emanuele.ceccariglia@gmail.com)"
WIKIDATA_TIMEOUT = 15

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_LEVEL = os.environ.get("SCRAPER_LOG_LEVEL", "INFO")


def get_week_dates(ref_date: date | None = None) -> list[str]:
    """Le 8 date ISO da coprire a ogni run: oggi + 7 giorni (finestra di scraping)."""
    d = ref_date or today_local()
    return [(d + timedelta(days=i)).isoformat() for i in range(8)]


def today_local() -> date:
    """Return today's date in the scraper's local timezone.

    Uses `SCRAPER_TZ` (default `Europe/Rome`) so that the scraper rolls over
    to the new "today" at Italian midnight, regardless of the server timezone.
    """
    return datetime.now(SCRAPER_TZ).date()
