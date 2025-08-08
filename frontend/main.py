from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
import requests
import os
from datetime import datetime
from io import BytesIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'una-chiave-segreta-molto-complessa'

# Correggi l'URL del backend per usare la porta interna 5000
BACKEND_URL = os.getenv("BACKEND_URL", "http://invoice_backend:5000")

# Filtro personalizzato per formattare le date
def format_date_italian(value):
    if value is None:
        return None
    try:
        date_obj = datetime.strptime(value, '%Y-%m-%d')
        return date_obj.strftime('%d/%m/%Y')
    except (ValueError, TypeError):
        return value

app.jinja_env.filters['to_italian_date'] = format_date_italian


@app.route('/')
def home():
    return redirect(url_for('fatture'))

@app.route('/clienti')
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

@app.route('/fatture')
def fatture():
    """Rotta per la gestione delle fatture."""
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

    return render_template('fatture.html', clients=clients, invoices=invoices, now=datetime.now())

# --- Proxy API per i clienti (aggiunte) ---
@app.route('/api/clients', methods=['POST'])
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

@app.route('/api/clients/<int:client_id>', methods=['GET'])
def get_client_proxy(client_id):
    try:
        response = requests.get(f"{BACKEND_URL}/api/clients/{client_id}")
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'message': f"Errore: {e}"}), 500

@app.route('/api/clients/<int:client_id>', methods=['PUT'])
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

@app.route('/api/clients/<int:client_id>', methods=['DELETE'])
def delete_client_proxy(client_id):
    try:
        response = requests.delete(f"{BACKEND_URL}/api/clients/{client_id}")
        response.raise_for_status()
        flash("Cliente eliminato con successo!", 'success')
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        flash(f"Errore durante l'eliminazione del cliente: {e}", 'danger')
        return jsonify({'message': f"Errore: {e}"}), 500


# --- Proxy API per le fatture ---
@app.route('/api/invoices', methods=['POST'])
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

@app.route('/api/invoices/<int:invoice_id>', methods=['GET'])
def get_invoice_proxy(invoice_id):
    """Proxy per ottenere i dati di una singola fattura."""
    try:
        response = requests.get(f"{BACKEND_URL}/api/invoices/{invoice_id}")
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'message': f"Errore: {e}"}), 500

@app.route('/api/invoices/<int:invoice_id>', methods=['PUT'])
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

@app.route('/download_invoice/<int:invoice_id>')
def download_invoice(invoice_id):
    """
    Rotta per scaricare un file DOCX di fattura, proxato dal backend.
    """
    try:
        response = requests.get(f"{BACKEND_URL}/api/invoices/{invoice_id}/download")
        response.raise_for_status()

        file_object = BytesIO(response.content)

        return send_file(
            file_object,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=f"fattura_{invoice_id}.docx"
        )
    except requests.exceptions.RequestException as e:
        flash(f"Errore durante il download: {e}", 'danger')
        return redirect(url_for('fatture'))