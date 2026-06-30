from __future__ import annotations

import responses

from scraper.config import UCI_PROGRAMMING_URL
from scraper.connectors.uci import UCIConnector, _strip_html


def test_strip_html():
    assert _strip_html("<p>Hello <b>world</b></p>") == "Hello world"
    assert _strip_html("No tags") == "No tags"
    assert _strip_html("") == ""


@responses.activate
def test_uci_connector_scrape():
    mock_url = UCI_PROGRAMMING_URL.format(date="2026-06-12")
    responses.add(
        responses.GET,
        mock_url,
        json={
            "data": [
                {
                    "id": 1,
                    "title": "Test Film",
                    "slug": "test-film",
                    "poster": "https://example.com/poster.jpg",
                    "description": "<p>A test film</p>",
                    "genres": [{"name": "Drama"}],
                    "screens": [
                        {
                            "2D": [
                                {
                                    "language": {"name": "ITA"},
                                    "screen": {"name": "2D"},
                                    "performances": [
                                        {"actual_start_at": "18:00", "room": "Sala 1"},
                                        {"actual_start_at": "20:30", "room": "Sala 1"},
                                    ],
                                }
                            ]
                        }
                    ],
                }
            ]
        },
        status=200,
    )

    connector = UCIConnector()
    result = connector.scrape("2026-06-12")

    assert len(result.films) == 1
    assert result.films[0].title == "Test Film"
    assert result.films[0].poster == "https://example.com/poster.jpg"
    assert result.films[0].description == "A test film"
    assert result.films[0].genres == ["Drama"]

    showing = result.films[0].present_in[0]
    assert showing.times == ["18:00", "20:30"]
    assert showing.language == "ITA"
    assert showing.screen == "2D"


@responses.activate
def test_uci_connector_empty_performances():
    mock_url = UCI_PROGRAMMING_URL.format(date="2026-06-12")
    responses.add(
        responses.GET,
        mock_url,
        json={
            "data": [
                {
                    "id": 1,
                    "title": "No Shows Film",
                    "slug": "no-shows",
                    "screens": [{"2D": [{"language": {"name": "ITA"}, "screen": {"name": "2D"}, "performances": []}]}],
                }
            ]
        },
        status=200,
    )

    connector = UCIConnector()
    result = connector.scrape("2026-06-12")

    assert len(result.films) == 1
    assert result.films[0].present_in[0].times == []


@responses.activate
def test_uci_connector_api_error():
    mock_url = UCI_PROGRAMMING_URL.format(date="2026-06-12")
    responses.add(responses.GET, mock_url, json={"error": "fail"}, status=500)

    connector = UCIConnector()
    result = connector.scrape("2026-06-12")

    assert len(result.films) == 0
    assert len(result.errors) > 0
