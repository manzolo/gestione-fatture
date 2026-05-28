from flask import Blueprint, request, jsonify
from app.models import db, Costo, CostoRicorrente
from datetime import date, datetime
from sqlalchemy import extract, func
import calendar

# Crea un Blueprint per le rotte API dei costi
costi_bp = Blueprint('costi_bp', __name__)

FREQUENZE_RICORRENZA = {
    'mensile': 1,
    'trimestrale': 3,
    'annuale': 12,
}


def parse_date(value, field_name):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError as exc:
        raise ValueError(f"{field_name} deve avere formato YYYY-MM-DD") from exc


def bool_from_payload(data, key, default=False):
    value = data.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    return bool(value)


def add_months(source_date, months):
    month_index = source_date.month - 1 + months
    year = source_date.year + month_index // 12
    month = month_index % 12 + 1
    day = min(source_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def due_date_for_period(year, month, day):
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(day, last_day))


def serialize_cost(costo):
    return {
        "id": costo.id,
        "descrizione": costo.descrizione,
        "anno_riferimento": costo.anno_riferimento,
        "data_pagamento": costo.data_pagamento.strftime('%Y-%m-%d'),
        "totale": costo.totale,
        "pagato": costo.pagato,
        "ricorrenza_id": costo.ricorrenza_id,
        "periodo_riferimento": costo.periodo_riferimento
    }


def serialize_recurring_cost(ricorrenza):
    return {
        "id": ricorrenza.id,
        "descrizione": ricorrenza.descrizione,
        "totale": ricorrenza.totale,
        "frequenza": ricorrenza.frequenza,
        "giorno_scadenza": ricorrenza.giorno_scadenza,
        "data_inizio": ricorrenza.data_inizio.strftime('%Y-%m-%d'),
        "data_fine": ricorrenza.data_fine.strftime('%Y-%m-%d') if ricorrenza.data_fine else None,
        "pagato_default": ricorrenza.pagato_default,
        "attivo": ricorrenza.attivo
    }


def build_recurring_cost(data):
    frequenza = data.get('frequenza', 'mensile')
    if frequenza not in FREQUENZE_RICORRENZA:
        raise ValueError("Frequenza non valida")

    giorno_scadenza = int(data.get('giorno_scadenza', 1))
    if giorno_scadenza < 1 or giorno_scadenza > 31:
        raise ValueError("Il giorno di scadenza deve essere tra 1 e 31")

    totale = float(data['totale'])
    if totale <= 0:
        raise ValueError("Il totale deve essere positivo")

    data_inizio = parse_date(data.get('data_inizio'), 'data_inizio')
    if not data_inizio:
        raise ValueError("La data di inizio è obbligatoria")

    data_fine = parse_date(data.get('data_fine'), 'data_fine')
    if data_fine and data_fine < data_inizio:
        raise ValueError("La data di fine non può precedere la data di inizio")

    return CostoRicorrente(
        descrizione=data['descrizione'],
        totale=totale,
        frequenza=frequenza,
        giorno_scadenza=giorno_scadenza,
        data_inizio=data_inizio,
        data_fine=data_fine,
        pagato_default=bool_from_payload(data, 'pagato_default', False),
        attivo=bool_from_payload(data, 'attivo', True)
    )


def generate_recurring_costs(until_date=None, commit=True):
    until_date = until_date or date.today()
    created = 0
    ricorrenze = CostoRicorrente.query.filter_by(attivo=True).all()

    for ricorrenza in ricorrenze:
        step_months = FREQUENZE_RICORRENZA[ricorrenza.frequenza]
        current = date(ricorrenza.data_inizio.year, ricorrenza.data_inizio.month, 1)
        end_date = min(ricorrenza.data_fine or until_date, until_date)

        while current <= end_date:
            due_date = due_date_for_period(current.year, current.month, ricorrenza.giorno_scadenza)
            if due_date >= ricorrenza.data_inizio and due_date <= end_date:
                periodo = f"{current.year:04d}-{current.month:02d}"
                exists = Costo.query.filter_by(
                    ricorrenza_id=ricorrenza.id,
                    periodo_riferimento=periodo
                ).first()
                if not exists:
                    db.session.add(Costo(
                        descrizione=f"{ricorrenza.descrizione} - {periodo}",
                        anno_riferimento=current.year,
                        data_pagamento=due_date,
                        totale=ricorrenza.totale,
                        pagato=ricorrenza.pagato_default,
                        ricorrenza_id=ricorrenza.id,
                        periodo_riferimento=periodo
                    ))
                    created += 1
            current = add_months(current, step_months)

    if created and commit:
        db.session.commit()
    return created


@costi_bp.route('/costs', methods=['POST'])
def add_costo():
    """Endpoint per l'aggiunta di un nuovo costo."""
    data = request.get_json()
    try:
        nuovo_costo = Costo(
            descrizione=data['descrizione'],
            anno_riferimento=data['anno_riferimento'],
            data_pagamento=parse_date(data['data_pagamento'], 'data_pagamento'),
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
        generate_recurring_costs()
        costs = Costo.query.order_by(Costo.data_pagamento.desc()).all()
        costs_data = [serialize_cost(c) for c in costs]
        return jsonify(costs_data), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Errore durante il recupero dei costi: {str(e)}"}), 500


@costi_bp.route('/costs/stats', methods=['GET'])
def get_costs_stats():
    """Endpoint per ottenere le statistiche dei costi."""
    try:
        generate_recurring_costs()
        year = request.args.get('year', type=int)
        query = Costo.query

        if year:
            query = query.filter(Costo.anno_riferimento == year)

        totale_annuo = query.with_entities(func.coalesce(func.sum(Costo.totale), 0)).scalar() or 0

        if year:
            mese_expr = extract('month', Costo.data_pagamento)
            per_mese_rows = (
                db.session.query(
                    mese_expr.label('mese'),
                    func.coalesce(func.sum(Costo.totale), 0).label('totale')
                )
                .filter(Costo.anno_riferimento == year)
                .group_by(mese_expr)
                .order_by(mese_expr)
                .all()
            )
            return jsonify({
                "anno_selezionato": year,
                "totale_annuo": float(totale_annuo),
                "per_mese": [
                    {"mese": int(row.mese), "totale": float(row.totale)}
                    for row in per_mese_rows
                ]
            }), 200

        per_anno_rows = (
            db.session.query(
                Costo.anno_riferimento.label('anno'),
                func.coalesce(func.sum(Costo.totale), 0).label('totale')
            )
            .group_by(Costo.anno_riferimento)
            .order_by(Costo.anno_riferimento)
            .all()
        )
        return jsonify({
            "anno_selezionato": None,
            "totale_annuo": float(totale_annuo),
            "per_anno": [
                {"anno": int(row.anno), "totale": float(row.totale)}
                for row in per_anno_rows
            ]
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Errore durante il recupero delle statistiche dei costi: {str(e)}"}), 500

@costi_bp.route('/costs/<int:costo_id>', methods=['GET'])
def get_single_cost(costo_id):
    """Endpoint per ottenere un singolo costo."""
    costo = Costo.query.get_or_404(costo_id)
    return jsonify(serialize_cost(costo)), 200

@costi_bp.route('/costs/<int:costo_id>', methods=['PUT'])
def update_costo(costo_id):
    """Endpoint per la modifica di un costo esistente."""
    costo = Costo.query.get_or_404(costo_id)
    data = request.get_json()
    try:
        costo.descrizione = data.get('descrizione', costo.descrizione)
        costo.anno_riferimento = data.get('anno_riferimento', costo.anno_riferimento)
        costo.data_pagamento = parse_date(data.get('data_pagamento'), 'data_pagamento') if data.get('data_pagamento') else costo.data_pagamento
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


@costi_bp.route('/recurring-costs', methods=['GET'])
def get_recurring_costs():
    """Endpoint per ottenere le regole dei costi ricorrenti."""
    try:
        recurring_costs = CostoRicorrente.query.order_by(CostoRicorrente.descrizione.asc()).all()
        return jsonify([serialize_recurring_cost(c) for c in recurring_costs]), 200
    except Exception as e:
        return jsonify({"message": f"Errore durante il recupero dei costi ricorrenti: {str(e)}"}), 500


@costi_bp.route('/recurring-costs', methods=['POST'])
def add_recurring_cost():
    """Endpoint per creare una nuova regola di costo ricorrente."""
    data = request.get_json()
    try:
        ricorrenza = build_recurring_cost(data)
        db.session.add(ricorrenza)
        db.session.flush()
        generate_recurring_costs(commit=False)
        db.session.commit()
        return jsonify({
            "message": "Costo ricorrente aggiunto con successo!",
            "id": ricorrenza.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Errore durante l'aggiunta del costo ricorrente: {str(e)}"}), 500


@costi_bp.route('/recurring-costs/<int:ricorrenza_id>', methods=['GET'])
def get_single_recurring_cost(ricorrenza_id):
    """Endpoint per ottenere una singola regola di costo ricorrente."""
    ricorrenza = CostoRicorrente.query.get_or_404(ricorrenza_id)
    return jsonify(serialize_recurring_cost(ricorrenza)), 200


@costi_bp.route('/recurring-costs/<int:ricorrenza_id>', methods=['PUT'])
def update_recurring_cost(ricorrenza_id):
    """Endpoint per modificare una regola di costo ricorrente."""
    ricorrenza = CostoRicorrente.query.get_or_404(ricorrenza_id)
    data = request.get_json()
    try:
        if 'descrizione' in data:
            ricorrenza.descrizione = data['descrizione']
        if 'totale' in data:
            totale = float(data['totale'])
            if totale <= 0:
                raise ValueError("Il totale deve essere positivo")
            ricorrenza.totale = totale
        if 'frequenza' in data:
            if data['frequenza'] not in FREQUENZE_RICORRENZA:
                raise ValueError("Frequenza non valida")
            ricorrenza.frequenza = data['frequenza']
        if 'giorno_scadenza' in data:
            giorno_scadenza = int(data['giorno_scadenza'])
            if giorno_scadenza < 1 or giorno_scadenza > 31:
                raise ValueError("Il giorno di scadenza deve essere tra 1 e 31")
            ricorrenza.giorno_scadenza = giorno_scadenza
        if 'data_inizio' in data:
            ricorrenza.data_inizio = parse_date(data['data_inizio'], 'data_inizio')
        if 'data_fine' in data:
            ricorrenza.data_fine = parse_date(data['data_fine'], 'data_fine')
        if ricorrenza.data_fine and ricorrenza.data_fine < ricorrenza.data_inizio:
            raise ValueError("La data di fine non può precedere la data di inizio")
        if 'pagato_default' in data:
            ricorrenza.pagato_default = bool_from_payload(data, 'pagato_default', False)
        if 'attivo' in data:
            ricorrenza.attivo = bool_from_payload(data, 'attivo', True)

        db.session.flush()
        generate_recurring_costs(commit=False)
        db.session.commit()
        return jsonify({"message": "Costo ricorrente aggiornato con successo!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Errore durante l'aggiornamento del costo ricorrente: {str(e)}"}), 500


@costi_bp.route('/recurring-costs/<int:ricorrenza_id>', methods=['DELETE'])
def delete_recurring_cost(ricorrenza_id):
    """Endpoint per disattivare una regola di costo ricorrente."""
    ricorrenza = CostoRicorrente.query.get_or_404(ricorrenza_id)
    try:
        ricorrenza.attivo = False
        db.session.commit()
        return jsonify({"message": "Costo ricorrente disattivato con successo!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Errore durante la disattivazione del costo ricorrente: {str(e)}"}), 500
