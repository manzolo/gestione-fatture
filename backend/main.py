from flask import Flask, request, jsonify, send_file
from .models import db, Cliente, Fattura, FatturaProgressivo
from datetime import datetime
import os
from docx import Document
from docxtpl import DocxTemplate
from sqlalchemy import text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_SQLALCHEMY_URL')
db.init_app(app)

# Creazione della directory temporanea se non esiste
temp_dir = os.path.join(app.root_path, 'temp')
if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)

# --- Voci e parametri predefiniti ---
DEFAULT_PRESTAZIONE_COSTO = 58.82
CONTRIBUTO_PERCENTAGE = 0.02
BOLLO_COSTO = 2.0
BOLLO_SOGLIA = 70.00
METODI_PAGAMENTO = ["Carta di credito/debito", "Bonifico", "Contanti"]

# --- API Clients ---
@app.route('/api/clients', methods=['GET'])
def get_clients():
    clients = Cliente.query.all()
    clients_list = [{
        'id': c.id,
        'nome': c.nome,
        'cognome': c.cognome,
        'codice_fiscale': c.codice_fiscale,
        'indirizzo': c.indirizzo
    } for c in clients]
    return jsonify(clients_list)

@app.route('/api/clients', methods=['POST'])
def add_client():
    data = request.get_json()
    new_client = Cliente(
        nome=data['nome'],
        cognome=data['cognome'],
        codice_fiscale=data['codice_fiscale'],
        indirizzo=data.get('indirizzo')
    )
    db.session.add(new_client)
    db.session.commit()
    return jsonify({'message': 'Cliente aggiunto con successo!'}), 201

@app.route('/api/clients/<int:client_id>', methods=['PUT'])
def edit_client(client_id):
    client = Cliente.query.get_or_404(client_id)
    data = request.get_json()
    client.nome = data['nome']
    client.cognome = data['cognome']
    client.codice_fiscale = data['codice_fiscale']
    client.indirizzo = data.get('indirizzo')
    db.session.commit()
    return jsonify({'message': 'Cliente aggiornato con successo!'})

@app.route('/api/clients/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    client = Cliente.query.get_or_404(client_id)
    if client.fatture:
        return jsonify({'message': 'Impossibile eliminare un cliente con fatture associate.'}), 400
    db.session.delete(client)
    db.session.commit()
    return jsonify({'message': 'Cliente eliminato con successo!'})

@app.route('/api/invoices', methods=['GET'])
def get_invoices():
    invoices = Fattura.query.order_by(Fattura.anno.desc(), Fattura.progressivo.desc()).all()
    invoices_list = [{
        'id': i.id,
        'numero_fattura': f"{i.progressivo}/{i.anno}",
        'data_fattura': i.data_fattura.strftime('%Y-%m-%d'),
        'data_pagamento': i.data_pagamento.strftime('%Y-%m-%d') if i.data_pagamento else None,
        'metodo_pagamento': i.metodo_pagamento,
        'cliente': f"{i.cliente.nome} {i.cliente.cognome}",
        'descrizione': i.descrizione,
        'totale': f"{i.totale:.2f}"
    } for i in invoices]
    return jsonify(invoices_list)

@app.route('/api/invoices', methods=['POST'])
def add_invoice():
    data = request.get_json()
    
    current_year = datetime.now().year
    
    # Recupera il prossimo numero progressivo per l'anno corrente
    progressivo_entry = FatturaProgressivo.query.filter_by(anno=current_year).first()
    if not progressivo_entry:
        progressivo_entry = FatturaProgressivo(anno=current_year, last_progressivo=0)
        db.session.add(progressivo_entry)
        db.session.commit()
    
    progressivo = progressivo_entry.last_progressivo + 1
    
    # Prepara i dati della fattura
    importo_prestazione_unitario = data['importo_prestazione']
    numero_sedute = data['numero_sedute']

    # --- LOGICA DI CALCOLO AGGIORNATA ---
    # Calcolo del subtotale basato sul numero di sedute
    subtotale_prestazioni = importo_prestazione_unitario * numero_sedute
    
    # Calcolo del contributo previdenziale sul subtotale
    contributo = subtotale_prestazioni * CONTRIBUTO_PERCENTAGE
    
    # Totale senza bollo
    totale_senza_bollo = subtotale_prestazioni + contributo
    
    # Calcolo del bollo
    bollo_flag = totale_senza_bollo >= BOLLO_SOGLIA
    
    # Calcolo del totale finale
    totale = totale_senza_bollo + (BOLLO_COSTO if bollo_flag else 0)
    # --- FINE LOGICA AGGIORNATA ---
    
    descrizione = f"n. {numero_sedute} di Seduta di consulenza psicologica"
    
    nuova_fattura = Fattura(
        anno=current_year,
        progressivo=progressivo,
        data_fattura=datetime.strptime(data['data_fattura'], '%Y-%m-%d').date(),
        data_pagamento=datetime.strptime(data['data_pagamento'], '%Y-%m-%d').date() if data.get('data_pagamento') else None,
        metodo_pagamento=data.get('metodo_pagamento'),
        cliente_id=data['cliente_id'],
        importo_prestazione=importo_prestazione_unitario,
        bollo=bollo_flag,
        descrizione=descrizione,
        totale=totale,
        numero_sedute=numero_sedute
    )
    
    db.session.add(nuova_fattura)
    
    # Aggiorna il numero progressivo
    progressivo_entry.last_progressivo = progressivo
    db.session.commit()
    
    return jsonify({'message': 'Fattura aggiunta con successo!', 'id': nuova_fattura.id}), 201

@app.route('/api/invoices/<int:invoice_id>/download', methods=['GET'])
def download_invoice_docx(invoice_id):
    try:
        fattura = Fattura.query.get_or_404(invoice_id)
        cliente = Cliente.query.get_or_404(fattura.cliente_id)

        # Assicurati che il file template esista e sia nella cartella corretta
        template_path = os.path.join(app.root_path, 'templates', 'invoice_template.docx')
        if not os.path.exists(template_path):
            return jsonify({"error": "Template file not found"}), 404
        
        doc = DocxTemplate(template_path)

        # Dati da passare al template
        context = {
            'numero_fattura': f"{fattura.progressivo}/{fattura.anno}",
            'data_fattura': fattura.data_fattura.strftime('%d/%m/%Y'),
            'cliente_nome': cliente.nome,
            'cliente_cognome': cliente.cognome,
            'cliente_codice_fiscale': cliente.codice_fiscale,
            'cliente_indirizzo': cliente.indirizzo,
            'descrizione': fattura.descrizione,
            'totale': f"€{fattura.totale:.2f}",
            'metodo_pagamento': fattura.metodo_pagamento,
            'data_pagamento': fattura.data_pagamento.strftime('%d/%m/%Y') if fattura.data_pagamento else 'Non pagato',
        }
        
        doc.render(context)
        
        # Salvataggio temporaneo del file nella directory 'temp'
        file_path = os.path.join(temp_dir, f"fattura_{fattura.id}.docx")
        doc.save(file_path)
        
        # Invio del file al frontend e eliminazione del file temporaneo
        return_data = send_file(file_path, as_attachment=True)
        #os.remove(file_path)  # Elimina il file dopo l'invio
        
        return return_data

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint di health check (rimane invariato)
@app.route('/health')
def health_check():
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({"status": "healthy"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500