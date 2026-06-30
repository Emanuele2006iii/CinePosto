from __future__ import annotations

from scraper.connectors.thespace import TheSpaceConnector
from scraper.models import Film

# --- _parse_api_film ---

def test_parse_api_film_returns_film_with_all_fields():
    connector = TheSpaceConnector()
    data = {
        "filmTitle": "Test Film",
        "posterImageSrc": "https://example.com/poster.jpg",
        "synopsisShort": "A great film.",
        "runningTime": 120,
        "isDurationUnknown": False,
        "genres": ["Action", "Drama"],
        "director": "Test Director",
        "showingGroups": [
            {
                "date": "2026-06-24T00:00:00Z",
                "sessions": [{"startTime": "2026-06-24T20:00:00Z"}],
            }
        ],
    }
    film = connector._parse_api_film(data, "2026-06-24")
    assert isinstance(film, Film)
    assert film.title == "Test Film"
    assert film.description == "A great film."
    assert film.duration == "120 min"
    assert film.director == "Test Director"
    assert film.genres == ["Action", "Drama"]
    assert film.poster == "https://example.com/poster.jpg"
    assert film.source_poster == "https://example.com/poster.jpg"


def test_parse_api_film_returns_none_when_title_missing():
    connector = TheSpaceConnector()
    film = connector._parse_api_film({}, "2026-06-24")
    assert film is None


def test_parse_api_film_title_normalized_uses_normalize_title():
    connector = TheSpaceConnector()
    data = {
        "filmTitle": "Avengers: Endgame (2019)",
        "showingGroups": [
            {
                "date": "2026-06-24T00:00:00Z",
                "sessions": [{"startTime": "2026-06-24T18:00:00Z"}],
            }
        ],
    }
    film = connector._parse_api_film(data, "2026-06-24")
    # normalize_title strips the year suffix
    assert "2019" not in film.title_normalized


def test_parse_api_film_unknown_duration_is_none():
    connector = TheSpaceConnector()
    data = {
        "filmTitle": "Test",
        "runningTime": 90,
        "isDurationUnknown": True,
        "showingGroups": [
            {
                "date": "2026-06-24T00:00:00Z",
                "sessions": [{"startTime": "2026-06-24T18:00:00Z"}],
            }
        ],
    }
    film = connector._parse_api_film(data, "2026-06-24")
    assert film.duration is None


# --- _parse_api_showing_groups ---

def test_parse_showing_groups_extracts_time_from_iso_datetime():
    connector = TheSpaceConnector()
    data = {
        "showingGroups": [
            {
                "date": "2026-06-24T00:00:00Z",
                "sessions": [{"startTime": "2026-06-24T20:30:00Z"}],
            }
        ]
    }
    showings = connector._parse_api_showing_groups(data, "2026-06-24", "http://test")
    assert len(showings) == 1
    assert showings[0].times == ["20:30"]
    assert showings[0].date == "2026-06-24"


def test_parse_showing_groups_extracts_language_from_attributes():
    connector = TheSpaceConnector()
    data = {
        "showingGroups": [
            {
                "date": "2026-06-24T00:00:00Z",
                "sessions": [
                    {
                        "startTime": "2026-06-24T18:00:00Z",
                        "attributes": [
                            {"attributeType": "Language", "name": "ITA"},
                            {"attributeType": "Format", "name": "Dolby Atmos"},
                        ],
                    }
                ],
            }
        ]
    }
    showings = connector._parse_api_showing_groups(data, "2026-06-24", "http://test")
    assert showings[0].language == "ITA"
    assert "Dolby Atmos" in showings[0].session_attributes


def test_parse_showing_groups_skips_session_without_time():
    connector = TheSpaceConnector()
    data = {
        "showingGroups": [
            {
                "date": "2026-06-24T00:00:00Z",
                "sessions": [{"startTime": ""}],
            }
        ]
    }
    showings = connector._parse_api_showing_groups(data, "2026-06-24", "http://test")
    assert showings == []


def test_parse_showing_groups_empty_returns_empty_list():
    connector = TheSpaceConnector()
    data = {"showingGroups": []}
    showings = connector._parse_api_showing_groups(data, "2026-06-24", "http://test")
    assert showings == []


def test_parse_showing_groups_has_sessions_flag_ignored():
    # hasSessions was dead code (always filtered by delta) — removed. Verify no side effect.
    connector = TheSpaceConnector()
    data = {"showingGroups": [], "hasSessions": True}
    showings = connector._parse_api_showing_groups(data, "2026-06-24", "http://test")
    assert showings == []


def test_parse_showing_groups_skips_malformed_date():
    connector = TheSpaceConnector()
    data = {
        "showingGroups": [
            {
                "date": "not-a-date",
                "sessions": [{"startTime": "2026-06-24T18:00:00Z"}],
            }
        ]
    }
    showings = connector._parse_api_showing_groups(data, "2026-06-24", "http://test")
    assert showings == []
