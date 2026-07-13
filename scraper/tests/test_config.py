"""Test di config: finestra date della run e calcolo di oggi in Europe/Rome."""
from __future__ import annotations

from datetime import date, datetime
from unittest import mock
from zoneinfo import ZoneInfo

from scraper.config import get_week_dates, today_local


def test_get_week_dates_starts_today():
    dates = get_week_dates(date(2026, 6, 14))
    assert dates[0] == "2026-06-14"
    assert len(dates) == 8


def test_get_week_dates_sunday_issue():
    dates = get_week_dates(date(2026, 6, 14))
    assert "2026-06-15" in dates
    assert "2026-06-21" in dates


def test_get_week_dates_monday():
    dates = get_week_dates(date(2026, 6, 8))
    assert dates[0] == "2026-06-08"
    assert dates[-1] == "2026-06-15"


def test_get_week_dates_no_arg():
    """When called with no arg, must use Italian local 'today' (Europe/Rome),
    not the host server's UTC date — see PlanAudit fix for TZ rollover bug.
    """
    dates = get_week_dates()
    assert len(dates) == 8
    assert dates[0] == today_local().isoformat()


def test_today_local_rollover_at_italian_midnight():
    """At 01:30 in Rome the date must roll over, even if UTC is still prev day.
    Simulates UTC=23:30, Rome=01:30 (next day) — today_local() must return D+1.
    """
    fake_now = datetime(2026, 6, 18, 1, 30, 0, tzinfo=ZoneInfo("Europe/Rome"))
    with mock.patch("scraper.config.datetime") as fake_dt:
        fake_dt.now.return_value = fake_now
        d = today_local()
        assert d == date(2026, 6, 18), f"Expected rollover to 2026-06-18, got {d}"


def test_today_local_returns_object_of_type_date():
    d = today_local()
    assert isinstance(d, date)
