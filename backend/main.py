from flask import Flask, request, jsonify, send_file
from .models import db, Cliente, Fattura, FatturaProgressivo
from datetime import datetime
import os
from docx import Document
from docxtpl import DocxTemplate
from sqlalchemy import text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_SQLALCHEMY_URL') or 'sqlite:///test.db'
db.init_app(app)

# Creazione della directory temporanea se non esiste
temp_dir = os.path.join(app.root_path, 'temp')
if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)

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
    
    # Usa il contributo fisso, non la percentuale che è stata rimossa
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
        indirizzo=data.get('indirizzo'),
        # Aggiungi i nuovi campi se presenti
        citta=data.get('citta'),
        cap=data.get('cap')
    )
    db.session.add(new_client)
    db.session.commit()
    return jsonify({'message': 'Cliente aggiunto con successo!'}), 201

@app.route('/api/clients/<int:client_id>', methods=['PUT'])
def edit_client(client_id):
    client = Cliente.query.get_or_404(client_id)
    data = request.get_json()
    client.nome = data.get('nome', client.nome)
    client.cognome = data.get('cognome', client.cognome)
    client.codice_fiscale = data.get('codice_fiscale', client.codice_fiscale)
    client.indirizzo = data.get('indirizzo', client.indirizzo)
    client.citta = data.get('citta', getattr(client, 'citta', None))
    client.cap = data.get('cap', getattr(client, 'cap', None))
    db.session.commit()
    return jsonify({'message': 'Cliente aggiornato con successo!'})

@app.route('/api/clients/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    client = Cliente.query.get_or_404(client_id)
    # assumiamo relazione .fatture o .invoices; adattare se nome diverso
    if getattr(client, 'fatture', None) and len(client.fatture) > 0:
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
        'cliente': f"{i.cliente.nome} {i.cliente.cognome}" if i.cliente else None,
        'descrizione': i.descrizione,
        'totale': f"{i.totale:.2f}"
    } for i in invoices]
    return jsonify(invoices_list)

# Nuovo endpoint per calcolare anteprima totali
@app.route('/api/calculate-totals', methods=['POST'])
def calculate_totals():
    data = request.get_json() or {}
    numero_sedute = int(data.get('numero_sedute', 1))
    
    calcoli = calculate_invoice_totals(numero_sedute)
    
    return jsonify({
        'numero_sedute': calcoli['numero_sedute'],
        'importo_unitario': f"€{calcoli['totale_unitario']:.2f}", # Mostra il prezzo unitario totale (base + contributo)
        'subtotale_prestazioni': f"€{calcoli['subtotale_base']:.2f}", # Subtotale delle prestazioni di base
        'contributo': f"€{calcoli['contributo']:.2f}",
        'totale_imponibile': f"€{calcoli['totale_imponibile']:.2f}", # Nuovo campo per il totale prima del bollo
        'bollo_applicato': calcoli['bollo_flag'],
        'bollo_importo': f"€{calcoli['bollo_importo']:.2f}",
        'totale': f"€{calcoli['totale']:.2f}"
    })

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
    numero_sedute = int(data.get('numero_sedute', 1))

    # Usa la funzione di utilità per i calcoli
    calcoli = calculate_invoice_totals(numero_sedute)
    
    descrizione = f"n. {numero_sedute} di Sedut{'e' if numero_sedute > 1 else 'a'} di consulenza psicologica"
    
    nuova_fattura = Fattura(
        anno=current_year,
        progressivo=progressivo,
        data_fattura=datetime.strptime(data['data_fattura'], '%Y-%m-%d').date() if data.get('data_fattura') else datetime.now().date(),
        data_pagamento=datetime.strptime(data['data_pagamento'], '%Y-%m-%d').date() if data.get('data_pagamento') else None,
        metodo_pagamento=data.get('metodo_pagamento'),
        cliente_id=data['cliente_id'],
        importo_prestazione=PRESTAZIONE_BASE, # Salva il prezzo unitario base
        bollo=calcoli['bollo_flag'],
        descrizione=descrizione,
        totale=calcoli['totale'],
        numero_sedute=numero_sedute
    )
    
    db.session.add(nuova_fattura)
    progressivo_entry.last_progressivo = progressivo
    db.session.commit()
    
    return jsonify({'message': 'Fattura aggiunta con successo!', 'id': nuova_fattura.id}), 201


@app.route('/api/invoices/<int:invoice_id>/download', methods=['GET'])
def download_invoice_docx(invoice_id):
    try:
        fattura = Fattura.query.get_or_404(invoice_id)
        cliente = Cliente.query.get_or_404(fattura.cliente_id)

        template_path = os.path.join(app.root_path, 'templates', 'invoice_template.docx')
        if not os.path.exists(template_path):
            return jsonify({"error": "Template file not found"}), 404
        
        doc = DocxTemplate(template_path)
        
        # Ricalcola i totali basandosi su numero_sedute salvato
        calcoli = calculate_invoice_totals(fattura.numero_sedute)
        
        # Gestione del testo condizionale per bollo e descrizione
        descrizione_prestazione = f"n. {calcoli['numero_sedute']} di Sedut{'e' if calcoli['numero_sedute'] > 1 else 'a'} di consulenza psicologica"
        
        # Variabili per il bollo: se il bollo non si applica, le stringhe saranno vuote
        bollo_descrizione = "Imposta di Bollo - Esc. Art. 15" if calcoli['bollo_flag'] else ""
        bollo_importo_formattato = f"€{calcoli['bollo_importo']:.2f}".replace('.', ',') if calcoli['bollo_flag'] else ""
        
        context = {
            'numero_fattura': f"{fattura.progressivo}/{fattura.anno}",
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
        
        # Salva il file nella nuova directory "invoices"
        file_path = os.path.join(app.root_path, 'invoices', f"fattura_{fattura.progressivo}_{fattura.anno}.docx")
        doc.save(file_path)
        
        return_data = send_file(file_path, as_attachment=True)
        # La riga per la rimozione del file è stata rimossa
            
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
