"""Wikidata enrichment: fetches poster, description, director, duration, original title, year, wikidata_id."""
from __future__ import annotations

import json
import logging
import re
import time

import requests

from scraper.config import (
    WIKIDATA_CACHE,
    WIKIDATA_ENDPOINT,
    WIKIDATA_TIMEOUT,
    WIKIDATA_USER_AGENT,
)
from scraper.models import Film
from scraper.normalizer import normalize_title

logger = logging.getLogger(__name__)

_cache: dict[str, dict] = {}
_last_query_time: float = 0.0
_MIN_QUERY_INTERVAL = 5.0  # Wikidata public SPARQL throttles aggressive clients; 5s stays well under the limit
_consecutive_failures: int = 0
_MAX_CONSECUTIVE_FAILURES = 3
_rate_limited_until: float = 0.0
_MISS_SENTINEL = "__NOT_FOUND__"  # distinguishes "searched, not found" from "not yet searched" (absent key)


def _load_cache() -> dict[str, dict]:
    """Carica la cache Wikidata da disco (una volta per processo, poi resta in memoria).

    NB: dopo aver modificato la logica di estrazione (nuove property) va
    invalidata a mano: `rm .wikidata_cache.json` — vedi docs/development.md.
    """
    global _cache
    if _cache:
        return _cache
    if WIKIDATA_CACHE.exists():
        try:
            with open(WIKIDATA_CACHE, encoding="utf-8") as f:
                _cache = json.load(f)
        except Exception:
            _cache = {}
    return _cache


def _save_cache() -> None:
    """Persiste la cache su disco a ogni aggiornamento (best-effort)."""
    try:
        with open(WIKIDATA_CACHE, "w", encoding="utf-8") as f:
            json.dump(_cache, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        logger.warning("Wikidata cache save failed: %s", exc)


def _sparql_query(query: str) -> list[dict] | None:
    """Esegue una query SPARQL sull'endpoint pubblico Wikidata, da buon cittadino.

    Tre protezioni contro il ban: intervallo minimo di 5s tra query, rispetto
    del Retry-After sul 429, e circuit breaker che smette di interrogare dopo
    3 fallimenti consecutivi (l'arricchimento degrada, la run non muore).
    Ritorna i bindings o None su errore.
    """
    global _last_query_time, _consecutive_failures, _rate_limited_until
    if _consecutive_failures >= _MAX_CONSECUTIVE_FAILURES:
        logger.warning("Wikidata: skipping query after %d consecutive failures", _consecutive_failures)
        return None
    now = time.time()
    if now < _rate_limited_until:
        wait = _rate_limited_until - now
        logger.info("Wikidata: rate-limited, waiting %.0fs", wait)
        time.sleep(wait)
    headers = {
        "User-Agent": WIKIDATA_USER_AGENT,
        "Accept": "application/sparql-results+json",
    }
    elapsed = time.time() - _last_query_time
    if elapsed < _MIN_QUERY_INTERVAL:
        time.sleep(_MIN_QUERY_INTERVAL - elapsed)
    try:
        _last_query_time = time.time()
        resp = requests.get(
            WIKIDATA_ENDPOINT,
            params={"query": query, "format": "json"},
            headers=headers,
            timeout=WIKIDATA_TIMEOUT,
        )
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", "30"))
            _rate_limited_until = time.time() + retry_after
            _consecutive_failures += 1
            logger.warning("Wikidata 429 rate limit, backing off %ds (%d/%d)", retry_after, _consecutive_failures, _MAX_CONSECUTIVE_FAILURES)
            return None
        resp.raise_for_status()
        data = resp.json()
        bindings = data.get("results", {}).get("bindings", [])
        if bindings:
            _consecutive_failures = 0
            _rate_limited_until = 0.0
        return bindings
    except Exception as exc:
        _consecutive_failures += 1
        logger.warning("Wikidata SPARQL query failed (%d/%d): %s", _consecutive_failures, _MAX_CONSECUTIVE_FAILURES, exc)
        return None


def _search_wikidata(title: str) -> dict | None:
    """Cerca i metadati di un film, passando prima dalla cache.

    Anche i MISS vengono cachati (sentinella): un film di nicchia assente da
    Wikidata non genera una ricerca a ogni run notturna.
    """
    cache = _load_cache()
    key = normalize_title(title).lower()
    if key in cache:
        cached = cache[key]
        return None if cached == _MISS_SENTINEL else cached

    result = _search_fuzzy(title)

    if result:
        cache[key] = result
        _save_cache()
        time.sleep(2)
        return result

    cache[key] = _MISS_SENTINEL
    _save_cache()
    time.sleep(1)
    return None



def _search_fuzzy(title: str) -> dict | None:
    """Cerca il titolo con l'API wbsearchentities (lingua it) e filtra i soli film.

    Il filtro sulla description ("film"/"movie") evita di agganciare l'omonimo
    libro, videogioco o persona.
    """
    try:
        resp = requests.get(
            "https://www.wikidata.org/w/api.php",
            params={
                "action": "wbsearchentities",
                "search": title,
                "language": "it",
                "limit": 5,
                "type": "item",
                "format": "json",
            },
            headers={"User-Agent": WIKIDATA_USER_AGENT},
            timeout=WIKIDATA_TIMEOUT,
        )
        resp.raise_for_status()
        results = resp.json().get("search", [])
        for item in results:
            entity_id = item.get("id")
            if not entity_id:
                continue
            desc = item.get("description", "")
            if "film" in desc.lower() or "movie" in desc.lower():
                return _fetch_entity_details(entity_id)
    except Exception as exc:
        logger.warning("Wikidata search API failed: %s", exc)
    return None


def _fetch_entity_details(entity_id: str) -> dict | None:
    """Estrae i metadati utili dall'entità Wikidata.

    Property lette: P18 immagine → poster, P57 regista (con lookup ricorsivo
    del nome), P2047 durata, P577 data di pubblicazione → year. Più label
    it/en per titolo e original_title, e la prima description disponibile.
    """
    try:
        resp = requests.get(
            f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json",
            headers={"User-Agent": WIKIDATA_USER_AGENT},
            timeout=WIKIDATA_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        entity = data.get("entities", {}).get(entity_id, {})
        result: dict = {}

        claims = entity.get("claims", {})
        if "P18" in claims:
            pic = claims["P18"][0].get("mainsnak", {}).get("datavalue", {}).get("value", "")
            if pic:
                result["poster"] = f"https://commons.wikimedia.org/wiki/Special:FilePath/{pic}"

        if "P57" in claims:
            for claim in claims["P57"]:
                val = claim.get("mainsnak", {}).get("datavalue", {}).get("value", {})
                if isinstance(val, dict):
                    director_id = val.get("id", "")
                    # Resolve director name via additional Wikidata entity lookup
                    if director_id:
                        try:
                            time.sleep(1)
                            director_details = _fetch_entity_details(director_id)
                            if director_details and "title" in director_details:
                                result["director"] = director_details["title"]
                        except Exception:
                            pass
                    break

        if "P2047" in claims:
            val = claims["P2047"][0].get("mainsnak", {}).get("datavalue", {}).get("value", "")
            if val:
                try:
                    result["duration"] = f"{int(float(val))} min"
                except (ValueError, TypeError):
                    pass

        # P577 = data di pubblicazione (Wikidata). Estrae l'anno dai primi 4 char.
        # Formato tipico: "+2021-10-22T00:00:00Z"
        if "P577" in claims:
            val = claims["P577"][0].get("mainsnak", {}).get("datavalue", {}).get("value", {})
            if isinstance(val, dict):
                time_str = val.get("time", "")
                m = re.search(r"[+-]?(\d{4})", time_str)
                if m:
                    try:
                        result["year"] = int(m.group(1))
                    except (ValueError, TypeError):
                        pass

        # L'entity_id stesso e' il "wikidata_id" (es. "Q97154362").
        result["wikidata_id"] = entity_id

        langs = entity.get("labels", {})
        it_title = langs.get("it", {}).get("value", "")
        en_title = langs.get("en", {}).get("value", "")
        result["title"] = it_title or en_title
        if en_title and it_title and en_title.lower() != it_title.lower():
            result["original_title"] = en_title

        desc_langs = entity.get("descriptions", {})
        for lang in ["it", "en"]:
            if lang in desc_langs:
                result["description"] = desc_langs[lang].get("value", "")
                break

        if result:
            logger.info("Wikidata search match for entity %s: %s", entity_id, list(result.keys()))
        return result if result else None
    except Exception as exc:
        logger.warning("Wikidata entity fetch failed for %s: %s", entity_id, exc)
        return None


def enrich_film(film) -> None:
    """Completa i metadati mancanti di un Film via Wikidata, in-place.

    Riempe SOLO i campi vuoti: quanto raccolto dal sito del cinema ha
    priorità su Wikidata. Se il film ha già tutto, nessuna chiamata di rete.
    Tenta prima col titolo originale, poi con quello normalizzato.
    """
    if not isinstance(film, Film):
        return

    if all(getattr(film, attr, None) for attr in ("poster", "description", "director", "duration")):
        return

    wiki_data = _search_wikidata(film.title)
    if not wiki_data:
        wiki_data = _search_wikidata(film.title_normalized)
    if not wiki_data:
        return

    if not film.poster and "poster" in wiki_data:
        film.poster = wiki_data["poster"]

    if not film.description and "description" in wiki_data:
        film.description = wiki_data["description"]

    if not film.director and "director" in wiki_data:
        film.director = wiki_data["director"]

    if not film.duration and "duration" in wiki_data:
        film.duration = wiki_data["duration"]

    if not film.original_title and "original_title" in wiki_data:
        film.original_title = wiki_data["original_title"]

    if not film.year and "year" in wiki_data:
        film.year = wiki_data["year"]

    if not film.wikidata_id and "wikidata_id" in wiki_data:
        film.wikidata_id = wiki_data["wikidata_id"]
