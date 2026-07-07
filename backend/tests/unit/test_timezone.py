"""Unit test per l'helper timezone: la data locale non dipende dal TZ del container."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import app.timezone as tz


def test_now_local_is_naive(monkeypatch):
    monkeypatch.setattr(tz, "_TZ", ZoneInfo("Europe/Rome"))
    assert tz.now_local().tzinfo is None


def test_today_local_usa_zona_configurata(monkeypatch):
    monkeypatch.setattr(tz, "_TZ", ZoneInfo("Europe/Rome"))
    assert tz.today_local() == datetime.now(ZoneInfo("Europe/Rome")).date()


def test_offset_applicato_indipendente_da_utc(monkeypatch):
    # Etc/GMT-14 = UTC+14: l'ora locale precede UTC di ~14h.
    monkeypatch.setattr(tz, "_TZ", ZoneInfo("Etc/GMT-14"))
    local = tz.now_local()
    utc = datetime.now(timezone.utc).replace(tzinfo=None)
    diff = (local - utc).total_seconds()
    assert 13 * 3600 < diff < 15 * 3600
