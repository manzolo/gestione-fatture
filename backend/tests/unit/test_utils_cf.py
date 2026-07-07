"""Unit test deterministici per decode_codice_fiscale.

La data di riferimento per l'euristica del secolo viene iniettata (parametro
`oggi`), così il test non dipende dalla data reale di esecuzione.
"""
from datetime import date

from app.utils import decode_codice_fiscale

OGGI = date(2026, 7, 7)


def test_cf_maschile_valido():
    r = decode_codice_fiscale("RSSMRA85M01H501Z", oggi=OGGI)
    assert r == {"sesso": "M", "data_nascita": date(1985, 8, 1)}


def test_cf_femminile_giorno_piu_40():
    # giorno 41 -> femmina, giorno reale 01
    r = decode_codice_fiscale("RSSMRA85M41H501Z", oggi=OGGI)
    assert r["sesso"] == "F"
    assert r["data_nascita"] == date(1985, 8, 1)


def test_cf_omocodia_nelle_posizioni_numeriche():
    # anno '8R': R -> 5 (omocodia) => 85, identico al CF senza omocodia
    r = decode_codice_fiscale("RSSMRA8RM01H501Z", oggi=OGGI)
    assert r["data_nascita"] == date(1985, 8, 1)


def test_cf_lunghezza_errata_ritorna_none():
    assert decode_codice_fiscale("ABC", oggi=OGGI) is None


def test_cf_mese_non_valido_ritorna_none():
    # 'Z' non è una lettera-mese valida
    assert decode_codice_fiscale("RSSMRA85Z01H501Z", oggi=OGGI) is None


def test_cf_data_impossibile_ritorna_none():
    # giorno 32 (agosto) -> date() solleva ValueError -> None
    assert decode_codice_fiscale("RSSMRA85M32H501Z", oggi=OGGI) is None


def test_cf_vuoto_o_none_ritorna_none():
    assert decode_codice_fiscale("", oggi=OGGI) is None
    assert decode_codice_fiscale(None, oggi=OGGI) is None


def test_cf_euristica_secolo_dipende_da_oggi():
    # anno '20': con oggi=2026 -> 2020; con oggi=2019 -> 1920
    r_2020 = decode_codice_fiscale("RSSMRA20M01H501Z", oggi=date(2026, 1, 1))
    assert r_2020["data_nascita"] == date(2020, 8, 1)
    r_1920 = decode_codice_fiscale("RSSMRA20M01H501Z", oggi=date(2019, 1, 1))
    assert r_1920["data_nascita"] == date(1920, 8, 1)
