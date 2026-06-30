"""Abstract base class for all cinema connectors."""
from __future__ import annotations

import abc

from scraper.models import ScrapeResult


class BaseConnector(abc.ABC):
    @property
    @abc.abstractmethod
    def cinema_name(self) -> str:
        ...

    @property
    @abc.abstractmethod
    def cinema_slug(self) -> str:
        ...

    @abc.abstractmethod
    def scrape(self, today: str, dates: list[str] | None = None) -> ScrapeResult:
        ...

    @abc.abstractmethod
    def fetch_film_detail(self, film_url: str) -> dict | None:
        ...
