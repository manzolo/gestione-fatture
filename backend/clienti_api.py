from flask import Blueprint, request, jsonify
from .models import db, Cliente
from codicefiscale import isvalid

clients_bp = Blueprint('clients_bp', __name__)

@clients_bp.route('/clients', methods=['GET', 'POST'])
def clients_api():
    if request.method == 'POST':
        data = request.get_json()
        if not isvalid(data['codice_fiscale']):
            return jsonify({"message": "Codice fiscale errato."}), 400
        new_client = Cliente(
            nome=data['nome'],
            cognome=data['cognome'],
            codice_fiscale=data['codice_fiscale'],
            indirizzo=data.get('indirizzo'),
            citta=data.get('citta'),
            cap=data.get('cap')
        )
        db.session.add(new_client)
        db.session.commit()
        return jsonify({"message": "Cliente aggiunto con successo!", "id": new_client.id}), 201
    else: # GET
        clients = Cliente.query.all()
        clients_list = [{
            'id': c.id,
            'nome': c.nome,
            'cognome': c.cognome,
            'codice_fiscale': c.codice_fiscale,
            'indirizzo': c.indirizzo,
            'citta': c.citta,
            'cap': c.cap
        } for c in clients]
        return jsonify(clients_list)

@clients_bp.route('/clients/<int:client_id>', methods=['GET', 'PUT', 'DELETE'])
def client_api_detail(client_id):
    client = Cliente.query.get_or_404(client_id)

    if request.method == 'GET':
        return jsonify({
            'id': client.id,
            'nome': client.nome,
            'cognome': client.cognome,
            'codice_fiscale': client.codice_fiscale,
            'indirizzo': client.indirizzo,
            'citta': client.citta,
            'cap': client.cap
        })
    elif request.method == 'PUT':
        data = request.get_json()
        
        # Aggiunto il controllo di validità del Codice Fiscale
        if 'codice_fiscale' in data and not isvalid(data['codice_fiscale']):
            return jsonify({"message": "Codice fiscale errato."}), 400
        
        client.nome = data.get('nome', client.nome)
        client.cognome = data.get('cognome', client.cognome)
        client.codice_fiscale = data.get('codice_fiscale', client.codice_fiscale)
        client.indirizzo = data.get('indirizzo', client.indirizzo)
        client.citta = data.get('citta', client.citta)
        client.cap = data.get('cap', client.cap)
        db.session.commit()
        return jsonify({"message": "Cliente aggiornato con successo!"}), 200
    elif request.method == 'DELETE':
        if getattr(client, 'fatture', None) and len(client.fatture) > 0:
            return jsonify({'message': 'Impossibile eliminare un cliente con fatture associate.'}), 400
        db.session.delete(client)
        db.session.commit()
        return jsonify({"message": "Cliente eliminato con successo!"}), 200
