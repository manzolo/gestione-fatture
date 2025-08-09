from flask import Flask, request, jsonify, send_file, Response
from .models import db, Cliente, Fattura, FatturaProgressivo
from datetime import datetime
import os
import json
from docx import Document
from docxtpl import DocxTemplate
from sqlalchemy import text
from collections import defaultdict
from itertools import groupby
from operator import itemgetter

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_SQLALCHEMY_URL') or 'sqlite:///test.db'
db.init_app(app)

# Creazione delle directory se non esistono
temp_dir = os.path.join(app.root_path, 'temp')
if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)
    
invoices_dir = os.path.join(app.root_path, 'invoices')
if not os.path.exists(invoices_dir):
    os.makedirs(invoices_dir)

# --- Voci e parametri predefiniti ---
METODI_PAGAMENTO = ["Carta di credito/debito", "Bonifico", "Contanti"]
# Parametri fissi
PRESTAZIONE_BASE = 58.82     # Prezzo base senza contributo
CONTRIBUTO_FISSO_PER_SEDUTA = 1.18 # Contributo fisso per ogni seduta
BOLLO_COSTO = 2.00
BOLLO_SOGLIA = 70.00

def calculate_invoice_totals(numero_sedute: int):
    """
    Calcola i totali usando la logica desiderata.
    """
    if numero_sedute < 0:
        numero_sedute = 0

    # Calcolo dei valori per singola seduta
    prezzo_base_unitario = PRESTAZIONE_BASE
    contributo_unitario = CONTRIBUTO_FISSO_PER_SEDUTA
    totale_unitario = round(prezzo_base_unitario + contributo_unitario, 2)

    # Calcolo dei totali
    subtotale_base = round(prezzo_base_unitario * numero_sedute, 2)
    contributo = round(contributo_unitario * numero_sedute, 2)
    totale_imponibile = round(subtotale_base + contributo, 2)

    # Bollo: si applica se il totale imponibile supera la soglia
    bollo_flag = totale_imponibile > BOLLO_SOGLIA
    bollo_importo = BOLLO_COSTO if bollo_flag else 0.0

    # Totale finale
    totale = round(totale_imponibile + bollo_importo, 2)

    return {
        'numero_sedute': numero_sedute,
        'importo_unitario': prezzo_base_unitario,
        'contributo_unitario': contributo_unitario,
        'totale_unitario': totale_unitario,
        'subtotale_base': subtotale_base,
        'contributo': contributo,
        'bollo_flag': bollo_flag,
        'bollo_importo': bollo_importo,
        'totale_imponibile': totale_imponibile,
        'totale': totale
    }

# --- API Clients ---
@app.route('/api/clients', methods=['GET', 'POST'])
def clients_api():
    if request.method == 'POST':
        data = request.get_json()
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

@app.route('/api/clients/<int:client_id>', methods=['GET', 'PUT', 'DELETE'])
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

# --- API Invoices ---
@app.route('/api/invoices', methods=['GET', 'POST'])
def invoices_api():
    if request.method == 'POST':
        data = request.get_json()
        current_year = datetime.now().year
        
        progressivo_entry = FatturaProgressivo.query.filter_by(anno=current_year).first()
        if not progressivo_entry:
            progressivo_entry = FatturaProgressivo(anno=current_year, last_progressivo=0)
            db.session.add(progressivo_entry)
            db.session.commit()
        
        progressivo = progressivo_entry.last_progressivo + 1
        
        numero_sedute = int(data.get('numero_sedute', 1))
        calcoli = calculate_invoice_totals(numero_sedute)
        
        descrizione = f"n. {numero_sedute} di Sedut{'e' if numero_sedute > 1 else 'a'} di consulenza psicologica"
        
        # Converte il valore del checkbox in un booleano per il database
        inviata_sns_value = data.get('inviata_sns')
        inviata_sns_bool = True if inviata_sns_value == 'on' else False

        nuova_fattura = Fattura(
            anno=current_year,
            progressivo=progressivo,
            data_fattura=datetime.strptime(data['data_fattura'], '%Y-%m-%d').date(),
            data_pagamento=datetime.strptime(data['data_pagamento'], '%Y-%m-%d').date() if data.get('data_pagamento') else None,
            metodo_pagamento=data.get('metodo_pagamento'),
            cliente_id=data['cliente_id'],
            importo_prestazione=PRESTAZIONE_BASE,
            bollo=calcoli['bollo_flag'],
            descrizione=descrizione,
            totale=calcoli['totale'],
            numero_sedute=numero_sedute,
            inviata_sns=inviata_sns_bool # Usa il valore booleano convertito
        )
        
        db.session.add(nuova_fattura)
        progressivo_entry.last_progressivo = progressivo
        db.session.commit()
        
        return jsonify({'message': 'Fattura aggiunta con successo!', 'id': nuova_fattura.id}), 201
    else:  
        # GET
                # Recupera tutte le fatture e le ordina per anno in modo decrescente
        invoices = Fattura.query.order_by(Fattura.anno.desc(), Fattura.progressivo.desc()).all()
        
        grouped_invoices = defaultdict(list)
        for i in invoices:
            grouped_invoices[i.anno].append({
                'id': i.id,
                'numero_fattura': f"{i.progressivo}/{i.anno}",
                'data_fattura': i.data_fattura.strftime('%Y-%m-%d'),
                'data_pagamento': i.data_pagamento.strftime('%Y-%m-%d') if i.data_pagamento else None,
                'metodo_pagamento': i.metodo_pagamento,
                'cliente': f"{i.cliente.nome} {i.cliente.cognome}" if i.cliente else None,
                'descrizione': i.descrizione,
                'totale': f"{i.totale:.2f}",
                'inviata_sns': i.inviata_sns
            })

        # Ordina le chiavi (gli anni) in ordine decrescente
        sorted_years = sorted(grouped_invoices.keys(), reverse=True)
        
        # Crea un nuovo dizionario che manterrà l'ordine
        sorted_grouped_invoices = {year: grouped_invoices[year] for year in sorted_years}

        # Serializza manualmente il dizionario in JSON per preservare l'ordine
        json_output = json.dumps(sorted_grouped_invoices)
        
        # Restituisce la risposta con il contenuto e l'intestazione corretta
        return Response(json_output, mimetype='application/json')

@app.route('/api/invoices/<int:invoice_id>', methods=['GET', 'PUT'])
def invoice_api_detail(invoice_id):
    fattura = Fattura.query.get_or_404(invoice_id)
    
    if request.method == 'GET':
        calcoli = calculate_invoice_totals(fattura.numero_sedute)
        return jsonify({
            'id': fattura.id,
            'numero_fattura': f"{fattura.progressivo}/{fattura.anno}",
            'data_fattura': fattura.data_fattura.strftime('%Y-%m-%d'),
            'data_pagamento': fattura.data_pagamento.strftime('%Y-%m-%d') if fattura.data_pagamento else '',
            'metodo_pagamento': fattura.metodo_pagamento,
            'cliente_id': fattura.cliente_id, # <--- Aggiungi questa riga
            'numero_sedute': fattura.numero_sedute,
            'totale': f"{fattura.totale:.2f}",
            'bollo_applicato': fattura.bollo,
            'descrizione': fattura.descrizione,
            'inviata_sns': fattura.inviata_sns,
            'calcoli': {
                'subtotale_prestazioni': f"{calcoli['subtotale_base']:.2f}",
                'contributo': f"{calcoli['contributo']:.2f}",
                'totale_imponibile': f"{calcoli['totale_imponibile']:.2f}",
                'bollo_importo': f"{calcoli['bollo_importo']:.2f}"
            }
        })
    elif request.method == 'PUT':
        data = request.get_json()

        # Aggiorna il cliente
        fattura.cliente_id = data.get('cliente_id', fattura.cliente_id) # <-- Aggiungi questa riga

        # Conversione esplicita del valore del checkbox in booleano
        inviata_sns_value = data.get('inviata_sns', False)
        if inviata_sns_value == 'on':
            fattura.inviata_sns = True
        else:
            fattura.inviata_sns = False
            
        fattura.data_fattura = datetime.strptime(data['data_fattura'], '%Y-%m-%d').date()
        fattura.data_pagamento = datetime.strptime(data['data_pagamento'], '%Y-%m-%d').date() if data.get('data_pagamento') else None
        fattura.metodo_pagamento = data.get('metodo_pagamento')
        fattura.numero_sedute = int(data.get('numero_sedute', fattura.numero_sedute))

        calcoli = calculate_invoice_totals(fattura.numero_sedute)
        fattura.totale = calcoli['totale']
        fattura.bollo = calcoli['bollo_flag']
        fattura.descrizione = f"n. {fattura.numero_sedute} di Sedut{'e' if fattura.numero_sedute > 1 else 'a'} di consulenza psicologica"

        db.session.commit()
        
        return jsonify({'message': 'Fattura aggiornata con successo!'})

@app.route('/api/invoices/<int:invoice_id>/download', methods=['GET'])
def download_invoice_docx(invoice_id):
    try:
        fattura = Fattura.query.get_or_404(invoice_id)
        cliente = Cliente.query.get_or_404(fattura.cliente_id)

        template_path = os.path.join(app.root_path, 'templates', 'invoice_template.docx')
        if not os.path.exists(template_path):
            return jsonify({"error": "Template file not found"}), 404
        
        doc = DocxTemplate(template_path)
        
        calcoli = calculate_invoice_totals(fattura.numero_sedute)
        descrizione_prestazione = f"n. {calcoli['numero_sedute']} di Sedut{'e' if calcoli['numero_sedute'] > 1 else 'a'} di consulenza psicologica"
        
        bollo_descrizione = "Imposta di Bollo - Esc. Art. 15" if calcoli['bollo_flag'] else ""
        bollo_importo_formattato = f"€{calcoli['bollo_importo']:.2f}".replace('.', ',') if calcoli['bollo_flag'] else ""
        
        context = {
            'numero_fattura': f"{fattura.progressivo}",
            'data_fattura': fattura.data_fattura.strftime('%d/%m/%Y'),
            'cliente_nome': cliente.nome,
            'cliente_cognome': cliente.cognome,
            'cliente_codice_fiscale': cliente.codice_fiscale,
            'cliente_indirizzo': cliente.indirizzo,
            'cliente_citta': getattr(cliente, 'citta', ''),
            'cliente_cap': getattr(cliente, 'cap', ''),
            'descrizione': descrizione_prestazione,
            'numero_sedute': calcoli['numero_sedute'],
            'subtotale_prestazioni': f"€{calcoli['subtotale_base']:.2f}".replace('.', ','),
            'contributo': f"€{calcoli['contributo']:.2f}".replace('.', ','),
            'totale_imponibile': f"€{calcoli['totale_imponibile']:.2f}".replace('.', ','),
            'bollo_descrizione': bollo_descrizione,
            'bollo_importo_formattato': bollo_importo_formattato,
            'totale': f"€{calcoli['totale']:.2f}".replace('.', ','),
            'metodo_pagamento': fattura.metodo_pagamento,
            'data_pagamento': fattura.data_pagamento.strftime('%d/%m/%Y') if fattura.data_pagamento else 'Non pagato',
        }
        
        doc.render(context)
        
        file_path = os.path.join(app.root_path, 'invoices', f"fattura_{fattura.progressivo}_{fattura.anno}.docx")
        doc.save(file_path)
        
        return_data = send_file(file_path, as_attachment=True)
        return return_data

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint di health check
@app.route('/health')
def health_check():
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({"status": "healthy"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500