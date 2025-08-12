from flask import Blueprint, render_template, request, jsonify, flash
import requests
import os

# Crea un Blueprint per le rotte dei clienti
cliente_bp = Blueprint('cliente_bp', __name__)

# Variabile d'ambiente per l'URL del backend
BACKEND_URL = os.getenv("BACKEND_URL", "http://invoice_backend:5000")

def handle_backend_response(response):
    """
    Gestisce la risposta del backend e estrae il messaggio di errore appropriato
    """
    try:
        # Prova a parsare il JSON dalla risposta
        response_data = response.json()
    except ValueError:
        # Se non è JSON valido, usa il testo della risposta
        response_data = {"message": response.text or "Errore sconosciuto"}
    
    return response_data, response.status_code

def get_error_message(response_data, default_message="Errore sconosciuto"):
    """
    Estrae il messaggio di errore dai dati di risposta del backend
    """
    if isinstance(response_data, dict):
        # Prova diversi campi comuni per i messaggi di errore
        for field in ['message', 'error', 'detail', 'msg', 'description']:
            if field in response_data and response_data[field]:
                return response_data[field]
    
    return default_message

# --- Proxy API per i clienti ---
@cliente_bp.route('/api/clients', methods=['POST'])
def add_client_proxy():
    data = request.get_json()
    
    try:
        response = requests.post(f"{BACKEND_URL}/api/clients", json=data, timeout=10)
        
        if response.ok:
            flash("Cliente aggiunto con successo!", 'success')
            response_data, status_code = handle_backend_response(response)
            return jsonify(response_data), status_code
        else:
            # Il backend ha restituito un errore, ma vogliamo il messaggio specifico
            response_data, status_code = handle_backend_response(response)
            error_message = get_error_message(response_data, "Errore durante l'aggiunta del cliente")
            
            flash(f"Errore: {error_message}", 'danger')
            return jsonify({'message': error_message}), status_code
            
    except requests.exceptions.Timeout:
        error_msg = "Timeout: Il server sta impiegando troppo tempo a rispondere"
        flash(error_msg, 'danger')
        return jsonify({'message': error_msg}), 408
    
    except requests.exceptions.ConnectionError:
        error_msg = "Errore di connessione: Impossibile raggiungere il server backend"
        flash(error_msg, 'danger')
        return jsonify({'message': error_msg}), 503
    
    except requests.exceptions.RequestException as e:
        error_msg = f"Errore di rete: {str(e)}"
        flash(error_msg, 'danger')
        return jsonify({'message': error_msg}), 500

@cliente_bp.route('/api/clients/<int:client_id>', methods=['GET'])
def get_client_proxy(client_id):
    try:
        response = requests.get(f"{BACKEND_URL}/api/clients/{client_id}", timeout=10)
        
        if response.ok:
            response_data, status_code = handle_backend_response(response)
            return jsonify(response_data), status_code
        else:
            response_data, status_code = handle_backend_response(response)
            error_message = get_error_message(response_data, "Cliente non trovato")
            return jsonify({'message': error_message}), status_code
            
    except requests.exceptions.Timeout:
        return jsonify({'message': "Timeout nel recupero del cliente"}), 408
    
    except requests.exceptions.ConnectionError:
        return jsonify({'message': "Errore di connessione al server"}), 503
    
    except requests.exceptions.RequestException as e:
        return jsonify({'message': f"Errore: {str(e)}"}), 500

@cliente_bp.route('/api/clients/<int:client_id>', methods=['PUT'])
def edit_client_proxy(client_id):
    data = request.get_json()
    
    try:
        response = requests.put(f"{BACKEND_URL}/api/clients/{client_id}", json=data, timeout=10)
        
        if response.ok:
            flash("Cliente aggiornato con successo!", 'success')
            response_data, status_code = handle_backend_response(response)
            return jsonify(response_data), status_code
        else:
            response_data, status_code = handle_backend_response(response)
            error_message = get_error_message(response_data, "Errore durante la modifica del cliente")
            
            flash(f"Errore: {error_message}", 'danger')
            return jsonify({'message': error_message}), status_code
            
    except requests.exceptions.Timeout:
        error_msg = "Timeout durante l'aggiornamento del cliente"
        flash(error_msg, 'danger')
        return jsonify({'message': error_msg}), 408
    
    except requests.exceptions.ConnectionError:
        error_msg = "Errore di connessione durante l'aggiornamento"
        flash(error_msg, 'danger')
        return jsonify({'message': error_msg}), 503
    
    except requests.exceptions.RequestException as e:
        error_msg = f"Errore durante l'aggiornamento: {str(e)}"
        flash(error_msg, 'danger')
        return jsonify({'message': error_msg}), 500

@cliente_bp.route('/api/clients/<int:client_id>', methods=['DELETE'])
def delete_client_proxy(client_id):
    try:
        response = requests.delete(f"{BACKEND_URL}/api/clients/{client_id}", timeout=10)
        
        if response.ok:
            flash("Cliente eliminato con successo!", 'success')
            response_data, status_code = handle_backend_response(response)
            return jsonify(response_data), status_code
        else:
            response_data, status_code = handle_backend_response(response)
            error_message = get_error_message(response_data, "Errore durante l'eliminazione del cliente")
            
            flash(f"Errore: {error_message}", 'danger')
            return jsonify({'message': error_message}), status_code
            
    except requests.exceptions.Timeout:
        error_msg = "Timeout durante l'eliminazione del cliente"
        flash(error_msg, 'danger')
        return jsonify({'message': error_msg}), 408
    
    except requests.exceptions.ConnectionError:
        error_msg = "Errore di connessione durante l'eliminazione"
        flash(error_msg, 'danger')
        return jsonify({'message': error_msg}), 503
    
    except requests.exceptions.RequestException as e:
        error_msg = f"Errore durante l'eliminazione: {str(e)}"
        flash(error_msg, 'danger')
        return jsonify({'message': error_msg}), 500