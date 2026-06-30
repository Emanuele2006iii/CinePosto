from __future__ import annotations

from scraper.delta import _last_removal_date, _showings_changed, merge_films
from scraper.models import Film, Showing


def test_merge_new_film():
    new_films = [
        Film(
            title="New Film",
            title_normalized="new film",
            present_in=[
                Showing(cinema="Cinema A", cinema_slug="cinema-a", date="2026-06-12", times=["18:00"])
            ],
        )
    ]
    merged = merge_films(new_films, [], "2026-06-12")
    assert len(merged) == 1
    assert merged[0].status == "in_programmazione"
    assert merged[0].history == [{"date": "2026-06-12", "action": "added"}]


def test_merge_existing_film_unchanged():
    previous = [
        {
            "title": "Existing Film",
            "title_normalized": "existing film",
            "present_in": [
                {"cinema": "Cinema A", "cinema_slug": "cinema-a", "date": "2026-06-12", "times": ["18:00"]}
            ],
            "history": [{"date": "2026-06-11", "action": "added"}],
            "status": "in_programmazione",
        }
    ]
    new_films = [
        Film(
            title="Existing Film",
            title_normalized="existing film",
            present_in=[
                Showing(cinema="Cinema A", cinema_slug="cinema-a", date="2026-06-12", times=["18:00"])
            ],
        )
    ]
    merged = merge_films(new_films, previous, "2026-06-12")
    assert len(merged) == 1
    assert merged[0].status == "in_programmazione"
    assert merged[0].history == [{"date": "2026-06-11", "action": "added"}]


def test_merge_existing_film_updated():
    previous = [
        {
            "title": "Updated Film",
            "title_normalized": "updated film",
            "present_in": [
                {"cinema": "Cinema A", "cinema_slug": "cinema-a", "date": "2026-06-12", "times": ["18:00"]}
            ],
            "history": [{"date": "2026-06-11", "action": "added"}],
            "status": "in_programmazione",
        }
    ]
    new_films = [
        Film(
            title="Updated Film",
            title_normalized="updated film",
            present_in=[
                Showing(cinema="Cinema A", cinema_slug="cinema-a", date="2026-06-12", times=["18:00", "20:30"])
            ],
        )
    ]
    merged = merge_films(new_films, previous, "2026-06-12")
    assert len(merged) == 1
    assert merged[0].history[-1] == {"date": "2026-06-12", "action": "updated"}


def test_merge_missing_film_within_threshold():
    previous = [
        {
            "title": "Recent Film",
            "title_normalized": "recent film",
            "present_in": [
                {"cinema": "Cinema A", "cinema_slug": "cinema-a", "date": "2026-06-11", "times": ["18:00"]}
            ],
            "history": [{"date": "2026-06-11", "action": "added"}],
            "status": "in_programmazione",
        }
    ]
    merged = merge_films([], previous, "2026-06-12")
    assert len(merged) == 0


def test_merge_missing_film_beyond_threshold():
    previous = [
        {
            "title": "Old Film",
            "title_normalized": "old film",
            "present_in": [
                {"cinema": "Cinema A", "cinema_slug": "cinema-a", "date": "2026-06-01", "times": ["18:00"]}
            ],
            "history": [{"date": "2026-06-01", "action": "added"}],
            "status": "in_programmazione",
        }
    ]
    merged = merge_films([], previous, "2026-06-12")
    assert len(merged) == 0


def test_showings_changed():
    old = [{"cinema_slug": "a", "date": "2026-06-12", "times": ["18:00"], "price": ""}]
    new_same = [{"cinema_slug": "a", "date": "2026-06-12", "times": ["18:00"], "price": ""}]
    new_diff = [{"cinema_slug": "a", "date": "2026-06-12", "times": ["18:00", "20:30"], "price": ""}]
    assert not _showings_changed(old, new_same)
    assert _showings_changed(old, new_diff)


def test_last_removal_date():
    history1 = [{"date": "2026-06-10", "action": "added"}, {"date": "2026-06-11", "action": "removed"}]
    history2 = [{"date": "2026-06-10", "action": "added"}]
    assert _last_removal_date(history1) == "2026-06-11"
    assert _last_removal_date(history2) is None
