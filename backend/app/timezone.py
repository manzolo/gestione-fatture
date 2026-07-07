"""Helper per date/orari nel fuso orario dell'attività (default Europe/Rome).

Il codice usa date "naive" per precompilare la data fattura. Se il container
girasse in UTC, tra mezzanotte e le ~02:00 (ora legale) la data verrebbe
precompilata col giorno precedente. Storicamente la correttezza dipendeva SOLO
dalla variabile TZ del compose (allineata a mano su prod). Centralizzando qui la
regola "oggi = ora locale attività" con zoneinfo, la data resta corretta anche se
il container gira in UTC, indipendentemente dal TZ dei container.

La zona è comunque configurabile via env TZ (coerente con i container).
"""
import os
from datetime import date, datetime
from zoneinfo import ZoneInfo

_TZ = ZoneInfo(os.getenv("TZ", "Europe/Rome"))


def now_local() -> datetime:
    """Datetime corrente nel fuso orario dell'attività (naive, come i default storici)."""
    return datetime.now(_TZ).replace(tzinfo=None)


def today_local() -> date:
    """Data odierna nel fuso orario dell'attività."""
    return datetime.now(_TZ).date()
