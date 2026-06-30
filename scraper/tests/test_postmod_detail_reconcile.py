"""
Test che riproduce il bug "Palestina Anima Mundi".

Scenario: homepage sostiene che il film ha 4 show (18, 19, 20, 21),
ma la pagina di dettaglio dice che il film ha solo 1 show (19 alle 20:30).

Lo scraper attuale si fida della homepage → sbaglia.
Lo scraper corretto usa il dettaglio come fonte canonica → vince il dettaglio.
"""
from __future__ import annotations

import json

import responses

from scraper.config import POSTMOD_CINEMA_URL
from scraper.connectors.postmodernissimo import PostModernissimoConnector


def _rsc_push(movies: list[dict]) -> str:
    """Stesso helper dei test_postmodernissimo.py esistenti."""
    inner = json.dumps({"page": {"movies": movies}}, ensure_ascii=False, separators=(",", ":"))
    escaped = inner.replace("\\", "\\\\").replace('"', '\\"')
    return f'self.__next_f.push([1,"{escaped}"]);\n'


@responses.activate
def test_postmod_reconciles_homepage_with_detail_when_disagree():
    """
    Homepage dice 4 show per Palestina Anima Mundi.
    Dettaglio dice solo 1 show (19/06 20:30).
    Lo scraper DEVE usare il dettaglio come fonte canonica.
    """
    permalink = "https://www.postmodernissimo.com/films/palestina-anima-mundi"

    # Homepage: il film appare con 4 show (18, 19, 20, 21)
    homepage_rsc = _rsc_push([
        {
            "id": 12381,
            "title": "Palestina Anima Mundi",
            "slug": "palestina-anima-mundi",
            "permalink": permalink,
            "content": "",
            "details": {"regia": "Francesca Albanese", "genere": "Presentazione libro", "durata": "60"},
            "programmazione": {
                "spazio_prog": "postmod",
                "shows": [
                    {"date": "20260618", "orario": "18:30", "opzioni": "off", "nota": None, "ticket": ""},
                    {"date": "20260619", "orario": "18:30", "opzioni": "off", "nota": None, "ticket": ""},
                    {"date": "20260620", "orario": "18:30", "opzioni": "off", "nota": None, "ticket": ""},
                    {"date": "20260621", "orario": "21:15", "opzioni": "off", "nota": None, "ticket": ""},
                ],
            },
        }
    ])
    homepage_html = f"<html><body><script>{homepage_rsc}</script></body></html>"

    # Dettaglio: il film ha SOLO l'orario canonico del 19 alle 20:30
    detail_rsc = _rsc_push([
        {
            "id": 12381,
            "title": "Palestina Anima Mundi",
            "slug": "palestina-anima-mundi",
            "permalink": permalink,
            "content": "Pagina di dettaglio con orari ridotti.",
            "details": {"regia": "Francesca Albanese", "genere": "Presentazione libro", "durata": "60"},
            "programmazione": {
                "spazio_prog": "postmod",
                "shows": [
                    {"date": "20260619", "orario": "20:30", "opzioni": "off", "nota": None, "ticket": ""},
                ],
            },
        }
    ])
    detail_html = f"<html><body><script>{detail_rsc}</script></body></html>"

    responses.add(
        responses.GET,
        POSTMOD_CINEMA_URL,
        body=homepage_html,
        status=200,
    )
    responses.add(
        responses.GET,
        permalink,
        body=detail_html,
        status=200,
    )

    weeks_dates = ["2026-06-18", "2026-06-19", "2026-06-20", "2026-06-21"]
    result = PostModernissimoConnector().scrape("2026-06-18", dates=weeks_dates)

    # Deve esserci un solo film (Palestina)
    assert len(result.films) == 1, f"atteso 1 film, ottenuti {len(result.films)}"
    film = result.films[0]

    # Mostra totali per data (un solo Showing per data)
    per_date = {s.date: sorted(s.times) for s in film.present_in}

    # ASSERT: solo il 19/06 alle 20:30 (dal dettaglio)
    assert list(per_date.keys()) == ["2026-06-19"], (
        f"BUG: lo scraper ha tenuto gli show della homepage invece del dettaglio. "
        f"Ottenuto: {per_date}, atteso solo '2026-06-19'"
    )
    assert per_date["2026-06-19"] == ["20:30"], (
        f"BUG: orario sbagliato. Ottenuto: {per_date['2026-06-19']}, atteso ['20:30']"
    )


@responses.activate
def test_postmod_keeps_homepage_shows_when_detail_unreachable():
    """
    Se il dettaglio fallisce (404/timeout), lo scraper deve comunque
    pubblicare gli show della homepage (no regression).
    """
    permalink = "https://www.postmodernissimo.com/films/palestina-anima-mundi"

    homepage_rsc = _rsc_push([
        {
            "id": 12382,
            "title": "Film Sempre OK",
            "slug": "film-sempre-ok",
            "permalink": permalink,
            "content": "",
            "details": {"regia": "Test Director", "genere": "Drammatico", "durata": "120"},
            "programmazione": {
                "spazio_prog": "postmod",
                "shows": [
                    {"date": "20260618", "orario": "18:00", "opzioni": "off", "nota": None, "ticket": ""},
                    {"date": "20260619", "orario": "20:00", "opzioni": "off", "nota": None, "ticket": ""},
                ],
            },
        }
    ])
    homepage_html = f"<html><body><script>{homepage_rsc}</script></body></html>"

    responses.add(
        responses.GET,
        POSTMOD_CINEMA_URL,
        body=homepage_html,
        status=200,
    )
    responses.add(
        responses.GET,
        permalink,
        body="Server Error",
        status=500,
    )

    weeks_dates = ["2026-06-18", "2026-06-19"]
    result = PostModernissimoConnector().scrape("2026-06-18", dates=weeks_dates)

    assert len(result.films) == 1
    film = result.films[0]
    per_date = {s.date: sorted(s.times) for s in film.present_in}
    assert per_date == {"2026-06-18": ["18:00"], "2026-06-19": ["20:00"]}, (
        f"REGRESSION: dettaglio fallito, doveva tenere gli show della homepage. Ottenuto: {per_date}"
    )
