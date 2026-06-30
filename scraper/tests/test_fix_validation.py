"""
Fix-validation tests.

Ogni test esercita un fix proposto e verifica che il bug noto sia risolto
mentre il comportamento atteso resta intatto.

Per ogni test:
 - uso mocks HTTP (responses) per API UCI / TheSpace
 - HTML mockato per PostMod
 - verifico che il fix produca il risultato corretto SENZA toccare il codice
   di produzione. Questo test è la SPEC del fix.

Run: python3 -m pytest tests/test_fix_validation.py -v
"""
from __future__ import annotations

import json

import responses

from scraper.config import (
    POSTMOD_CINEMA_URL,
    THE_SPACE_AUTH_URL,
    THE_SPACE_FILMS_URL,
    UCI_PROGRAMMING_URL,
)
from scraper.connectors.postmodernissimo import PostModernissimoConnector
from scraper.connectors.thespace import TheSpaceConnector
from scraper.connectors.uci import UCIConnector
from scraper.main import _deduplicate_films
from scraper.models import Film, Showing

# ---------- UCI FIXES ----------

@responses.activate
def test_fix_uci_filters_performances_by_day():
    """Fix 1: `_build_showings_from_screens` deve filtrare performance per `day == target_date`.

    Caso: la API ritorna TUTTE le performance di un film (anche di altre date)
    associate alla response di una data target. Il bug originale metteva
    performance del 17/06 sotto 16/06, generando il bug del '16:00 fantasma'.
    """
    target_date = "2026-06-16"
    mock_url = UCI_PROGRAMMING_URL.format(date=target_date)
    responses.add(
        responses.GET, mock_url,
        json={"data": [{
            "id": 1, "title": "Disclosure Day", "slug": "disclosure-day",
            "poster": "", "description": "", "genres": [],
            "screens": [{"2D": [{
                "language": {"name": "ITA"},
                "screen": {"name": "2D"},
                "performances": [
                    # performance spurie di altre date
                    {"actual_start_at": "16:00", "day": "2026-06-17", "room": "Sala 1"},
                    {"actual_start_at": "17:00", "day": "2026-06-17", "room": "Sala 2"},
                    # performance vere del target
                    {"actual_start_at": "20:20", "day": "2026-06-16", "room": "Sala 1"},
                    {"actual_start_at": "21:30", "day": "2026-06-16", "room": "Sala 2"},
                    {"actual_start_at": "22:00", "day": "2026-06-16", "room": "Sala 3"},
                ],
            }]}],
        }]},
        status=200,
    )

    connector = UCIConnector()
    result = connector.scrape(target_date, dates=[target_date])

    assert len(result.films) == 1
    times = sorted(result.films[0].present_in[0].times)
    assert times == ["20:20", "21:30", "22:00"], \
        f"BUG: day filter non applicato, trovati {times} (atteso solo 16/06)"


@responses.activate
def test_fix_uci_skips_not_today_true():
    """Fix 2: il campo `not_today=True` significa 'non in programmazione oggi'.

    Il connettore UCI deve scartare il film intero se `not_today=True` per
    la data richiesta.
    """
    target_date = "2026-06-16"
    mock_url = UCI_PROGRAMMING_URL.format(date=target_date)
    responses.add(responses.GET, mock_url, json={"data": [
        {"id": 1, "title": "Pecore sotto copertura", "slug": "pecore",
         "not_today": True,
         "screens": [{"2D": [{"language": {"name": "ITA"}, "screen": {"name": "2D"},
                              "performances": [{"actual_start_at": "16:00", "day": target_date}]}]}]},
        {"id": 2, "title": "Disclosure Day", "slug": "dd",
         "not_today": False,
         "screens": [{"2D": [{"language": {"name": "ITA"}, "screen": {"name": "2D"},
                              "performances": [{"actual_start_at": "21:30", "day": target_date}]}]}]},
    ]}, status=200)

    result = UCIConnector().scrape(target_date, dates=[target_date])
    titles = [f.title for f in result.films]
    assert titles == ["Disclosure Day"], f"BUG: not_today non filtrato, ottenuto {titles}"


# ---------- POSTMOD FIXES ----------

def _rsc(movies):
    """Mock del payload RSC reale: ogni movie dict compare come `{...}` top-level.

    Usa separators=(",", ":") per restare compatibile con la regex non-greedy
    del parser `_parse_rsc_payload` (no spazi dopo ":")
    """
    inner = "".join(json.dumps(m, ensure_ascii=False, separators=(",", ":")) for m in movies)
    esc = inner.replace("\\", "\\\\").replace('"', '\\"')
    return (
        "<html><body><script>"
        f'self.__next_f.push([1,"{esc}"]);'
        "</script></body></html>"
    )


@responses.activate
def test_fix_postmod_filters_opzioni_noprog():
    """Fix 3A: filtrare slot con opzioni='noprog' (non in programmazione).

    Caso: Amarga Navidad 16/06 ha slot noprog alle 16:45 e 21:15 + slot vost alle 19:00.
    Il fix deve scartare i due noprog.
    """
    rsc = _rsc([{
        "id": 1, "title": "Amarga Navidad", "slug": "amarga-navidad",
        "permalink": "https://www.postmodernissimo.com/films/amarga-navidad",
        "content": "", "details": {"genere": "", "regia": "", "durata": None},
        "programmazione": {
            "spazio_prog": "postmod",
            "shows": [
                {"date": "20260616", "orario": "16:45", "opzioni": "noprog", "nota": None, "ticket": ""},
                {"date": "20260616", "orario": "19:00", "opzioni": "vost",   "nota": None, "ticket": ""},
                {"date": "20260616", "orario": "21:15", "opzioni": "noprog", "nota": None, "ticket": ""},
            ],
        },
    }])
    responses.add(responses.GET, POSTMOD_CINEMA_URL, body=rsc, status=200)

    result = PostModernissimoConnector().scrape("2026-06-16", dates=["2026-06-16"])
    assert len(result.films) == 1
    times = result.films[0].present_in[0].times
    assert times == ["19:00"], f"BUG noprog non filtrato: {times}"


@responses.activate
def test_fix_postmod_duplicati_stream_order():
    """FIX 1: '_parse_rsc_payload' deve ACCUMULARE gli `shows` da tutte le occorrenze
    dello stesso `permalink`, non scegliere solo l'occorrenza "ultima".
    Comportamento pianificato in PlanAudit.md, FIX 1.
    """
    occ_a = (
        '{"id":1,"title":"Don Chisciotte","slug":"don-chisciotte",'
        '"permalink":"https://www.postmodernissimo.com/films/don-chisciotte",'
        '"content":"","details":{"genere":"","regia":"","durata":null},'
        '"programmazione":{"spazio_prog":"postmod","shows":['
        '{"date":"20260617","orario":"18:30","opzioni":"off","nota":null,"ticket":""}'
        ']}}'
    )
    occ_b = (
        '{"id":1,"title":"Don Chisciotte","slug":"don-chisciotte",'
        '"permalink":"https://www.postmodernissimo.com/films/don-chisciotte",'
        '"content":"","details":{"genere":"","regia":"","durata":null},'
        '"programmazione":{"spazio_prog":"postmod","shows":['
        '{"date":"20260617","orario":"21:00","opzioni":"off","nota":null,"ticket":""}'
        ']}}'
    )
    rsc = "self.__next_f.push([1,\"" + (occ_a + occ_b).replace('"', '\\"') + "\"]);"
    html = f"<html><body><script>{rsc}</script></body></html>"
    responses.add(responses.GET, POSTMOD_CINEMA_URL, body=html, status=200)

    result = PostModernissimoConnector().scrape("2026-06-17", dates=["2026-06-17"])
    times = result.films[0].present_in[0].times if result.films else []
    assert times == ["18:30", "21:00"], f"FIX 1 non applicato: scelto {times}, atteso ['18:30', '21:00']"


@responses.activate
def test_fix_postmod_filters_event_stub_by_title_hint():
    """Fix 3C: scartare stub-eventi non in /eventi/ ma con titolo sospetto."""
    occ = (
        '{"id":1,"title":"Fabio Segatori e il Gruppo Micrologus presentano Don Chisciotte",'
        '"slug":"fabio-segatori-gruppo-micrologus-don-chisciotte",'
        '"permalink":"https://www.postmodernissimo.com/eventi/fabio-segatori-gruppo-micrologus-don-chisciotte",'
        '"content":"","details":{"genere":"","regia":"","durata":null},'
        '"programmazione":{"spazio_prog":"postmod","shows":['
        '{"date":"20260617","orario":"21:00","opzioni":"off","nota":null,"ticket":""}'
        ']}}'
    )
    rsc = "self.__next_f.push([1,\"" + occ.replace('"', '\\"') + "\"]);"
    html = f"<html><body><script>{rsc}</script></body></html>"
    responses.add(responses.GET, POSTMOD_CINEMA_URL, body=html, status=200)

    result = PostModernissimoConnector().scrape("2026-06-17", dates=["2026-06-17"])
    titles = [f.title for f in result.films]
    assert titles == [], f"BUG: evento stub non filtrato, trovato {titles}"


# ---------- THESPACE FIXES ----------

@responses.activate
def test_fix_thespace_filters_showing_groups_by_date():
    """Fix Thespace: filtrare showingGroups per `parsed_date == target_date`.

    Caso: la API ritorna showingGroups con date potenzialmente diverse da
    quella richiesta. Bug noto: SCARY MOVIE 16/06 cache aveva 16:10 che è
    di 17/06. Confronto: dopo il fix, il Film finale per SCARY MOVIE in cache
    deve presentarsi AL 17/06 solo per la data 17/06 (non duplicato per 16/06).
    """
    target_dates = ["2026-06-16", "2026-06-17"]
    responses.add(responses.POST, THE_SPACE_AUTH_URL, json={"access_token": "x"}, status=200)
    # Per 16/06: solo SCARY MOVIE 18:35 20:45
    # Per 17/06: solo SCARY MOVIE 16:10 + spurio 16:10 anche per 16/06
    responses.add(
        responses.GET, THE_SPACE_FILMS_URL,
        json={"result": [
            {
                "filmTitle": "SCARY MOVIE",
                "filmUrl": "/film/scary-movie",
                "showingGroups": [
                    {"date": "2026-06-16T00:00:00", "sessions": [
                        {"startTime": "2026-06-16T18:35:00", "attributes": []},
                        {"startTime": "2026-06-16T20:45:00", "attributes": []},
                    ]},
                ],
            },
        ]},
        status=200,
    )
    result = TheSpaceConnector().scrape(target_dates[1], dates=target_dates)
    # Atteso dopo fix: SCARY MOVIE 16/06 SOLO con (18:35, 20:45); 17/06 con (16:10)
    scary = next(f for f in result.films if "SCARY" in f.title.upper())
    per_date = {s.date: sorted(s.times) for s in scary.present_in}
    assert "2026-06-16" in per_date and "16:10" not in per_date.get("2026-06-16", []),\
        f"BUG Thespace: 16:10 leak su 16/06: {per_date}"


# ---------- DEDUP FIXES ----------

def test_fix_dedup_unescapes_html_before_match():
    """Fix dedup: applicare html.unescape ai titoli PRIMA del fuzzy_match.

    Caso: due film 'Puliti' (Giugno '24) e 'Encoded' (PostMod) per lo stesso titolo
    devono essere uniti. Il fix proposto normalizza in _deduplicate_films.
    """
    clean = Film(
        title="Still Walking – Camminando in un giorno d'estate",
        title_normalized="still walking – camminando in un giorno d'estate",
        present_in=[Showing(cinema="X", cinema_slug="x", date="2026-06-16", times=["21:15"])],
    )
    encoded = Film(
        title="Still Walking &#8211; Camminando in un giorno d&#8217;estate",
        title_normalized="still walking &#8211; camminando in un giorno d&#8217;estate",
        present_in=[Showing(cinema="Y", cinema_slug="y", date="2026-06-16", times=["21:15"])],
    )
    merged = _deduplicate_films([clean, encoded])
    assert len(merged) == 1, f"BUG dedup: {len(merged)} Film (atteso 1)"
    cs = sorted(s.cinema_slug for s in merged[0].present_in)
    assert cs == ["x", "y"], f"BUG: cinema perdeduti in dedup: {cs}"
