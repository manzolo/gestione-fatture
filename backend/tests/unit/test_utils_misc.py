"""Unit test per format_numero_sedute, calculate_prezzo_base_da_totale e tipi di seduta."""
import pytest

from app.utils import (
    format_numero_sedute, calculate_prezzo_base_da_totale,
    build_descrizione_prestazione, normalize_tipo_seduta, TIPI_SEDUTA,
)


@pytest.mark.parametrize("valore,atteso", [
    (1.0, "1"),
    (2.0, "2"),
    (10.0, "10"),
    (1.5, "1,5"),
    (2.5, "2,5"),
    (0.5, "0,5"),
])
def test_format_numero_sedute(valore, atteso):
    assert format_numero_sedute(valore) == atteso


@pytest.mark.parametrize("totale,base_atteso", [
    (60.0, 58.82),
    (65.0, 63.73),
    (70.0, 68.63),
])
def test_calculate_prezzo_base_da_totale(totale, base_atteso):
    # la funzione non arrotonda: confronto sul valore arrotondato a 2 decimali
    assert round(calculate_prezzo_base_da_totale(totale), 2) == pytest.approx(base_atteso)


@pytest.mark.parametrize("numero,tipo,atteso", [
    (1.0, 'singola', "n. 1 di Seduta di consulenza psicologica"),
    (2.0, 'singola', "n. 2 di Sedute di consulenza psicologica"),
    (1.0, 'coppia', "n. 1 di Seduta di consulenza psicologica di coppia"),
    (1.5, 'coppia', "n. 1,5 di Sedute di consulenza psicologica di coppia"),
    (1.0, None, "n. 1 di Seduta di consulenza psicologica"),
    (1.0, 'Coppia', "n. 1 di Seduta di consulenza psicologica di coppia"),
])
def test_build_descrizione_prestazione(numero, tipo, atteso):
    assert build_descrizione_prestazione(numero, tipo) == atteso


@pytest.mark.parametrize("valore,atteso", [
    (None, 'singola'),
    ('', 'singola'),
    ('singola', 'singola'),
    (' COPPIA ', 'coppia'),
])
def test_normalize_tipo_seduta(valore, atteso):
    assert normalize_tipo_seduta(valore) == atteso


def test_normalize_tipo_seduta_sconosciuto():
    with pytest.raises(ValueError):
        normalize_tipo_seduta('famiglia')


@pytest.mark.parametrize("tipo,prezzo_totale,base_atteso", [
    ('singola', 60.00, 58.82),
    ('coppia', 70.00, 68.63),
])
def test_prezzi_proposti_tipi_seduta(tipo, prezzo_totale, base_atteso):
    # i prezzi proposti nel form devono restare quelli concordati (60 / 70 €)
    assert TIPI_SEDUTA[tipo]['prezzo_totale'] == prezzo_totale
    assert round(calculate_prezzo_base_da_totale(prezzo_totale), 2) == pytest.approx(base_atteso)
