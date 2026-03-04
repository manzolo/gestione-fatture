import logging
import os
from datetime import datetime

from flask import Blueprint, jsonify, request

from app.models import db, Fattura, Cliente

logger = logging.getLogger(__name__)

sts_bp = Blueprint("sts_bp", __name__)


def _sts_client():
    """Istanzia STSClient solo quando STS_USERNAME è configurato."""
    from app.sts.client import STSClient
    return STSClient()


def _sts_configured() -> bool:
    return bool(os.getenv("STS_USERNAME"))


def _fattura_sts_dict(fattura) -> dict:
    return {
        "id": fattura.id,
        "numero_fattura": f"{fattura.progressivo}/{fattura.anno}",
        "data_fattura": fattura.data_fattura.isoformat(),
        "data_pagamento": fattura.data_pagamento.isoformat() if fattura.data_pagamento else None,
        "totale": fattura.totale,
        "inviata_sts": fattura.inviata_sts,
        "protocollo_sts": fattura.protocollo_sts,
        "data_invio_sts": fattura.data_invio_sts.isoformat() if fattura.data_invio_sts else None,
        "cliente": (
            f"{fattura.cliente.nome} {fattura.cliente.cognome}" if fattura.cliente else None
        ),
    }


@sts_bp.route("/sts/invoices/unsent", methods=["GET"])
def sts_unsent():
    """Lista fatture non ancora inviate a STS con data_pagamento valorizzata."""
    year = request.args.get("year", type=int)
    query = Fattura.query.filter(
        Fattura.inviata_sts == False,
        Fattura.data_pagamento.isnot(None),
    )
    if year:
        query = query.filter(Fattura.anno == year)
    fatture = query.order_by(Fattura.anno.desc(), Fattura.progressivo.desc()).all()
    return jsonify([_fattura_sts_dict(f) for f in fatture])


@sts_bp.route("/sts/invoices/<int:invoice_id>/send", methods=["POST"])
def sts_send_single(invoice_id):
    """Invia una singola fattura a STS."""
    if not _sts_configured():
        return jsonify({
            "success": False,
            "error": "STS non configurato: impostare STS_USERNAME nelle variabili d'ambiente.",
        }), 503

    fattura = Fattura.query.get_or_404(invoice_id)
    force = request.args.get("force", "false").lower() == "true"

    if not fattura.data_pagamento:
        return jsonify({
            "success": False,
            "error": "data_pagamento obbligatoria per l'invio a STS.",
        }), 400

    if fattura.inviata_sts and not force:
        return jsonify({
            "success": False,
            "error": "Fattura già inviata a STS. Usa ?force=true per reinviare.",
            "protocollo_sts": fattura.protocollo_sts,
        }), 409

    cliente = Cliente.query.get_or_404(fattura.cliente_id)

    client = _sts_client()
    result = client.send_inserimento(fattura, cliente)

    is_debug = result.get("debug_mode", False)

    if result["success"] and not is_debug:
        fattura.inviata_sts = True
        fattura.protocollo_sts = result.get("protocollo")
        fattura.data_invio_sts = datetime.utcnow()
        db.session.commit()
        logger.info(
            "Fattura %d inviata a STS, protocollo: %s",
            invoice_id, fattura.protocollo_sts,
        )

    response = {
        "success": result["success"],
        "fattura_id": invoice_id,
        "protocollo": result.get("protocollo"),
        "errors": result.get("errors", []),
    }
    if is_debug:
        response["debug_mode"] = True
        response["soap_payload"] = result.get("soap_payload", "")

    return jsonify(response), 200 if result["success"] else 422


@sts_bp.route("/sts/invoices/send-batch", methods=["POST"])
def sts_send_batch():
    """
    Invia un batch di fatture a STS.
    Body JSON: {"year": 2025} oppure {"ids": [1, 2, 3]}
    """
    if not _sts_configured():
        return jsonify({
            "success": False,
            "error": "STS non configurato: impostare STS_USERNAME nelle variabili d'ambiente.",
        }), 503

    data = request.get_json(silent=True) or {}
    year = data.get("year")
    ids = data.get("ids")

    if year:
        fatture = Fattura.query.filter(
            Fattura.anno == year,
            Fattura.inviata_sts == False,
            Fattura.data_pagamento.isnot(None),
        ).all()
    elif ids:
        fatture = Fattura.query.filter(
            Fattura.id.in_(ids),
            Fattura.data_pagamento.isnot(None),
        ).all()
    else:
        return jsonify({"success": False, "error": "Specificare 'year' o 'ids'."}), 400

    client = _sts_client()
    results = []

    for fattura in fatture:
        cliente = Cliente.query.get(fattura.cliente_id)
        if not cliente:
            results.append({"fattura_id": fattura.id, "success": False, "error": "Cliente non trovato"})
            continue

        result = client.send_inserimento(fattura, cliente)

        is_debug = result.get("debug_mode", False)

        if result["success"] and not is_debug:
            fattura.inviata_sts = True
            fattura.protocollo_sts = result.get("protocollo")
            fattura.data_invio_sts = datetime.utcnow()
            db.session.commit()

        entry = {
            "fattura_id": fattura.id,
            "success": result["success"],
            "protocollo": result.get("protocollo"),
            "errors": result.get("errors", []),
        }
        if is_debug:
            entry["debug_mode"] = True
            entry["soap_payload"] = result.get("soap_payload", "")

        results.append(entry)

    total = len(results)
    sent = sum(1 for r in results if r["success"])
    return jsonify({
        "total": total,
        "sent": sent,
        "failed": total - sent,
        "results": results,
    })


@sts_bp.route("/sts/invoices/<int:invoice_id>/cancel", methods=["POST"])
def sts_cancel_single(invoice_id):
    """Annulla l'invio di una fattura su STS (cancellazione)."""
    if not _sts_configured():
        return jsonify({
            "success": False,
            "error": "STS non configurato: impostare STS_USERNAME nelle variabili d'ambiente.",
        }), 503

    fattura = Fattura.query.get_or_404(invoice_id)

    if not fattura.inviata_sts:
        return jsonify({
            "success": False,
            "error": "Fattura non risulta inviata a STS.",
        }), 400

    if not fattura.protocollo_sts:
        return jsonify({
            "success": False,
            "error": "Fattura flaggata manualmente come inviata: impossibile annullare su STS senza protocollo.",
        }), 400

    cliente = Cliente.query.get_or_404(fattura.cliente_id)

    client = _sts_client()
    result = client.send_cancellazione(fattura, cliente)

    is_debug = result.get("debug_mode", False)

    if result["success"] and not is_debug:
        fattura.inviata_sts = False
        fattura.protocollo_sts = None
        fattura.data_invio_sts = None
        db.session.commit()
        logger.info("Fattura %d cancellata da STS.", invoice_id)

    response = {
        "success": result["success"],
        "fattura_id": invoice_id,
        "errors": result.get("errors", []),
    }
    if is_debug:
        response["debug_mode"] = True
        response["soap_payload"] = result.get("soap_payload", "")

    return jsonify(response), 200 if result["success"] else 422
