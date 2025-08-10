from flask import Blueprint, render_template, request, jsonify, flash
import requests
import os

# Crea un Blueprint per le rotte dei clienti
cliente_bp = Blueprint('cliente_bp', __name__)

# Variabile d'ambiente per l'URL del backend
BACKEND_URL = os.getenv("BACKEND_URL", "http://invoice_backend:5000")

@cliente_bp.route('/clienti')
def clienti():
    """Rotta per la gestione dei clienti."""
    try:
        clients_response = requests.get(f"{BACKEND_URL}/api/clients")
        clients_response.raise_for_status()
        clients = clients_response.json()
    except requests.exceptions.RequestException as e:
        flash(f"Errore di connessione al backend: {e}", 'danger')
        clients = []

    return render_template('clienti.html', clients=clients)

# --- Proxy API per i clienti ---
@cliente_bp.route('/api/clients', methods=['POST'])
def add_client_proxy():
    data = request.get_json()
    try:
        response = requests.post(f"{BACKEND_URL}/api/clients", json=data)
        response.raise_for_status()
        flash("Cliente aggiunto con successo!", 'success')
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        flash(f"Errore durante l'aggiunta del cliente: {e}", 'danger')
        return jsonify({'message': f"Errore: {e}"}), 500

@cliente_bp.route('/api/clients/<int:client_id>', methods=['GET'])
def get_client_proxy(client_id):
    try:
        response = requests.get(f"{BACKEND_URL}/api/clients/{client_id}")
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'message': f"Errore: {e}"}), 500

@cliente_bp.route('/api/clients/<int:client_id>', methods=['PUT'])
def edit_client_proxy(client_id):
    data = request.get_json()
    try:
        response = requests.put(f"{BACKEND_URL}/api/clients/{client_id}", json=data)
        response.raise_for_status()
        flash("Cliente aggiornato con successo!", 'success')
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        flash(f"Errore durante la modifica del cliente: {e}", 'danger')
        return jsonify({'message': f"Errore: {e}"}), 500

@cliente_bp.route('/api/clients/<int:client_id>', methods=['DELETE'])
def delete_client_proxy(client_id):
    try:
        response = requests.delete(f"{BACKEND_URL}/api/clients/{client_id}")
        response.raise_for_status()
        flash("Cliente eliminato con successo!", 'success')
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        flash(f"Errore durante l'eliminazione del cliente: {e}", 'danger')
        return jsonify({'message': f"Errore: {e}"}), 500