from flask import Blueprint, request, jsonify
from .models import db, Costo
from datetime import datetime

# Crea un Blueprint per le rotte API dei costi
costi_bp = Blueprint('costi_bp', __name__)

@costi_bp.route('/costs', methods=['POST'])
def add_costo():
    """Endpoint per l'aggiunta di un nuovo costo."""
    data = request.get_json()
    try:
        nuovo_costo = Costo(
            descrizione=data['descrizione'],
            anno_riferimento=data['anno_riferimento'],
            data_pagamento=datetime.strptime(data['data_pagamento'], '%Y-%m-%d').date(),
            totale=data['totale'],
            pagato=data.get('pagato', False)
        )
        db.session.add(nuovo_costo)
        db.session.commit()
        return jsonify({"message": "Costo aggiunto con successo!", "id": nuovo_costo.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Errore durante l'aggiunta del costo: {str(e)}"}), 500

@costi_bp.route('/costs', methods=['GET'])
def get_costs():
    """Endpoint per ottenere tutti i costi."""
    try:
        costs = Costo.query.order_by(Costo.data_pagamento.desc()).all()
        costs_data = [{
            "id": c.id,
            "descrizione": c.descrizione,
            "anno_riferimento": c.anno_riferimento,
            "data_pagamento": c.data_pagamento.strftime('%Y-%m-%d'),
            "totale": c.totale,
            "pagato": c.pagato
        } for c in costs]
        return jsonify(costs_data), 200
    except Exception as e:
        return jsonify({"message": f"Errore durante il recupero dei costi: {str(e)}"}), 500

@costi_bp.route('/costs/<int:costo_id>', methods=['GET'])
def get_single_cost(costo_id):
    """Endpoint per ottenere un singolo costo."""
    costo = Costo.query.get_or_404(costo_id)
    return jsonify({
        "id": costo.id,
        "descrizione": costo.descrizione,
        "anno_riferimento": costo.anno_riferimento,
        "data_pagamento": costo.data_pagamento.strftime('%Y-%m-%d'),
        "totale": costo.totale,
        "pagato": costo.pagato
    }), 200

@costi_bp.route('/costs/<int:costo_id>', methods=['PUT'])
def update_costo(costo_id):
    """Endpoint per la modifica di un costo esistente."""
    costo = Costo.query.get_or_404(costo_id)
    data = request.get_json()
    try:
        costo.descrizione = data.get('descrizione', costo.descrizione)
        costo.anno_riferimento = data.get('anno_riferimento', costo.anno_riferimento)
        costo.data_pagamento = datetime.strptime(data.get('data_pagamento'), '%Y-%m-%d').date() if data.get('data_pagamento') else costo.data_pagamento
        costo.totale = data.get('totale', costo.totale)
        costo.pagato = data.get('pagato', costo.pagato)
        
        db.session.commit()
        return jsonify({"message": "Costo aggiornato con successo!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Errore durante l'aggiornamento del costo: {str(e)}"}), 500

@costi_bp.route('/costs/<int:costo_id>', methods=['DELETE'])
def delete_costo(costo_id):
    """Endpoint per l'eliminazione di un costo."""
    costo = Costo.query.get_or_404(costo_id)
    try:
        db.session.delete(costo)
        db.session.commit()
        return jsonify({"message": "Costo eliminato con successo!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Errore durante l'eliminazione del costo: {str(e)}"}), 500
