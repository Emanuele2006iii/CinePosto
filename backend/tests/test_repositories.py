"""Test unit del layer data-access.

Testiamo direttamente i repository con una session in-memory,
senza far girare FastAPI. Test veloci e mirati.
"""
from datetime import date, timedelta

import pytest

from app.models.cinema import Cinema
from app.models.film import Film
from app.models.showing import Showing
from app.repositories import cinema_repo, film_repo, showing_repo


# ============ CinemaRepository ============

def test_upsert_insert_new_cinema(session):
    """upsert crea un cinema se non esiste."""
    data = {
        "slug": "postmodernissimo",
        "name": "PostModernissimo",
        "city": "Perugia",
        "address": "Via del Carmine 4",
        "region": "Umbria",
        "lat": 43.11,
        "lon": 12.39,
    }
    result = cinema_repo.upsert(session, data)
    session.commit()

    assert result.slug == "postmodernissimo"
    assert cinema_repo.get_by_slug(session, "postmodernissimo") is not None


def test_upsert_updates_existing_cinema(session, sample_cinema):
    """upsert aggiorna un cinema se lo slug esiste gia'."""
    data = {
        "slug": sample_cinema.slug,
        "name": "Nome Aggiornato",
        "city": sample_cinema.city,
        "address": "Via Nuova 2",
        "region": sample_cinema.region,
        "lat": sample_cinema.lat,
        "lon": sample_cinema.lon,
    }
    cinema_repo.upsert(session, data)
    session.commit()

    updated = cinema_repo.get_by_slug(session, sample_cinema.slug)
    assert updated.name == "Nome Aggiornato"
    assert updated.address == "Via Nuova 2"


def test_list_all_ordered_by_name(session):
    """list_all restituisce cinema in ordine alfabetico di nome."""
    cinemas = [
        Cinema(slug="uci", name="UCI", city="Perugia", address="A", region="Umbria", lat=1, lon=1),
        Cinema(slug="pmm", name="PostModernissimo", city="Perugia", address="B", region="Umbria", lat=1, lon=1),
        Cinema(slug="ts", name="The Space", city="Corciano", address="C", region="Umbria", lat=1, lon=1),
    ]
    session.add_all(cinemas)
    session.commit()

    result = cinema_repo.list_all(session)
    names = [c.name for c in result]
    assert names == sorted(names)


# ============ FilmRepository — normalize_title ============

@pytest.mark.parametrize("input_title,expected", [
    ("Dune", "dune"),
    ("Città Perduta", "citta perduta"),                              # rimuove accenti
    ("Ricchi…da morire – Delitti", "ricchi da morire delitti"),      # punteggiatura speciale
    ("  spazi   multipli  ", "spazi multipli"),                       # collassa spazi
    ("It's Wonderful!", "it s wonderful"),                            # apostrofi
])
def test_normalize_title(input_title, expected):
    """La normalizzazione produce forme consistenti per dedup."""
    assert film_repo.normalize_title(input_title) == expected


# ============ FilmRepository — CRUD + search ============

def test_upsert_from_scraper_insert_and_lookup_by_natural_key(session):
    """upsert_from_scraper crea un film e lo si ritrova con la chiave naturale."""
    data = {"title": "Dune", "year": 2021, "director": "Denis Villeneuve"}
    film = film_repo.upsert_from_scraper(session, data)
    session.commit()

    assert film.id is not None
    assert film.title_normalized == "dune"

    found = film_repo.get_by_natural_key(session, "dune", 2021)
    assert found is not None
    assert found.id == film.id


def test_upsert_from_scraper_updates_only_non_null(session):
    """Un secondo upsert con campi null NON sovrascrive i valori esistenti."""
    # 1. Insert iniziale con sinossi
    film_repo.upsert_from_scraper(session, {
        "title": "Dune", "year": 2021, "synopsis": "Sinossi vera",
    })
    session.commit()

    # 2. Secondo upsert senza sinossi → non deve cancellarla
    film_repo.upsert_from_scraper(session, {
        "title": "Dune", "year": 2021, "director": "Villeneuve",
    })
    session.commit()

    found = film_repo.get_by_natural_key(session, "dune", 2021)
    assert found.synopsis == "Sinossi vera"     # preservata
    assert found.director == "Villeneuve"       # aggiornata


def test_search_by_title_ignora_accenti(session):
    """La ricerca deve trovare 'città' anche cercando 'citta'."""
    film_repo.upsert_from_scraper(session, {"title": "Città Perduta", "year": 2024})
    session.commit()

    result = film_repo.search_by_title(session, "citta")
    assert len(result) == 1
    assert result[0].title == "Città Perduta"


def test_list_in_programming(session, sample_film):
    """list_in_programming restituisce film con almeno un showing nel range."""
    # Cinema di test
    c = Cinema(slug="c1", name="C1", city="P", address="A", region="U", lat=1, lon=1)
    session.add(c)
    # Showing di sample_film oggi
    session.add(Showing(
        film_id=sample_film.id, cinema_slug="c1",
        date=date.today(), times='["20:00"]',
    ))
    session.commit()

    today = date.today()
    result = film_repo.list_in_programming(session, today, today)
    assert sample_film in result

    # Range che non copre la data → lista vuota
    future = today + timedelta(days=10)
    result2 = film_repo.list_in_programming(session, future, future)
    assert sample_film not in result2


# ============ ShowingRepository ============

def test_showing_upsert_and_joinedload(session, sample_cinema, sample_film):
    """Upsert di uno showing + fetch con eager loading di film e cinema."""
    showing_repo.upsert(session, {
        "film_id": sample_film.id,
        "cinema_slug": sample_cinema.slug,
        "date": date.today(),
        "times": '["19:30", "22:00"]',
    })
    session.commit()

    result = showing_repo.list_by_date(session, date.today())
    assert len(result) == 1
    s = result[0]
    # Grazie a joinedload, .film e .cinema sono gia' popolati (nessuna nuova query)
    assert s.film.title == sample_film.title
    assert s.cinema.name == sample_cinema.name


def test_count_by_cinema_only_future(session, sample_cinema, sample_film):
    """count_by_cinema conta solo gli spettacoli >= oggi (esclude passati)."""
    yesterday = date.today() - timedelta(days=1)
    tomorrow = date.today() + timedelta(days=1)

    session.add_all([
        Showing(film_id=sample_film.id, cinema_slug=sample_cinema.slug,
                date=yesterday, times='["20:00"]'),
        Showing(film_id=sample_film.id, cinema_slug=sample_cinema.slug,
                date=tomorrow, times='["21:00"]'),
    ])
    session.commit()

    count = showing_repo.count_by_cinema(session, sample_cinema.slug)
    assert count == 1   # solo domani, ieri escluso
