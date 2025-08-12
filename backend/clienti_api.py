from flask import Blueprint, request, jsonify
from .models import db, Cliente
from codicefiscale import isvalid
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
import re

clients_bp = Blueprint('clients_bp', __name__)

def extract_constraint_error(error_message):
    """
    Estrae informazioni specifiche dagli errori di constraint del database
    """
    # Pattern per errori di chiave duplicata PostgreSQL
    duplicate_key_pattern = r'duplicate key value violates unique constraint "([^"]+)"'
    detail_pattern = r'DETAIL:\s*Key \(([^)]+)\)=\(([^)]+)\) already exists'
    
    match_constraint = re.search(duplicate_key_pattern, str(error_message))
    match_detail = re.search(detail_pattern, str(error_message))
    
    if match_constraint and match_detail:
        constraint_name = match_constraint.group(1)
        field_name = match_detail.group(1)
        field_value = match_detail.group(2)
        
        # Messaggi specifici per diversi constraint
        if 'codice_fiscale' in constraint_name:
            return f"Codice Fiscale '{field_value}' già presente nel sistema. Utilizza un codice fiscale diverso."
        elif 'email' in constraint_name:
            return f"Email '{field_value}' già utilizzata da un altro cliente."
        else:
            return f"Il valore inserito per il campo '{field_name}' è già presente nel sistema."
    
    return "Errore: dati duplicati nel sistema."

def handle_database_error(error):
    """
    Gestisce gli errori del database e restituisce messaggi user-friendly
    """
    if isinstance(error, IntegrityError):
        if 'UniqueViolation' in str(error.orig):
            return extract_constraint_error(str(error.orig)), 409
        elif 'NotNullViolation' in str(error.orig):
            # Estrae il nome del campo null
            null_field_pattern = r'null value in column "([^"]+)" violates not-null constraint'
            match = re.search(null_field_pattern, str(error.orig))
            if match:
                field_name = match.group(1)
                return f"Il campo '{field_name}' è obbligatorio.", 400
            return "Campi obbligatori mancanti.", 400
        elif 'ForeignKeyViolation' in str(error.orig):
            return "Riferimento non valido. Controlla i dati inseriti.", 400
        else:
            return "Errore di integrità dei dati.", 400
    
    return "Errore del database.", 500

@clients_bp.route('/clients', methods=['GET', 'POST'])
def clients_api():
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # Validazione dati di input
            if not data:
                return jsonify({"message": "Nessun dato fornito."}), 400
            
            # Campi obbligatori
            required_fields = ['nome', 'cognome', 'codice_fiscale']
            missing_fields = [field for field in required_fields if not data.get(field, '').strip()]
            
            if missing_fields:
                return jsonify({
                    "message": f"Campi obbligatori mancanti: {', '.join(missing_fields)}."
                }), 400
            
            # Validazione codice fiscale
            codice_fiscale = data['codice_fiscale'].strip().upper()
            if not isvalid(codice_fiscale):
                return jsonify({
                    "message": "Il Codice Fiscale inserito non è valido. Controlla il formato."
                }), 400
            
            # Controllo preventivo duplicati codice fiscale
            existing_client = Cliente.query.filter_by(codice_fiscale=codice_fiscale).first()
            if existing_client:
                return jsonify({
                    "message": f"Un cliente con Codice Fiscale '{codice_fiscale}' è già presente nel sistema."
                }), 409
            
            # Validazione lunghezza campi
            if len(data['nome'].strip()) > 100:
                return jsonify({"message": "Il nome non può superare i 100 caratteri."}), 400
            
            if len(data['cognome'].strip()) > 100:
                return jsonify({"message": "Il cognome non può superare i 100 caratteri."}), 400
            
            # Validazione CAP se presente
            cap = data.get('cap', '').strip()
            if cap and not re.match(r'^\d{5}$', cap):
                return jsonify({"message": "Il CAP deve essere composto da 5 cifre."}), 400
            
            # Creazione nuovo cliente
            new_client = Cliente(
                nome=data['nome'].strip(),
                cognome=data['cognome'].strip(),
                codice_fiscale=codice_fiscale,
                indirizzo=data.get('indirizzo', '').strip() or None,
                citta=data.get('citta', '').strip() or None,
                cap=cap or None
            )
            
            db.session.add(new_client)
            db.session.commit()
            
            return jsonify({
                "message": f"Cliente {new_client.nome} {new_client.cognome} aggiunto con successo!",
                "id": new_client.id
            }), 201
            
        except IntegrityError as e:
            db.session.rollback()
            error_message, status_code = handle_database_error(e)
            return jsonify({"message": error_message}), status_code
        
        except Exception as e:
            db.session.rollback()
            print(f"Errore imprevisto durante l'aggiunta del cliente: {str(e)}")
            return jsonify({
                "message": "Si è verificato un errore imprevisto. Riprova più tardi."
            }), 500
    
    else:  # GET
        try:
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
        except Exception as e:
            print(f"Errore durante il recupero dei clienti: {str(e)}")
            return jsonify({"message": "Errore durante il recupero dei clienti."}), 500

@clients_bp.route('/clients/<int:client_id>', methods=['GET', 'PUT', 'DELETE'])
def client_api_detail(client_id):
    try:
        client = Cliente.query.get(client_id)
        if not client:
            return jsonify({"message": "Cliente non trovato."}), 404
        
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
            try:
                data = request.get_json()
                
                if not data:
                    return jsonify({"message": "Nessun dato fornito per l'aggiornamento."}), 400
                
                # Validazione campi obbligatori se forniti
                if 'nome' in data and not data['nome'].strip():
                    return jsonify({"message": "Il nome non può essere vuoto."}), 400
                
                if 'cognome' in data and not data['cognome'].strip():
                    return jsonify({"message": "Il cognome non può essere vuoto."}), 400
                
                # Validazione codice fiscale se fornito
                if 'codice_fiscale' in data:
                    codice_fiscale = data['codice_fiscale'].strip().upper()
                    if not isvalid(codice_fiscale):
                        return jsonify({
                            "message": "Il Codice Fiscale inserito non è valido. Controlla il formato."
                        }), 400
                    
                    # Controllo duplicati solo se il codice fiscale è diverso da quello attuale
                    if codice_fiscale != client.codice_fiscale:
                        existing_client = Cliente.query.filter_by(codice_fiscale=codice_fiscale).first()
                        if existing_client:
                            return jsonify({
                                "message": f"Un altro cliente con Codice Fiscale '{codice_fiscale}' è già presente nel sistema."
                            }), 409
                
                # Validazione CAP se presente
                if 'cap' in data:
                    cap = data['cap'].strip()
                    if cap and not re.match(r'^\d{5}$', cap):
                        return jsonify({"message": "Il CAP deve essere composto da 5 cifre."}), 400
                
                # Aggiornamento campi
                if 'nome' in data:
                    client.nome = data['nome'].strip()
                if 'cognome' in data:
                    client.cognome = data['cognome'].strip()
                if 'codice_fiscale' in data:
                    client.codice_fiscale = data['codice_fiscale'].strip().upper()
                if 'indirizzo' in data:
                    client.indirizzo = data['indirizzo'].strip() or None
                if 'citta' in data:
                    client.citta = data['citta'].strip() or None
                if 'cap' in data:
                    client.cap = data['cap'].strip() or None
                
                db.session.commit()
                
                return jsonify({
                    "message": f"Cliente {client.nome} {client.cognome} aggiornato con successo!"
                }), 200
                
            except IntegrityError as e:
                db.session.rollback()
                error_message, status_code = handle_database_error(e)
                return jsonify({"message": error_message}), status_code
            
            except Exception as e:
                db.session.rollback()
                print(f"Errore durante l'aggiornamento del cliente {client_id}: {str(e)}")
                return jsonify({
                    "message": "Si è verificato un errore durante l'aggiornamento. Riprova più tardi."
                }), 500
        
        elif request.method == 'DELETE':
            try:
                # Controllo se il cliente ha fatture associate
                if hasattr(client, 'fatture') and client.fatture:
                    fatture_count = len(client.fatture)
                    return jsonify({
                        'message': f'Impossibile eliminare il cliente: ha {fatture_count} fattur{"a" if fatture_count == 1 else "e"} associat{"a" if fatture_count == 1 else "e"}.'
                    }), 400
                
                client_name = f"{client.nome} {client.cognome}"
                db.session.delete(client)
                db.session.commit()
                
                return jsonify({
                    "message": f"Cliente {client_name} eliminato con successo!"
                }), 200
                
            except Exception as e:
                db.session.rollback()
                print(f"Errore durante l'eliminazione del cliente {client_id}: {str(e)}")
                return jsonify({
                    "message": "Si è verificato un errore durante l'eliminazione. Riprova più tardi."
                }), 500
    
    except Exception as e:
        print(f"Errore generale nell'API cliente {client_id}: {str(e)}")
        return jsonify({"message": "Si è verificato un errore imprevisto."}), 500