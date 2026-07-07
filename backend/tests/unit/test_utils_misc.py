"""Unit test per format_numero_sedute e calculate_prezzo_base_da_totale."""
import pytest

from app.utils import format_numero_sedute, calculate_prezzo_base_da_totale


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
