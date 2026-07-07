"""Unit test deterministici per il calcolo dei totali fattura.

Nessun DB, nessun container: si testa la funzione pura calculate_invoice_totals.
Focus sulla logica fiscale critica: soglia bollo (strict >), sedute frazionarie,
arrotondamenti e prezzo base di default.
"""
import pytest

from app.utils import calculate_invoice_totals, PRESTAZIONE_BASE, BOLLO_COSTO


def test_una_seduta_default_sotto_soglia_no_bollo():
    r = calculate_invoice_totals(1)
    assert r["importo_unitario"] == PRESTAZIONE_BASE
    assert r["totale_imponibile"] == pytest.approx(60.00)
    assert r["bollo_flag"] is False
    assert r["bollo_importo"] == 0.0
    assert r["totale"] == pytest.approx(60.00)


def test_due_sedute_default_sopra_soglia_con_bollo():
    r = calculate_invoice_totals(2)
    # 58.82*2=117.64 ; contributo round(1.1764*2)=2.35 ; imponibile 119.99
    assert r["subtotale_base"] == pytest.approx(117.64)
    assert r["contributo"] == pytest.approx(2.35)
    assert r["totale_imponibile"] == pytest.approx(119.99)
    assert r["bollo_flag"] is True
    assert r["bollo_importo"] == BOLLO_COSTO
    assert r["totale"] == pytest.approx(121.99)


def test_soglia_bollo_esatta_77_47_non_applica_bollo():
    """Confine critico: a 77.47 esatti NON si applica il bollo (strict >)."""
    r = calculate_invoice_totals(1, prezzo_base_unitario=75.95)
    assert r["totale_imponibile"] == pytest.approx(77.47)
    assert r["bollo_flag"] is False
    assert r["bollo_importo"] == 0.0


def test_soglia_bollo_appena_sopra_applica_bollo():
    r = calculate_invoice_totals(1, prezzo_base_unitario=75.96)
    assert r["totale_imponibile"] == pytest.approx(77.48)
    assert r["bollo_flag"] is True
    assert r["bollo_importo"] == BOLLO_COSTO


def test_seduta_frazionaria_1_5():
    r = calculate_invoice_totals(1.5)
    assert r["subtotale_base"] == pytest.approx(88.23)
    assert r["contributo"] == pytest.approx(1.76)
    assert r["totale_imponibile"] == pytest.approx(89.99)
    assert r["bollo_flag"] is True
    assert r["totale"] == pytest.approx(91.99)


def test_seduta_frazionaria_2_5():
    r = calculate_invoice_totals(2.5)
    assert r["subtotale_base"] == pytest.approx(147.05)
    assert r["totale_imponibile"] == pytest.approx(149.99)
    assert r["bollo_flag"] is True


def test_sedute_negative_vengono_azzerate():
    r = calculate_invoice_totals(-3)
    assert r["numero_sedute"] == 0.0
    assert r["subtotale_base"] == 0.0
    assert r["contributo"] == 0.0
    assert r["totale_imponibile"] == 0.0
    assert r["bollo_flag"] is False
    assert r["totale"] == 0.0


def test_prezzo_base_none_usa_default():
    r_none = calculate_invoice_totals(2, prezzo_base_unitario=None)
    r_def = calculate_invoice_totals(2, prezzo_base_unitario=PRESTAZIONE_BASE)
    assert r_none == r_def
