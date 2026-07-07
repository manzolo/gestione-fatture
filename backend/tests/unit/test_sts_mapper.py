"""Unit test per il mapping STS (mapper.py).

Nessuna rete, nessun DB: fattura/cliente sono fake (SimpleNamespace) e la
cifratura del CF è disattivata (cert_path=None -> encrypt_cf ritorna il CF in
chiaro, deterministico).
"""
from datetime import date
from types import SimpleNamespace

from app.sts.mapper import build_inserimento_payload, build_cancellazione_payload

CONFIG = {
    "partita_iva": "65498732105",
    "pincode_encrypted": "PINCODE_ENC",
    "cf_proprietario_encrypted": "CFPROP_ENC",
    "dispositivo": 1,
    "natura_iva": "N2.2",
    "cert_path": None,  # disattiva la cifratura -> CF in chiaro, deterministico
}


def _fattura(**kw):
    base = dict(
        data_fattura=date(2025, 3, 10),
        progressivo=3,
        anno=2025,
        data_pagamento=date(2025, 3, 15),
        totale=60.0,
        metodo_pagamento="bonifico",
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _cliente(**kw):
    base = dict(codice_fiscale="RSSMRA85M01H501Z", flag_opposizione=False)
    base.update(kw)
    return SimpleNamespace(**base)


def test_inserimento_num_documento_e_importo():
    xml = build_inserimento_payload(_fattura(), _cliente(), CONFIG)
    assert "<doc:numDocumento>3/2025</doc:numDocumento>" in xml
    assert "<doc:importo>60.00</doc:importo>" in xml
    assert "<doc:dataEmissione>2025-03-10</doc:dataEmissione>" in xml
    assert "<doc:dataPagamento>2025-03-15</doc:dataPagamento>" in xml


def test_inserimento_flag_opposizione_zero_include_cf():
    xml = build_inserimento_payload(_fattura(), _cliente(flag_opposizione=False), CONFIG)
    assert "<doc:flagOpposizione>0</doc:flagOpposizione>" in xml
    assert "cfCittadino" in xml
    # CF in chiaro (cert_path=None)
    assert "RSSMRA85M01H501Z" in xml


def test_inserimento_flag_opposizione_uno_omette_cf():
    xml = build_inserimento_payload(_fattura(), _cliente(flag_opposizione=True), CONFIG)
    assert "<doc:flagOpposizione>1</doc:flagOpposizione>" in xml
    assert "cfCittadino" not in xml
    assert "RSSMRA85M01H501Z" not in xml


def test_inserimento_pagamento_tracciato_bonifico_si():
    xml = build_inserimento_payload(_fattura(metodo_pagamento="bonifico"), _cliente(), CONFIG)
    assert "<doc:pagamentoTracciato>SI</doc:pagamentoTracciato>" in xml


def test_inserimento_pagamento_tracciato_contanti_no():
    for metodo in ("contanti", "Contanti", "CONTANTI"):
        xml = build_inserimento_payload(_fattura(metodo_pagamento=metodo), _cliente(), CONFIG)
        assert "<doc:pagamentoTracciato>NO</doc:pagamentoTracciato>" in xml


def test_inserimento_pagamento_tracciato_vuoto_no():
    for metodo in ("", None):
        xml = build_inserimento_payload(_fattura(metodo_pagamento=metodo), _cliente(), CONFIG)
        assert "<doc:pagamentoTracciato>NO</doc:pagamentoTracciato>" in xml


def test_inserimento_importo_arrotondato_due_decimali():
    xml = build_inserimento_payload(_fattura(totale=121.9), _cliente(), CONFIG)
    assert "<doc:importo>121.90</doc:importo>" in xml


def test_cancellazione_num_documento_e_piva():
    xml = build_cancellazione_payload(_fattura(), _cliente(), CONFIG)
    assert "<doc:numDocumento>3/2025</doc:numDocumento>" in xml
    assert "<doc:pIva>65498732105</doc:pIva>" in xml
    assert "<doc:dataEmissione>2025-03-10</doc:dataEmissione>" in xml
    assert "cancellazioneDocumentoSpesaRequest" in xml
