import logging
import os
import ssl
import time
import xml.etree.ElementTree as ET

import requests
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from urllib3.util.ssl_ import create_urllib3_context

from app.sts.mapper import build_inserimento_payload, build_cancellazione_payload

logger = logging.getLogger(__name__)

STS_ENDPOINTS = {
    "test": "https://invioSS730pTest.sanita.finanze.it/DocumentoSpesa730pWeb/DocumentoSpesa730pPort",
    "production": "https://invioSS730p.sanita.finanze.it/DocumentoSpesa730pWeb/DocumentoSpesa730pPort",
}

SOAP_ACTION_INSERIMENTO = "inserimento.documentospesap730.sanita.finanze.it"
SOAP_ACTION_CANCELLAZIONE = "cancellazione.documentospesap730.sanita.finanze.it"

# Codici errore STS che non devono essere ritentati
NO_RETRY_CODES = {"WS002", "WS004"}

MAX_RETRIES = 3
RETRY_BACKOFF = 2  # secondi base per backoff esponenziale

# Cipher suite con SECLEVEL=1: necessario per i server governativi italiani
# che usano cipher suite considerate "legacy" da OpenSSL >= 1.1.1
_STS_CIPHERS = "DEFAULT@SECLEVEL=1"


class _STSSSLAdapter(HTTPAdapter):
    """
    HTTPAdapter con SSL context personalizzato per i server STS del MEF.

    Gestisce:
    - SECLEVEL=1 per cipher suite legacy (risolve SSLV3_ALERT_HANDSHAKE_FAILURE)
    - TLS 1.2 minimo
    - Verifica certificato opzionale (ssl_verify=False per ambiente test)
    - CA bundle personalizzato
    """

    def __init__(self, ssl_verify: bool = True, ca_bundle: str | None = None, **kwargs):
        self._ssl_verify = ssl_verify
        self._ca_bundle = ca_bundle
        super().__init__(**kwargs)

    def _build_ctx(self) -> ssl.SSLContext:
        if not self._ssl_verify:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            ctx = create_urllib3_context(ciphers=_STS_CIPHERS)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        else:
            ctx = create_urllib3_context(ciphers=_STS_CIPHERS)
            ctx.minimum_version = ssl.TLSVersion.TLSv1_2
            # Carica prima i certificati di sistema, poi eventualmente il CA bundle
            # aggiuntivo. Questo garantisce che la catena completa sia verificabile
            # anche se il bundle custom contiene solo certificati intermedi.
            ctx.set_default_verify_paths()
            if self._ca_bundle:
                ctx.load_verify_locations(cafile=self._ca_bundle)
        return ctx

    def init_poolmanager(self, *args, **kwargs):
        kwargs["ssl_context"] = self._build_ctx()
        super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, proxy, **proxy_kwargs):
        proxy_kwargs["ssl_context"] = self._build_ctx()
        return super().proxy_manager_for(proxy, **proxy_kwargs)


def _build_session(
    username: str,
    password: str,
    ca_bundle: str | None,
    ssl_verify: bool,
    environment: str,
) -> requests.Session:
    session = requests.Session()
    session.auth = HTTPBasicAuth(username, password)

    # Produzione: verifica SSL sempre obbligatoria
    effective_verify = True if environment == "production" else ssl_verify
    if not effective_verify:
        logger.warning(
            "STS_SSL_VERIFY=false: verifica certificato TLS disabilitata. "
            "Accettabile solo in ambiente di test."
        )

    effective_ca = ca_bundle if (ca_bundle and os.path.exists(ca_bundle)) else None
    if ca_bundle and not effective_ca:
        logger.warning("STS_CA_BUNDLE configurato (%s) ma file non trovato.", ca_bundle)

    adapter = _STSSSLAdapter(ssl_verify=effective_verify, ca_bundle=effective_ca)
    session.mount("https://", adapter)
    # session.verify deve essere coerente col contesto dell'adapter:
    # requests lo passa a urllib3 che altrimenti sovrascrive il verify_mode del ctx
    if not effective_verify:
        session.verify = False
    elif effective_ca:
        session.verify = effective_ca
    return session


def _parse_response(xml_text: str) -> dict:
    """
    Analizza la risposta XML di STS ed estrae esito, protocollo e messaggi.

    Struttura attesa (namespace http://documentospesap730.sanita.finanze.it):
      <esitoChiamata>0|1|2</esitoChiamata>  (0=ok, 1=errore, 2=ok+warning)
      <protocollo>...</protocollo>
      <listaMessaggi>
        <messaggio><codice>...</codice><descrizione>...</descrizione></messaggio>
      </listaMessaggi>

    Usa {*} per ricerca namespace-agnostic (Python 3.8+).
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        logger.error("Impossibile parsare la risposta XML STS: %s", exc)
        return {"success": False, "protocollo": None, "errors": [str(exc)], "raw": xml_text}

    def find_text(element, tag):
        node = element.find(".//{*}" + tag)
        return node.text.strip() if node is not None and node.text else ""

    esito = find_text(root, "esitoChiamata")
    protocollo = find_text(root, "protocollo") or None

    errors = []
    for msg in root.findall(".//{*}messaggio"):
        codice = find_text(msg, "codice")
        descrizione = find_text(msg, "descrizione")
        if codice or descrizione:
            errors.append({"codice": codice, "descrizione": descrizione})

    # PDF pag.18: esitoChiamata = 0 (ok), 1 (errore), 2 (ok con warning)
    success = esito in ("0", "2")
    return {"success": success, "protocollo": protocollo, "errors": errors, "raw": xml_text}


class STSClient:
    """
    Client SOAP per il Sistema Tessera Sanitaria.

    Le credenziali e la configurazione vengono lette dalle variabili d'ambiente:
      STS_ENVIRONMENT          test | production  (default: test)
      STS_USERNAME             username per HTTP Basic Auth
      STS_PASSWORD             password per HTTP Basic Auth
      STS_PINCODE_ENCRYPTED    pinCode già cifrato RSA (fornito da STS per test)
      STS_CF_PROPRIETARIO_ENCRYPTED  cfProprietario già cifrato RSA
      STS_PARTITA_IVA          P.IVA del professionista
      STS_DISPOSITIVO          numero dispositivo (default: 1)
      STS_CERTIFICATE_PATH     path PEM per cifrare il CF paziente (opzionale)
    """

    def __init__(self):
        env = os.getenv("STS_ENVIRONMENT", "test").lower()
        self.endpoint = STS_ENDPOINTS.get(env, STS_ENDPOINTS["test"])
        self.debug = os.getenv("STS_DEBUG", "false").lower() in ("true", "1", "yes")
        self.username = os.getenv("STS_USERNAME", "")
        self.password = os.getenv("STS_PASSWORD", "")
        self.config = {
            "partita_iva": os.getenv("STS_PARTITA_IVA", ""),
            "pincode_encrypted": os.getenv("STS_PINCODE_ENCRYPTED", ""),
            "cf_proprietario_encrypted": os.getenv("STS_CF_PROPRIETARIO_ENCRYPTED", ""),
            "dispositivo": int(os.getenv("STS_DISPOSITIVO", "1")),
            "cert_path": os.getenv("STS_CERTIFICATE_PATH", None),
            "natura_iva": os.getenv("STS_NATURA_IVA", "N2.2"),
        }
        self._ca_bundle = os.getenv("STS_CA_BUNDLE", None)
        ssl_verify_env = os.getenv("STS_SSL_VERIFY", "true").lower()
        ssl_verify = ssl_verify_env not in ("false", "0", "no")
        self._session = _build_session(
            self.username, self.password, self._ca_bundle, ssl_verify, env
        )

    def _post_soap(self, payload: str, soap_action: str) -> requests.Response:
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": soap_action,
        }

        last_exc = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = self._session.post(
                    self.endpoint,
                    data=payload.encode("utf-8"),
                    headers=headers,
                    timeout=30,
                )
                # Qualsiasi risposta HTTP (anche 5xx) = connessione riuscita, niente retry
                return resp
            except requests.exceptions.SSLError as exc:
                # Errore SSL non transitorio: non ritentare
                raise RuntimeError(f"STS SSL error: {exc}") from exc
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
                last_exc = exc
                logger.warning(
                    "STS request error (attempt %d/%d): %s", attempt, MAX_RETRIES, exc
                )

            if attempt < MAX_RETRIES:
                time.sleep(min(RETRY_BACKOFF ** attempt, 3))

        raise RuntimeError(
            f"STS non raggiungibile dopo {MAX_RETRIES} tentativi: {last_exc}"
        )

    def _should_retry_errors(self, errors: list) -> bool:
        for e in errors:
            codice = e.get("codice", "")
            if codice in NO_RETRY_CODES:
                return False
        return True

    def send_inserimento(self, fattura, cliente) -> dict:
        """Invia una spesa sanitaria a STS."""
        payload = build_inserimento_payload(fattura, cliente, self.config)
        logger.debug("STS inserimento payload:\n%s", payload)

        if self.debug:
            logger.info("STS DEBUG MODE: inserimento payload generato, invio saltato.")
            return {
                "success": True,
                "debug_mode": True,
                "soap_payload": payload,
                "protocollo": f"DEBUG-{int(time.time())}",
                "errors": [],
                "raw": "",
            }

        try:
            resp = self._post_soap(payload, SOAP_ACTION_INSERIMENTO)
        except RuntimeError as exc:
            return {"success": False, "protocollo": None, "errors": [str(exc)], "raw": ""}

        result = _parse_response(resp.text)

        if not result["success"]:
            for err in result["errors"]:
                logger.warning(
                    "STS inserimento errore [%s]: %s",
                    err.get("codice"), err.get("descrizione"),
                )

        return result

    def send_cancellazione(self, fattura, cliente) -> dict:
        """Annulla un invio precedente su STS."""
        if not fattura.protocollo_sts:
            return {
                "success": False,
                "protocollo": None,
                "errors": [{"codice": "LOCAL", "descrizione": "protocollo_sts non presente"}],
                "raw": "",
            }

        payload = build_cancellazione_payload(fattura, cliente, self.config)
        logger.debug("STS cancellazione payload:\n%s", payload)

        if self.debug:
            logger.info("STS DEBUG MODE: cancellazione payload generato, invio saltato.")
            return {
                "success": True,
                "debug_mode": True,
                "soap_payload": payload,
                "protocollo": fattura.protocollo_sts,
                "errors": [],
                "raw": "",
            }

        try:
            resp = self._post_soap(payload, SOAP_ACTION_CANCELLAZIONE)
        except RuntimeError as exc:
            return {"success": False, "protocollo": None, "errors": [str(exc)], "raw": ""}

        result = _parse_response(resp.text)

        if not result["success"]:
            for err in result["errors"]:
                logger.warning(
                    "STS cancellazione errore [%s]: %s",
                    err.get("codice"), err.get("descrizione"),
                )

        return result
