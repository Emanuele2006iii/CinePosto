"""Test del connettore PostModernissimo su payload RSC e HTML registrati."""
from __future__ import annotations

import json

import responses

from scraper.config import POSTMOD_CINEMA_URL
from scraper.connectors.postmodernissimo import PostModernissimoConnector


def _build_rsc_push(movies: list[dict]) -> str:
    inner = json.dumps({"page": {"movies": movies}}, ensure_ascii=False, separators=(",", ":"))
    escaped = inner.replace("\\", "\\\\").replace('"', '\\"')
    return f'self.__next_f.push([1,"{escaped}"]);\n'


@responses.activate
def test_postmodernissimo_connector_scrape():
    rsc_push = _build_rsc_push(
        [
            {
                "id": 9999,
                "title": "Test Film",
                "slug": "test-film",
                "permalink": "https://www.postmodernissimo.com/films/test-film",
                "content": "A test film description.",
                "details": {
                    "regia": "Test Director",
                    "genere": "Commedia, Drammatico",
                    "durata": "120",
                    "nazione": "Italia",
                    "anno": "2026",
                    "youtube_cover": {"url": "https://example.com/poster.jpg"},
                },
                "programmazione": {
                    "spazio_prog": "postmod",
                    "shows": [
                        {"date": "20260612", "orario": "19:00", "opzioni": "off", "nota": None, "ticket": ""},
                        {"date": "20260612", "orario": "21:30", "opzioni": "off", "nota": None, "ticket": ""},
                        {"date": "20260613", "orario": "19:00", "opzioni": "off", "nota": None, "ticket": ""},
                    ],
                },
            }
        ]
    )

    html_content = f"""
    <html>
    <body>
    <script>{rsc_push}</script>
    <ul class="movie-container">
        <li class="movie-item">
            <a href="/films/test-film">
                <h2>Test Film</h2>
                <p class="text-sm">Test Director</p>
                <img src="https://example.com/poster.jpg">
            </a>
        </li>
    </ul>
    </body>
    </html>
    """
    responses.add(
        responses.GET,
        POSTMOD_CINEMA_URL,
        body=html_content,
        status=200,
    )

    connector = PostModernissimoConnector()
    result = connector.scrape("2026-06-12", dates=["2026-06-12", "2026-06-13"])

    assert len(result.films) >= 1
    film = result.films[0]
    assert film.title == "Test Film"
    assert film.director == "Test Director"
    assert film.duration == "120"
    assert "Commedia" in film.genres
    assert len(film.present_in) == 2
    assert film.present_in[0].date == "2026-06-12"
    assert film.present_in[0].times == ["19:00", "21:30"]
    assert film.present_in[1].date == "2026-06-13"
    assert film.present_in[1].times == ["19:00"]


@responses.activate
def test_postmodernissimo_skips_weekend_only():
    rsc_push = _build_rsc_push(
        [
            {
                "id": 9998,
                "title": "Weekend Film",
                "slug": "weekend-film",
                "permalink": "https://www.postmodernissimo.com/films/weekend-film",
                "content": "",
                "details": {"regia": None, "genere": "", "durata": None},
                "programmazione": {
                    "spazio_prog": "postmod",
                    "shows": [
                        {"date": "20260620", "orario": "20:00", "opzioni": "off", "nota": None, "ticket": ""},
                        {"date": "20260621", "orario": "20:00", "opzioni": "off", "nota": None, "ticket": ""},
                    ],
                },
            }
        ]
    )

    html_content = f"""
    <html><body>
    <script>{rsc_push}</script>
    </body></html>
    """
    responses.add(responses.GET, POSTMOD_CINEMA_URL, body=html_content, status=200)

    connector = PostModernissimoConnector()
    result = connector.scrape(
        "2026-06-12",
        dates=["2026-06-12", "2026-06-13", "2026-06-14"],
    )

    assert len(result.films) == 0


@responses.activate
def test_postmodernissimo_director_cleaned():
    rsc_push = _build_rsc_push(
        [
            {
                "id": 9997,
                "title": "Clean Film",
                "slug": "clean-film",
                "permalink": "https://www.postmodernissimo.com/films/clean-film",
                "content": "",
                "details": {"regia": "  (  John Doe  )  ", "genere": "", "durata": None},
                "programmazione": {
                    "spazio_prog": "postmod",
                    "shows": [
                        {"date": "20260612", "orario": "18:00", "opzioni": "off", "nota": None, "ticket": ""},
                    ],
                },
            }
        ]
    )

    html_content = f"<html><body><script>{rsc_push}</script></body></html>"
    responses.add(responses.GET, POSTMOD_CINEMA_URL, body=html_content, status=200)

    connector = PostModernissimoConnector()
    result = connector.scrape("2026-06-12", dates=["2026-06-12"])

    assert len(result.films) == 1
    assert result.films[0].director == "John Doe"
