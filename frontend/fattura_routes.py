from flask import Blueprint, render_template, request, jsonify, flash, send_file, redirect, url_for
import requests
import os
from datetime import datetime
from io import BytesIO

# Crea un Blueprint per le rotte delle fatture
fattura_bp = Blueprint('fattura_bp', __name__)

# Variabile d'ambiente per l'URL del backend
BACKEND_URL = os.getenv("BACKEND_URL", "http://invoice_backend:5000")

@fattura_bp.route('/')
def fatture():
    """Rotta per la gestione delle fatture e la dashboard."""
    try:
        clients_response = requests.get(f"{BACKEND_URL}/api/clients")
        clients_response.raise_for_status()
        clients = clients_response.json()

        invoices_response = requests.get(f"{BACKEND_URL}/api/invoices")
        invoices_response.raise_for_status()
        invoices = invoices_response.json()
    except requests.exceptions.RequestException as e:
        flash(f"Errore di connessione al backend: {e}", 'danger')
        clients = []
        invoices = []

    return render_template('index.html', clients=clients, invoices=invoices, now=datetime.now())

# --- Proxy API per le fatture e le statistiche ---
@fattura_bp.route('/api/invoices', methods=['POST'])
def add_invoice_proxy():
    """Proxy per la creazione di una nuova fattura."""
    data = request.get_json()
    try:
        response = requests.post(f"{BACKEND_URL}/api/invoices", json=data)
        response.raise_for_status()
        flash("Fattura aggiunta con successo!", 'success')
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        flash(f"Errore durante l'aggiunta: {e}", 'danger')
        return jsonify({'message': f"Errore: {e}"}), 500

@fattura_bp.route('/api/invoices/<int:invoice_id>', methods=['GET'])
def get_invoice_proxy(invoice_id):
    """Proxy per ottenere i dati di una singola fattura."""
    try:
        response = requests.get(f"{BACKEND_URL}/api/invoices/{invoice_id}")
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'message': f"Errore: {e}"}), 500

@fattura_bp.route('/api/invoices/<int:invoice_id>', methods=['PUT'])
def edit_invoice_proxy(invoice_id):
    """Proxy per la modifica di una fattura."""
    data = request.get_json()
    try:
        response = requests.put(f"{BACKEND_URL}/api/invoices/{invoice_id}", json=data)
        response.raise_for_status()
        
        flash("Fattura aggiornata con successo!", 'success')
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        flash(f"Errore durante la modifica: {e}", 'danger')
        return jsonify({'message': f"Errore: {e}"}), 500

@fattura_bp.route('/download_invoice_zip/<int:invoice_id>')
def download_invoice_zip(invoice_id):
    """Rotta per scaricare un file ZIP di fattura, proxato dal backend."""
    try:
        response = requests.get(f"{BACKEND_URL}/api/invoices/{invoice_id}/download")
        response.raise_for_status()

        # Leggi il contenuto come un oggetto BytesIO
        file_object = BytesIO(response.content)

        # Restituisci il file ZIP con il mimetype corretto
        return send_file(
            file_object,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"fattura_{invoice_id}.zip"
        )
    except requests.exceptions.RequestException as e:
        flash(f"Errore durante il download: {e}", 'danger')
        return redirect(url_for('fattura_bp.fatture'))
    
@fattura_bp.route('/api/invoices/years', methods=['GET'])
def get_invoices_years_proxy():
    """Proxy per ottenere gli anni disponibili delle fatture dal backend."""
    try:
        response = requests.get(f"{BACKEND_URL}/api/invoices/years")
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'message': f"Errore nella richiesta al backend: {e}"}), 500

@fattura_bp.route('/api/invoices/stats', methods=['GET'])
def get_invoices_stats_proxy():
    """Proxy per ottenere le statistiche delle fatture dal backend (con supporto per parametro year)."""
    try:
        year_param = request.args.get('year')
        backend_url = f"{BACKEND_URL}/api/invoices/stats"
        
        params = {}
        if year_param:
            params['year'] = year_param
            
        response = requests.get(backend_url, params=params)
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'message': f"Errore nella richiesta al backend: {e}"}), 500