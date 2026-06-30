from __future__ import annotations

from scraper.models import CinemaError, Film, Showing, output_to_json


def test_showing_creation():
    s = Showing(
        cinema="Test Cinema",
        cinema_slug="test-cinema",
        date="2026-06-12",
        times=["18:00", "20:30"],
        screen="Sala 1",
        source_url="https://example.com",
        language="ITA",
        session_attributes=["3D"],
    )
    assert s.cinema == "Test Cinema"
    assert s.times == ["18:00", "20:30"]
    assert s.screen == "Sala 1"


def test_film_creation():
    f = Film(
        title="Test Film",
        title_normalized="test film",
        present_in=[],
        poster="https://example.com/poster.jpg",
    )
    assert f.title == "Test Film"
    assert f.poster == "https://example.com/poster.jpg"


def test_output_to_json():
    film = Film(
        title="Test Film",
        title_normalized="test film",
        present_in=[
            Showing(
                cinema="Cinema A",
                cinema_slug="cinema-a",
                date="2026-06-12",
                times=["18:00"],
                screen="Sala 1",
            )
        ],
        poster="https://example.com/poster.jpg",
        description="A test film",
        genres=["Drama", "Thriller"],
    )
    error = CinemaError(
        cinema="Cinema B",
        timestamp="2026-06-12T10:00:00",
        exception="ConnectionError",
        phase="scrape",
        detail="Timeout",
    )
    output = output_to_json([film], [error], "TestCity")
    assert output["city"] == "TestCity"
    assert len(output["films"]) == 1
    assert len(output["errors"]) == 1
    assert output["films"][0]["title"] == "Test Film"
    assert output["films"][0]["present_in"][0]["cinema"] == "Cinema A"


def test_cinema_error_to_dict():
    e = CinemaError(
        cinema="Test",
        timestamp="2026-06-12T10:00:00",
        exception="ValueError",
        phase="parse",
        url="https://example.com",
        detail="Bad data",
    )
    d = e.to_dict()
    assert d["cinema"] == "Test"
    assert d["exception"] == "ValueError"
    assert d["url"] == "https://example.com"
