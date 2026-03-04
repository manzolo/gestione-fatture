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
          voceSpesa / tipoSpesa, importo, naturaIVA
          pagamentoTracciato
          tipoDocumento
          flagOpposizione
    """
    piva = _esc(config["partita_iva"])
    pincode = _esc(config["pincode_encrypted"])
    cf_prop = _esc(config["cf_proprietario_encrypted"])
    dispositivo = int(config.get("dispositivo", 1))

    data_emissione = _esc(fattura.data_fattura.isoformat())
    num_documento = _esc(f"{fattura.progressivo}/{fattura.anno}")
    data_pagamento = _esc(fattura.data_pagamento.isoformat())

    natura_iva = _esc(config.get("natura_iva", "N2.2"))
    importo = f"{round(fattura.totale, 2):.2f}"
    flag_opposizione = "1" if getattr(cliente, "flag_opposizione", False) else "0"
    pagamento_tracciato = (
        "SI"
        if fattura.metodo_pagamento and fattura.metodo_pagamento.lower() != "contanti"
        else "NO"
    )

    # cfCittadino: non emettere il tag se flagOpposizione=1 (PDF pag.15)
    cf_cittadino_xml = ""
    if flag_opposizione != "1":
        cf_cifrato = _esc(encrypt_cf(cliente.codice_fiscale, config.get("cert_path")))
        cf_cittadino_xml = f"\n        <doc:cfCittadino>{cf_cifrato}</doc:cfCittadino>"

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope
    xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:doc="{_NS}">
  <soapenv:Header/>
  <soapenv:Body>
    <doc:inserimentoDocumentoSpesaRequest>
      <doc:pincode>{pincode}</doc:pincode>
      <doc:Proprietario>
        <doc:cfProprietario>{cf_prop}</doc:cfProprietario>
      </doc:Proprietario>
      <doc:idInserimentoDocumentoFiscale>
        <doc:idSpesa>
          <doc:pIva>{piva}</doc:pIva>
          <doc:dataEmissione>{data_emissione}</doc:dataEmissione>
          <doc:numDocumentoFiscale>
            <doc:dispositivo>{dispositivo}</doc:dispositivo>
            <doc:numDocumento>{num_documento}</doc:numDocumento>
          </doc:numDocumentoFiscale>
        </doc:idSpesa>
        <doc:dataPagamento>{data_pagamento}</doc:dataPagamento>{cf_cittadino_xml}
        <doc:voceSpesa>
          <doc:tipoSpesa>SP</doc:tipoSpesa>
          <doc:importo>{importo}</doc:importo>
          <doc:naturaIVA>{natura_iva}</doc:naturaIVA>
        </doc:voceSpesa>
        <doc:pagamentoTracciato>{pagamento_tracciato}</doc:pagamentoTracciato>
        <doc:tipoDocumento>F</doc:tipoDocumento>
        <doc:flagOpposizione>{flag_opposizione}</doc:flagOpposizione>
      </doc:idInserimentoDocumentoFiscale>
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
    num_documento = _esc(f"{fattura.progressivo}/{fattura.anno}")

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope
    xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:doc="{_NS}">
  <soapenv:Header/>
  <soapenv:Body>
    <doc:cancellazioneDocumentoSpesaRequest>
      <doc:pincode>{pincode}</doc:pincode>
      <doc:Proprietario>
        <doc:cfProprietario>{cf_prop}</doc:cfProprietario>
      </doc:Proprietario>
      <doc:idCancellazioneDocumentoFiscale>
        <doc:pIva>{piva}</doc:pIva>
        <doc:dataEmissione>{data_emissione}</doc:dataEmissione>
        <doc:numDocumentoFiscale>
          <doc:dispositivo>{dispositivo}</doc:dispositivo>
          <doc:numDocumento>{num_documento}</doc:numDocumento>
        </doc:numDocumentoFiscale>
      </doc:idCancellazioneDocumentoFiscale>
    </doc:cancellazioneDocumentoSpesaRequest>
  </soapenv:Body>
</soapenv:Envelope>"""
