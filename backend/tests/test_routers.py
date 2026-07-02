"""Test end-to-end degli endpoint HTTP.

Testiamo la catena completa router → service → repo → DB in-memory
con TestClient di FastAPI. Ogni test parte da un DB pulito.
"""
from datetime import date

from app.models.cinema import Cinema
from app.models.film import Film
from app.models.showing import Showing


# ============ /health ============

def test_health_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ============ /api/v1/cinema ============

def test_list_cinemas_empty(client):
    """Nessun cinema in DB → lista vuota, non errore."""
    resp = client.get("/api/v1/cinema")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_cinemas_with_data(client, session):
    """Con 2 cinema in DB → ritorna 2 cinema ordinati per nome."""
    session.add_all([
        Cinema(slug="uci", name="UCI", city="Perugia", address="A", region="Umbria", lat=1, lon=1),
        Cinema(slug="pmm", name="PostModernissimo", city="Perugia", address="B", region="Umbria", lat=1, lon=1),
    ])
    session.commit()

    resp = client.get("/api/v1/cinema")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    # Ordine alfabetico
    assert body[0]["name"] == "PostModernissimo"
    assert body[1]["name"] == "UCI"
    # Filtraggio degli attributi: no relazioni, no id interni SQLAlchemy
    assert "showings" not in body[0]


def test_get_cinema_by_slug_returns_with_count(client, sample_cinema):
    resp = client.get(f"/api/v1/cinema/{sample_cinema.slug}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["slug"] == sample_cinema.slug
    assert body["showings_count"] == 0    # nessun showing associato


def test_get_cinema_not_found(client):
    """Slug inesistente → 404."""
    resp = client.get("/api/v1/cinema/non-esiste")
    assert resp.status_code == 404
    assert "non trovato" in resp.json()["detail"].lower()


# ============ /api/v1/film ============

def test_films_today_empty(client):
    resp = client.get("/api/v1/film/oggi")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_film_detail_not_found(client):
    resp = client.get("/api/v1/film/9999")
    assert resp.status_code == 404


def test_get_film_detail_returns_detail_schema(client, session, sample_film, sample_cinema):
    """Il dettaglio film include il campo showings (denormalizzato)."""
    session.add(Showing(
        film_id=sample_film.id, cinema_slug=sample_cinema.slug,
        date=date.today(), times='["20:00"]',
    ))
    session.commit()

    resp = client.get(f"/api/v1/film/{sample_film.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == sample_film.id
    assert body["title"] == sample_film.title
    assert "synopsis" in body     # campo di FilmDetail
    assert "showings" in body
    assert len(body["showings"]) == 1
    # times deve essere una lista di stringhe (il validator ha parsato la stringa JSON)
    assert body["showings"][0]["times"] == ["20:00"]


# ============ /api/v1/film/search ============

def test_search_requires_min_2_chars(client):
    """Query di 1 carattere → 422 Unprocessable (validazione FastAPI)."""
    resp = client.get("/api/v1/film/search?q=a")
    assert resp.status_code == 422


def test_search_returns_matching_films(client, session):
    """Ricerca case-insensitive con normalizzazione accenti."""
    session.add_all([
        Film(title="Dune", title_normalized="dune", year=2021),
        Film(title="Città Perduta", title_normalized="citta perduta", year=2024),
    ])
    session.commit()

    resp = client.get("/api/v1/film/search?q=citta")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["title"] == "Città Perduta"


# ============ /api/v1/admin/reimport ============

def test_admin_reimport_requires_token(client):
    """Senza header X-Admin-Token → 422."""
    resp = client.post("/api/v1/admin/reimport")
    assert resp.status_code == 422


def test_admin_reimport_rejects_wrong_token(client):
    resp = client.post(
        "/api/v1/admin/reimport",
        headers={"X-Admin-Token": "token-sbagliato"},
    )
    assert resp.status_code == 403
