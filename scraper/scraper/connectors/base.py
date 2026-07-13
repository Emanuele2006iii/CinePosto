"""Abstract base class for all cinema connectors."""
from __future__ import annotations

import abc

from scraper.models import ScrapeResult


class BaseConnector(abc.ABC):
    """Interfaccia comune dei connettori: un connettore per cinema (pattern Strategy).

    Contratto: `scrape()` NON deve sollevare per errori di rete/parsing —
    li raccoglie in `ScrapeResult.errors` così una fonte rotta non blocca
    le altre. Aggiungere un cinema = implementare questa classe in un nuovo
    file e registrarla in main.py.
    """

    @property
    @abc.abstractmethod
    def cinema_name(self) -> str:
        """Nome del cinema mostrato all'utente (es. "PostModernissimo")."""
        ...

    @property
    @abc.abstractmethod
    def cinema_slug(self) -> str:
        """Identificatore stabile del cinema, chiave in CINEMA_LOCATIONS e nel DB."""
        ...

    @abc.abstractmethod
    def scrape(self, today: str, dates: list[str] | None = None) -> ScrapeResult:
        """Raccoglie la programmazione per le date richieste (default: prossimi 8 giorni).

        Args:
            today: data odierna ISO (YYYY-MM-DD), calcolata in Europe/Rome.
            dates: date da coprire; None = usa get_week_dates().
        """
        ...

    @abc.abstractmethod
    def fetch_film_detail(self, film_url: str) -> dict | None:
        """Recupera i metadati extra dalla pagina di dettaglio del film; None se non disponibili."""
        ...
