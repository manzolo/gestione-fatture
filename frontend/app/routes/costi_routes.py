from flask import Blueprint, request, jsonify, flash, render_template
import requests
import os
from collections import defaultdict

# Crea un Blueprint per le rotte dei costi
costi_bp = Blueprint('costi_bp', __name__)

# Variabile d'ambiente per l'URL del backend
BACKEND_URL = os.getenv("BACKEND_URL", "http://invoice_backend:5000")

# --- Proxy API per i costi ---
@costi_bp.route('/api/costs', methods=['POST'])
def add_costo_proxy():
    """Proxy per la creazione di un nuovo costo."""
    data = request.get_json()
    try:
        response = requests.post(f"{BACKEND_URL}/api/costs", json=data)
        response.raise_for_status()
        flash("Costo aggiunto con successo!", 'success')
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        flash(f"Errore durante l'aggiunta del costo: {e}", 'danger')
        return jsonify({'message': f"Errore: {e}"}), 500

@costi_bp.route('/api/costs', methods=['GET'])
def get_costs_proxy():
    """Proxy per ottenere la lista dei costi."""
    try:
        response = requests.get(f"{BACKEND_URL}/api/costs")
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        flash(f"Errore durante il recupero dei costi: {e}", 'danger')
        return jsonify({'message': f"Errore: {e}"}), 500
        
@costi_bp.route('/api/costs/<int:costo_id>', methods=['GET'])
def get_costo_by_id_proxy(costo_id):
    """Proxy per ottenere un singolo costo per ID."""
    try:
        response = requests.get(f"{BACKEND_URL}/api/costs/{costo_id}")
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        flash(f"Errore durante il recupero del costo: {e}", 'danger')
        return jsonify({'message': f"Errore: {e}"}), 500

@costi_bp.route('/api/costs/<int:costo_id>', methods=['PUT'])
def edit_costo_proxy(costo_id):
    """Proxy per la modifica di un costo."""
    data = request.get_json()
    try:
        response = requests.put(f"{BACKEND_URL}/api/costs/{costo_id}", json=data)
        response.raise_for_status()
        flash("Costo aggiornato con successo!", 'success')
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        flash(f"Errore durante la modifica del costo: {e}", 'danger')
        return jsonify({'message': f"Errore: {e}"}), 500

@costi_bp.route('/api/costs/<int:costo_id>', methods=['DELETE'])
def delete_costo_proxy(costo_id):
    """Proxy per l'eliminazione di un costo."""
    try:
        response = requests.delete(f"{BACKEND_URL}/api/costs/{costo_id}")
        response.raise_for_status()
        flash("Costo eliminato con successo!", 'success')
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        flash(f"Errore durante l'eliminazione del costo: {e}", 'danger')
        return jsonify({'message': f"Errore: {e}"}), 500

@costi_bp.route('/api/costs/stats', methods=['GET'])
def get_costs_stats_proxy():
    """Proxy per ottenere le statistiche dei costi."""
    try:
        # Passa l'anno selezionato se presente, altrimenti ottieni le statistiche generali
        year = request.args.get('year')
        params = {'year': year} if year else {}
        response = requests.get(f"{BACKEND_URL}/api/costs/stats", params=params)
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        flash(f"Errore durante il recupero delle statistiche dei costi: {e}", 'danger')
        return jsonify({'message': f"Errore: {e}"}), 500