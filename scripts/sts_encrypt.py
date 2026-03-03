#!/usr/bin/env python3
"""
Genera i valori cifrati RSA per STS_PINCODE_ENCRYPTED e STS_CF_PROPRIETARIO_ENCRYPTED.

Uso:
    python3 scripts/sts_encrypt.py --pincode 1234567890 --cf RSSMRA80A01H501U

Requisiti:
    pip install cryptography

Il certificato certs/sts_cert.pem deve essere presente (copiato da kit730P_ver_20240214/SanitelCF.cer).
"""
import argparse
import base64
import os
import sys


def encrypt(value: str, cert_path: str) -> str:
    try:
        from cryptography import x509
        from cryptography.hazmat.primitives.asymmetric import padding
    except ImportError:
        sys.exit("Errore: installa la libreria cryptography con: pip install cryptography")

    if not os.path.exists(cert_path):
        sys.exit(f"Errore: certificato non trovato: {cert_path}")

    with open(cert_path, "rb") as f:
        cert = x509.load_pem_x509_certificate(f.read())

    encrypted = cert.public_key().encrypt(value.encode("utf-8"), padding.PKCS1v15())
    return base64.b64encode(encrypted).decode("utf-8")


def main():
    parser = argparse.ArgumentParser(description="Cifra pincode e CF per STS")
    parser.add_argument("--pincode", required=True, help="Pincode in chiaro (es: 1234567890)")
    parser.add_argument("--cf", required=True, help="Codice Fiscale proprietario in chiaro")
    parser.add_argument(
        "--cert",
        default=os.path.join(os.path.dirname(__file__), "..", "certs", "sts_cert.pem"),
        help="Percorso al certificato SanitelCF PEM (default: certs/sts_cert.pem)",
    )
    args = parser.parse_args()

    cert_path = os.path.abspath(args.cert)
    print(f"Certificato: {cert_path}")
    print()

    pincode_enc = encrypt(args.pincode, cert_path)
    cf_enc = encrypt(args.cf, cert_path)

    print("Copia questi valori nel file .env:\n")
    print(f"STS_PINCODE_ENCRYPTED={pincode_enc}")
    print(f"STS_CF_PROPRIETARIO_ENCRYPTED={cf_enc}")
    print()
    print("NOTA: RSA PKCS#1 v1.5 è non-deterministico: ogni esecuzione produce")
    print("      valori diversi ma tutti ugualmente validi.")


if __name__ == "__main__":
    main()
