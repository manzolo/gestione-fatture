import logging
import os

logger = logging.getLogger(__name__)


def encrypt_cf(plain_cf: str, cert_path: str | None) -> str:
    """
    Cifra il codice fiscale del cittadino con RSA PKCS#1 v1.5 usando il
    certificato pubblico SanitelCF fornito da STS.

    Fase iniziale (placeholder): se cert_path è None o il file non esiste,
    restituisce il CF in chiaro con un warning. Il test STS accetta il CF
    non cifrato.

    Fase futura: montare il certificato PEM in STS_CERTIFICATE_PATH e
    aggiungere `cryptography>=42.0.0` a requirements.txt per abilitare
    la cifratura reale.
    """
    if not cert_path or not os.path.exists(cert_path):
        logger.warning(
            "STS_CERTIFICATE_PATH non configurato o file assente (%s): "
            "il codice fiscale verrà inviato in chiaro. "
            "Accettabile solo in ambiente di test.",
            cert_path,
        )
        return plain_cf

    try:
        from cryptography.hazmat.primitives import serialization, hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        import base64

        with open(cert_path, "rb") as f:
            cert_data = f.read()

        # Carica come certificato X.509 o chiave pubblica PEM
        try:
            from cryptography import x509
            cert = x509.load_pem_x509_certificate(cert_data)
            public_key = cert.public_key()
        except Exception:
            public_key = serialization.load_pem_public_key(cert_data)

        encrypted = public_key.encrypt(
            plain_cf.encode("utf-8"),
            padding.PKCS1v15(),
        )
        return base64.b64encode(encrypted).decode("utf-8")

    except ImportError:
        logger.warning(
            "Libreria `cryptography` non installata. "
            "Il codice fiscale verrà inviato in chiaro."
        )
        return plain_cf
    except Exception as exc:
        logger.error("Errore durante la cifratura del CF: %s", exc)
        return plain_cf
