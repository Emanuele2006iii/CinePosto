from __future__ import annotations

from unittest.mock import patch

import pytest

import scraper.metadata as meta
from scraper.metadata import enrich_film
from scraper.models import Film


@pytest.fixture(autouse=True)
def reset_metadata_globals():
    """Isolate each test from module-level state mutations."""
    meta._cache = {}
    meta._consecutive_failures = 0
    meta._rate_limited_until = 0.0
    meta._last_query_time = 0.0
    yield
    meta._cache = {}
    meta._consecutive_failures = 0
    meta._rate_limited_until = 0.0
    meta._last_query_time = 0.0


def _complete_film() -> Film:
    return Film(
        title="Oppenheimer",
        title_normalized="oppenheimer",
        poster="https://example.com/p.jpg",
        description="A physicist builds the bomb.",
        director="Christopher Nolan",
        duration="180 min",
    )


def _empty_film() -> Film:
    return Film(title="Oppenheimer", title_normalized="oppenheimer")


# --- enrich_film skip condition ---

def test_enrich_skips_when_all_fields_present():
    film = _complete_film()
    with patch.object(meta, "_search_wikidata") as mock_search:
        enrich_film(film)
        mock_search.assert_not_called()


def test_enrich_calls_wikidata_when_poster_missing():
    film = _complete_film()
    film.poster = None
    with patch.object(meta, "_search_wikidata", return_value={"poster": "https://wiki.com/p.jpg"}):
        enrich_film(film)
    assert film.poster == "https://wiki.com/p.jpg"


def test_enrich_populates_all_fields_from_wikidata():
    film = _empty_film()
    wiki_data = {
        "poster": "https://wiki.com/p.jpg",
        "description": "Wiki desc",
        "director": "Wiki Director",
        "duration": "120 min",
        "original_title": "Original Title",
    }
    with patch.object(meta, "_search_wikidata", return_value=wiki_data):
        enrich_film(film)
    assert film.poster == "https://wiki.com/p.jpg"
    assert film.description == "Wiki desc"
    assert film.director == "Wiki Director"
    assert film.duration == "120 min"
    assert film.original_title == "Original Title"


def test_enrich_does_not_overwrite_existing_fields():
    film = _empty_film()
    film.director = "Original Director"
    wiki_data = {"director": "Wiki Director", "poster": "https://wiki.com/p.jpg"}
    with patch.object(meta, "_search_wikidata", return_value=wiki_data):
        enrich_film(film)
    assert film.director == "Original Director"
    assert film.poster == "https://wiki.com/p.jpg"


def test_enrich_does_nothing_when_wikidata_returns_none():
    film = _empty_film()
    with patch.object(meta, "_search_wikidata", return_value=None):
        enrich_film(film)
    assert film.poster is None
    assert film.description is None
    assert film.director is None


def test_enrich_falls_back_to_normalized_title():
    film = _empty_film()
    # First call (title) returns None, second call (title_normalized) returns data
    with patch.object(meta, "_search_wikidata", side_effect=[None, {"poster": "https://p.jpg"}]):
        enrich_film(film)
    assert film.poster == "https://p.jpg"


# --- _search_wikidata cache ---

def test_search_returns_cached_result_without_api_call():
    meta._cache = {"oppenheimer": {"poster": "https://cached.com/p.jpg"}}
    with patch.object(meta, "_search_fuzzy") as mock_fuzzy:
        result = meta._search_wikidata("Oppenheimer")
    assert result == {"poster": "https://cached.com/p.jpg"}
    mock_fuzzy.assert_not_called()


def test_search_returns_none_for_cached_miss_sentinel():
    meta._cache = {"oppenheimer": meta._MISS_SENTINEL}
    with patch.object(meta, "_search_fuzzy") as mock_fuzzy:
        result = meta._search_wikidata("Oppenheimer")
    assert result is None
    mock_fuzzy.assert_not_called()


def test_search_stores_result_in_cache_on_hit():
    wiki_data = {"poster": "https://wiki.com/p.jpg"}
    with patch.object(meta, "_search_fuzzy", return_value=wiki_data):
        with patch.object(meta, "_save_cache"):
            result = meta._search_wikidata("Oppenheimer")
    assert result == wiki_data
    assert meta._cache.get("oppenheimer") == wiki_data


def test_search_stores_sentinel_in_cache_on_miss():
    with patch.object(meta, "_search_fuzzy", return_value=None):
        with patch.object(meta, "_save_cache"):
            result = meta._search_wikidata("Unknown Film")
    assert result is None
    assert meta._cache.get("unknown film") == meta._MISS_SENTINEL


# --- _sparql_query circuit breaker ---

def test_sparql_skips_after_max_consecutive_failures():
    meta._consecutive_failures = meta._MAX_CONSECUTIVE_FAILURES
    with patch("scraper.metadata.requests.get") as mock_get:
        result = meta._sparql_query("SELECT ?x WHERE { ?x ?y ?z }")
    assert result is None
    mock_get.assert_not_called()


def test_sparql_increments_failure_counter_on_error():
    with patch("scraper.metadata.requests.get", side_effect=Exception("network error")):
        meta._sparql_query("SELECT ?x WHERE { ?x ?y ?z }")
    assert meta._consecutive_failures == 1


def test_sparql_resets_failure_counter_on_success():
    meta._consecutive_failures = 2
    mock_resp = type("R", (), {
        "status_code": 200,
        "raise_for_status": lambda self: None,
        "json": lambda self: {"results": {"bindings": [{"x": "val"}]}},
    })()
    with patch("scraper.metadata.requests.get", return_value=mock_resp):
        with patch("scraper.metadata.time.sleep"):
            result = meta._sparql_query("SELECT ?x WHERE { ?x ?y ?z }")
    assert meta._consecutive_failures == 0
    assert result == [{"x": "val"}]
