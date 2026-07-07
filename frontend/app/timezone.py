"""Helper per date/orari nel fuso orario dell'attività (default Europe/Rome).

Il frontend precompila la data odierna nel form nuova fattura. Con zoneinfo la
data resta corretta anche se il container gira in UTC, senza dipendere dal TZ.
Speculare a backend/app/timezone.py.
"""
import os
from datetime import date, datetime
from zoneinfo import ZoneInfo

_TZ = ZoneInfo(os.getenv("TZ", "Europe/Rome"))


def now_local() -> datetime:
    """Datetime corrente nel fuso orario dell'attività (naive)."""
    return datetime.now(_TZ).replace(tzinfo=None)


def today_local() -> date:
    """Data odierna nel fuso orario dell'attività."""
    return datetime.now(_TZ).date()
