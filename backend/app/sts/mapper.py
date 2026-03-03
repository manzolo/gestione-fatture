import xml.sax.saxutils as saxutils
from app.sts.encryption import encrypt_cf

_NS = "http://documentospesap730.sanita.finanze.it"


def _esc(value: str) -> str:
    return saxutils.escape(str(value))


def build_inserimento_payload(fattura, cliente, config: dict) -> str:
    """
    Costruisce l'envelope SOAP per l'operazione Inserimento.

    Struttura conforme a DocumentoSpesa730pSchema.xsd:
      inserimentoDocumentoSpesaRequest
        pincode
        Proprietario / cfProprietario
        idInserimentoDocumentoFiscale
          idSpesa / pIva, dataEmissione, numDocumentoFiscale
          dataPagamento
          cfCittadino
          voceSpesa / tipoSpesa, importo, aliquotaIVA
          pagamentoTracciato
          tipoDocumento
          flagOpposizione
    """
    piva = _esc(config["partita_iva"])
    pincode = _esc(config["pincode_encrypted"])
    cf_prop = _esc(config["cf_proprietario_encrypted"])
    dispositivo = int(config.get("dispositivo", 1))

    data_emissione = _esc(fattura.data_fattura.isoformat())
    num_documento = _esc(f"F{fattura.anno}{fattura.progressivo:04d}")
    data_pagamento = _esc(fattura.data_pagamento.isoformat())

    cf_cifrato = _esc(encrypt_cf(cliente.codice_fiscale, config.get("cert_path")))

    importo = f"{round(fattura.totale, 2):.2f}"
    flag_opposizione = "1" if getattr(cliente, "flag_opposizione", False) else "0"
    pagamento_tracciato = (
        "SI"
        if fattura.metodo_pagamento and fattura.metodo_pagamento.lower() != "contanti"
        else "NO"
    )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope
    xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:doc="{_NS}">
  <soapenv:Header/>
  <soapenv:Body>
    <doc:inserimentoDocumentoSpesaRequest>
      <pincode>{pincode}</pincode>
      <Proprietario>
        <cfProprietario>{cf_prop}</cfProprietario>
      </Proprietario>
      <idInserimentoDocumentoFiscale>
        <idSpesa>
          <pIva>{piva}</pIva>
          <dataEmissione>{data_emissione}</dataEmissione>
          <numDocumentoFiscale>
            <dispositivo>{dispositivo}</dispositivo>
            <numDocumento>{num_documento}</numDocumento>
          </numDocumentoFiscale>
        </idSpesa>
        <dataPagamento>{data_pagamento}</dataPagamento>
        <cfCittadino>{cf_cifrato}</cfCittadino>
        <voceSpesa>
          <tipoSpesa>SP</tipoSpesa>
          <importo>{importo}</importo>
          <aliquotaIVA>0.00</aliquotaIVA>
        </voceSpesa>
        <pagamentoTracciato>{pagamento_tracciato}</pagamentoTracciato>
        <tipoDocumento>F</tipoDocumento>
        <flagOpposizione>{flag_opposizione}</flagOpposizione>
      </idInserimentoDocumentoFiscale>
    </doc:inserimentoDocumentoSpesaRequest>
  </soapenv:Body>
</soapenv:Envelope>"""


def build_cancellazione_payload(fattura, cliente, config: dict) -> str:
    """
    Costruisce l'envelope SOAP per l'operazione Cancellazione.

    Struttura:
      cancellazioneDocumentoSpesaRequest
        pincode
        Proprietario / cfProprietario
        idCancellazioneDocumentoFiscale / pIva, dataEmissione, numDocumentoFiscale
    """
    piva = _esc(config["partita_iva"])
    pincode = _esc(config["pincode_encrypted"])
    cf_prop = _esc(config["cf_proprietario_encrypted"])
    dispositivo = int(config.get("dispositivo", 1))

    data_emissione = _esc(fattura.data_fattura.isoformat())
    num_documento = _esc(f"F{fattura.anno}{fattura.progressivo:04d}")

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope
    xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:doc="{_NS}">
  <soapenv:Header/>
  <soapenv:Body>
    <doc:cancellazioneDocumentoSpesaRequest>
      <pincode>{pincode}</pincode>
      <Proprietario>
        <cfProprietario>{cf_prop}</cfProprietario>
      </Proprietario>
      <idCancellazioneDocumentoFiscale>
        <pIva>{piva}</pIva>
        <dataEmissione>{data_emissione}</dataEmissione>
        <numDocumentoFiscale>
          <dispositivo>{dispositivo}</dispositivo>
          <numDocumento>{num_documento}</numDocumento>
        </numDocumentoFiscale>
      </idCancellazioneDocumentoFiscale>
    </doc:cancellazioneDocumentoSpesaRequest>
  </soapenv:Body>
</soapenv:Envelope>"""
