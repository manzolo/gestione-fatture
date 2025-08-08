from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import requests
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'una-chiave-segreta-molto-complessa'
BACKEND_URL = os.getenv("BACKEND_URL", "http://invoice_backend:8900")

@app.route('/')
def home():
    """Rotta principale che reindirizza alla pagina dei clienti."""
    return redirect(url_for('clienti'))

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

@app.route('/add_client', methods=['POST'])
def add_client():
    """Rotta per aggiungere un nuovo cliente."""
    data = {
        'nome': request.form['nome'],
        'cognome': request.form['cognome'],
        'codice_fiscale': request.form['codice_fiscale'],
        'indirizzo': request.form['indirizzo']
    }
    try:
        response = requests.post(f"{BACKEND_URL}/api/clients", json=data)
        response.raise_for_status()
        flash("Cliente aggiunto con successo!", 'success')
    except requests.exceptions.RequestException as e:
        flash(f"Errore durante l'aggiunta del cliente: {e}", 'danger')
    
    return redirect(url_for('clienti'))

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

@app.route('/add_invoice', methods=['POST'])
def add_invoice():
    """Rotta per aggiungere una nuova fattura."""
    data = {
        'cliente_id': request.form['cliente_id'],
        'data_fattura': request.form['data_fattura'],
        'data_pagamento': request.form.get('data_pagamento'),
        'metodo_pagamento': request.form.get('metodo_pagamento'),
        'importo_prestazione': float(request.form['importo_prestazione']),
        'numero_sedute': int(request.form['numero_sedute'])
    }
    try:
        response = requests.post(f"{BACKEND_URL}/api/invoices", json=data)
        response.raise_for_status()
        flash("Fattura aggiunta con successo!", 'success')
    except requests.exceptions.RequestException as e:
        flash(f"Errore durante l'aggiunta della fattura: {e}", 'danger')
        
    return redirect(url_for('fatture'))

@app.route('/download_invoice/<int:invoice_id>')
def download_invoice(invoice_id):
    """Rotta per scaricare un file DOCX di fattura."""
    try:
        response = requests.get(f"{BACKEND_URL}/api/invoices/{invoice_id}/download")
        response.raise_for_status()
        
        filename = f"fattura_{invoice_id}.docx"
        with open(filename, 'wb') as f:
            f.write(response.content)
            
        return send_file(filename, as_attachment=True)
    except requests.exceptions.RequestException as e:
        flash(f"Errore durante il download: {e}", 'danger')
        return redirect(url_for('fatture'))