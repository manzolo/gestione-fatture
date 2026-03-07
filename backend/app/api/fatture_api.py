from flask import Blueprint, request, jsonify, send_file, Response, current_app
from app.models import db, Fattura, FatturaProgressivo, Cliente, Costo
from datetime import datetime
from sqlalchemy import text, func, extract
from collections import defaultdict
from docxtpl import DocxTemplate
import requests
import os
import json
import tempfile
import zipfile
import shutil
from app.utils import calculate_invoice_totals, calculate_prezzo_base_da_totale, format_numero_sedute, PRESTAZIONE_BASE, CONTRIBUTO_PERCENTUALE, BOLLO_COSTO, BOLLO_SOGLIA

invoices_bp = Blueprint('invoices_bp', __name__)


def _build_pagamento_descrizione(fattura):
    """Costruisce la descrizione del pagamento per il template della fattura."""
    metodo = fattura.metodo_pagamento or ''
    if fattura.data_pagamento:
        return f"Pagato con {metodo} in data {fattura.data_pagamento.strftime('%d/%m/%Y')}"
    elif metodo.lower() == 'bonifico':
        iban = os.getenv('INVOICE_IBAN', '')
        intestatario = os.getenv('INVOICE_INTESTATARIO', '')
        if iban and intestatario:
            return f"Il pagamento dovrà essere effettuato a mezzo bonifico bancario sull'IBAN {iban} intestato a {intestatario}"
        elif iban:
            return f"Il pagamento dovrà essere effettuato a mezzo bonifico bancario sull'IBAN {iban}"
        else:
            return "Il pagamento dovrà essere effettuato a mezzo bonifico bancario"
    else:
        return f"Pagato con {metodo} in data Non pagato"


@invoices_bp.route('/invoices', methods=['GET', 'POST'])
def invoices_api():
    if request.method == 'POST':
        data = request.get_json()
        current_year = datetime.now().year
        
        # VALIDAZIONE E CONVERSIONE NUMERO_SEDUTE
        try:
            numero_sedute = float(data.get('numero_sedute', 1))
            if numero_sedute <= 0:
                return jsonify({'message': 'Il numero di sedute deve essere maggiore di 0'}), 400
            if numero_sedute > 100:
                return jsonify({'message': 'Il numero di sedute non può superare 100'}), 400
        except (ValueError, TypeError):
            return jsonify({'message': 'Il numero di sedute deve essere un numero valido (es: 1, 1.5, 2.5)'}), 400
        
        # GESTIONE PREZZO TOTALE UNITARIO (conversione in prezzo base)
        prezzo_totale_unitario = data.get('prezzo_totale_unitario', 60.00)  # Default 60€
        try:
            prezzo_totale_unitario = float(prezzo_totale_unitario)
            if prezzo_totale_unitario <= 0:
                return jsonify({'message': 'Il prezzo deve essere maggiore di 0'}), 400
            if prezzo_totale_unitario > 1000:
                return jsonify({'message': 'Il prezzo non può superare 1000€'}), 400
            # Converte il prezzo totale in prezzo base
            prezzo_base = calculate_prezzo_base_da_totale(prezzo_totale_unitario)
        except (ValueError, TypeError):
            return jsonify({'message': 'Il prezzo deve essere un numero valido'}), 400
        
        progressivo_entry = FatturaProgressivo.query.filter_by(anno=current_year).first()
        if not progressivo_entry:
            progressivo_entry = FatturaProgressivo(anno=current_year, last_progressivo=0)
            db.session.add(progressivo_entry)
            db.session.commit()
        
        progressivo = progressivo_entry.last_progressivo + 1
        
        # Calcola i totali usando il prezzo base personalizzato
        calcoli = calculate_invoice_totals(numero_sedute, prezzo_base)

        numero_sedute_formattato = format_numero_sedute(numero_sedute)
        descrizione = f"n. {numero_sedute_formattato} di Sedut{'e' if numero_sedute > 1 else 'a'} di consulenza psicologica"

        inviata_sts_bool = data.get('inviata_sts', False)

        nuova_fattura = Fattura(
            anno=current_year,
            progressivo=progressivo,
            data_fattura=datetime.strptime(data['data_fattura'], '%Y-%m-%d').date(),
            data_pagamento=datetime.strptime(data['data_pagamento'], '%Y-%m-%d').date() if data.get('data_pagamento') else None,
            metodo_pagamento=data.get('metodo_pagamento'),
            cliente_id=data['cliente_id'],
            importo_prestazione=prezzo_base,  # Salva il prezzo base
            bollo=calcoli['bollo_flag'],
            descrizione=descrizione,
            totale=calcoli['totale'],
            numero_sedute=numero_sedute,
            inviata_sts=inviata_sts_bool
        )
        
        db.session.add(nuova_fattura)
        progressivo_entry.last_progressivo = progressivo
        db.session.commit()
        
        return jsonify({'message': 'Fattura aggiunta con successo!', 'id': nuova_fattura.id}), 201
    else:  
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
                'inviata_sts': i.inviata_sts or False,
                'protocollo_sts': i.protocollo_sts,
                'data_invio_sts': i.data_invio_sts.isoformat() if i.data_invio_sts else None,
            })

        sorted_years = sorted(grouped_invoices.keys(), reverse=True)
        sorted_grouped_invoices = {year: grouped_invoices[year] for year in sorted_years}
        json_output = json.dumps(sorted_grouped_invoices)
        return Response(json_output, mimetype='application/json')

@invoices_bp.route('/invoices/<int:invoice_id>', methods=['GET', 'PUT'])
def invoice_api_detail(invoice_id):
    fattura = Fattura.query.get_or_404(invoice_id)
    
    if request.method == 'GET':
        # Usa importo_prestazione (prezzo base salvato nel database)
        prezzo_base = fattura.importo_prestazione
        calcoli = calculate_invoice_totals(fattura.numero_sedute, prezzo_base)
        
        # Calcola il prezzo totale per mostrarlo nel form
        prezzo_totale_unitario = round(prezzo_base * (1 + CONTRIBUTO_PERCENTUALE), 2)
        
        return jsonify({
            'id': fattura.id,
            'numero_fattura': f"{fattura.progressivo}/{fattura.anno}",
            'data_fattura': fattura.data_fattura.strftime('%Y-%m-%d'),
            'data_pagamento': fattura.data_pagamento.strftime('%Y-%m-%d') if fattura.data_pagamento else '',
            'metodo_pagamento': fattura.metodo_pagamento,
            'cliente_id': fattura.cliente_id,
            'numero_sedute': fattura.numero_sedute,
            'prezzo_unitario': prezzo_base,  # Prezzo base
            'prezzo_totale_unitario': prezzo_totale_unitario,  # Prezzo totale (base + contributo)
            'totale': f"{fattura.totale:.2f}",
            'bollo_applicato': fattura.bollo,
            'descrizione': fattura.descrizione,
            'inviata_sts': fattura.inviata_sts,
            'calcoli': {
                'subtotale_prestazioni': f"{calcoli['subtotale_base']:.2f}",
                'contributo': f"{calcoli['contributo']:.2f}",
                'totale_imponibile': f"{calcoli['totale_imponibile']:.2f}",
                'bollo_importo': f"{calcoli['bollo_importo']:.2f}"
            }
        })
    elif request.method == 'PUT':
        data = request.get_json()
        fattura.cliente_id = data.get('cliente_id', fattura.cliente_id)
        inviata_sts_bool = data.get('inviata_sts', False)
        fattura.data_fattura = datetime.strptime(data['data_fattura'], '%Y-%m-%d').date()
        fattura.data_pagamento = datetime.strptime(data['data_pagamento'], '%Y-%m-%d').date() if data.get('data_pagamento') else None
        fattura.metodo_pagamento = data.get('metodo_pagamento')
        
        # VALIDAZIONE E CONVERSIONE NUMERO_SEDUTE
        numero_sedute_update = data.get('numero_sedute')
        if numero_sedute_update is not None:
            try:
                numero_sedute_update = float(numero_sedute_update)
                if numero_sedute_update <= 0:
                    return jsonify({'message': 'Il numero di sedute deve essere maggiore di 0'}), 400
                if numero_sedute_update > 100:
                    return jsonify({'message': 'Il numero di sedute non può superare 100'}), 400
                fattura.numero_sedute = numero_sedute_update
            except (ValueError, TypeError):
                return jsonify({'message': 'Il numero di sedute deve essere un numero valido'}), 400
        
        # GESTIONE PREZZO TOTALE UNITARIO (se fornito, aggiorna il prezzo_unitario)
        prezzo_totale_update = data.get('prezzo_totale_unitario')
        if prezzo_totale_update is not None:
            try:
                prezzo_totale_update = float(prezzo_totale_update)
                if prezzo_totale_update <= 0:
                    return jsonify({'message': 'Il prezzo deve essere maggiore di 0'}), 400
                if prezzo_totale_update > 1000:
                    return jsonify({'message': 'Il prezzo non può superare 1000€'}), 400
                # Converte il prezzo totale in prezzo base e salva in importo_prestazione
                fattura.importo_prestazione = calculate_prezzo_base_da_totale(prezzo_totale_update)
            except (ValueError, TypeError):
                return jsonify({'message': 'Il prezzo deve essere un numero valido'}), 400
        
        # Usa importo_prestazione (prezzo base salvato nel database)
        prezzo_base = fattura.importo_prestazione
        calcoli = calculate_invoice_totals(fattura.numero_sedute, prezzo_base)
        fattura.totale = calcoli['totale']
        fattura.bollo = calcoli['bollo_flag']
        fattura.inviata_sts = inviata_sts_bool
        numero_sedute_formattato = format_numero_sedute(fattura.numero_sedute)
        fattura.descrizione = f"n. {numero_sedute_formattato} di Sedut{'e' if fattura.numero_sedute > 1 else 'a'} di consulenza psicologica"
        db.session.commit()
        return jsonify({'message': 'Fattura aggiornata con successo!'})

@invoices_bp.route('/invoices/<int:invoice_id>/download', methods=['GET'])
def download_invoice_zip(invoice_id):
    try:
        fattura = Fattura.query.get_or_404(invoice_id)
        cliente = Cliente.query.get_or_404(fattura.cliente_id)
        app_root = current_app.root_path
        
        SAVE_DIR = os.path.join(app_root, 'invoices')
        os.makedirs(SAVE_DIR, exist_ok=True)
        # Cerca prima un template custom (montato via volume), altrimenti usa quello built-in
        custom_template_path = os.path.join(app_root, 'templates', 'custom', 'invoice_template.docx')
        builtin_template_path = os.path.join(app_root, 'templates', 'invoice_template.docx')
        template_path = custom_template_path if os.path.exists(custom_template_path) else builtin_template_path
        if not os.path.exists(template_path):
            return jsonify({"error": "Template file not found"}), 404

        # Usa importo_prestazione (prezzo base salvato nel database)
        prezzo_base = fattura.importo_prestazione
        calcoli = calculate_invoice_totals(fattura.numero_sedute, prezzo_base)
        numero_sedute_formattato = format_numero_sedute(calcoli['numero_sedute'])
        descrizione_prestazione = f"n. {numero_sedute_formattato} di Sedut{'e' if calcoli['numero_sedute'] > 1 else 'a'} di consulenza psicologica"

        bollo_descrizione_estesa = ""
        bollo_descrizione_semplice = ""
        bollo_importo_formattato = ""
        if calcoli['bollo_flag']:
            bollo_descrizione_estesa = "Imposta di bollo da 2 euro assolta sull'originale per importi maggiori di 77,47 euro"
            bollo_descrizione_semplice = "Imposta di Bollo - Esc. Art. 15"
            bollo_importo_formattato = f"€{calcoli['bollo_importo']:.2f}".replace('.', ',')

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
            'numero_sedute': numero_sedute_formattato,
            'subtotale_prestazioni': f"€ {calcoli['subtotale_base']:.2f}".replace('.', ','),
            'contributo': f"€ {calcoli['contributo']:.2f}".replace('.', ','),
            'totale_imponibile': f"€ {calcoli['totale_imponibile']:.2f}".replace('.', ','),
            'bollo_descrizione_estesa': bollo_descrizione_estesa,
            'bollo_descrizione_semplice': bollo_descrizione_semplice,
            'bollo_importo_formattato': bollo_importo_formattato,
            'totale': f"€ {calcoli['totale']:.2f}".replace('.', ','),
            'pagamento_descrizione': _build_pagamento_descrizione(fattura),
            # Dati intestatario (professionista) da env vars
            'intestatario_titolo': os.getenv('INVOICE_INTESTATARIO_TITOLO', ''),
            'intestatario_professione': os.getenv('INVOICE_INTESTATARIO_PROFESSIONE', ''),
            'intestatario_indirizzo': os.getenv('INVOICE_INTESTATARIO_INDIRIZZO', ''),
            'intestatario_cap_citta': os.getenv('INVOICE_INTESTATARIO_CAP_CITTA', ''),
            'intestatario_cf': os.getenv('INVOICE_INTESTATARIO_CF', ''),
            'intestatario_piva': os.getenv('INVOICE_INTESTATARIO_PIVA', ''),
            'intestatario_email': os.getenv('INVOICE_INTESTATARIO_EMAIL', ''),
            'intestatario_pec': os.getenv('INVOICE_INTESTATARIO_PEC', ''),
            'intestatario_nome': os.getenv('INVOICE_INTESTATARIO_NOME', ''),
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            # Crea il DOCX
            docx_path = os.path.join(tmpdir, f"fattura_{fattura.progressivo}_{fattura.anno}.docx")
            doc = DocxTemplate(template_path)
            doc.render(context)
            doc.save(docx_path)
            
            gotenberg_url = os.getenv('GOTENBERG_URL', 'http://localhost:3000')
            gotenberg_libreoffice_endpoint = f'{gotenberg_url}/forms/libreoffice/convert'

            files = {
                'files': open(docx_path, 'rb')
            }
            
            try:
                response = requests.post(gotenberg_libreoffice_endpoint, files=files, timeout=60)
                response.raise_for_status()                
                pdf_path = os.path.join(tmpdir, f"fattura_{fattura.progressivo}_{fattura.anno}.pdf")
                with open(pdf_path, 'wb') as pdf_file:
                    pdf_file.write(response.content)

            except requests.exceptions.RequestException as e:
                print(f"Errore nella comunicazione con Gotenberg: {e}")
                return jsonify({"error": "Errore nella conversione a PDF (problema con il servizio Gotenberg)"}), 500

            # Crea il file ZIP
            zip_path = os.path.join(tmpdir, f"fattura_{fattura.progressivo}_{fattura.anno}.zip")
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                zipf.write(docx_path, os.path.basename(docx_path))
                zipf.write(pdf_path, os.path.basename(pdf_path))
            
            final_zip_path = os.path.join(SAVE_DIR, os.path.basename(zip_path))
            shutil.copyfile(zip_path, final_zip_path)
            
            return send_file(zip_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
@invoices_bp.route('/invoices/years', methods=['GET'])
def get_available_years():
    try:
        years = db.session.query(Fattura.anno).distinct().order_by(Fattura.anno.desc()).all()
        years_list = [year.anno for year in years]
        return jsonify(years_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@invoices_bp.route('/invoices/unpaid', methods=['GET'])
def get_unpaid_invoices():
    fatture = Fattura.query.filter(Fattura.data_pagamento.is_(None)) \
        .order_by(Fattura.anno.desc(), Fattura.progressivo.desc()).all()
    result = []
    for f in fatture:
        result.append({
            'id': f.id,
            'numero_fattura': f'{f.progressivo}/{f.anno}',
            'data_fattura': f.data_fattura.isoformat(),
            'cliente': f'{f.cliente.nome} {f.cliente.cognome}' if f.cliente else None,
            'totale': float(f.totale),
        })
    return jsonify(result)

@invoices_bp.route('/invoices/stats', methods=['GET'])
def get_invoice_stats():
    try:
        year_param = request.args.get('year')
        
        if year_param:
            selected_year = int(year_param)
            year_filter = Fattura.anno == selected_year
        else:
            year_filter = True
            selected_year = None

        total_invoices = db.session.query(Fattura).filter(year_filter).count()
        total_amount = db.session.query(func.sum(Fattura.totale)).filter(year_filter).scalar() or 0.0
        unique_clients = db.session.query(Fattura.cliente_id).filter(year_filter).distinct().count()

        if selected_year:
            monthly_stats = db.session.query(
                extract('month', Fattura.data_fattura).label('mese'),
                func.count(Fattura.id).label('conteggio'),
                func.sum(Fattura.totale).label('totale')
            ).filter(year_filter).group_by('mese').order_by('mese').all()
            monthly_data = [{'mese': int(s.mese), 'conteggio': s.conteggio, 'totale': float(s.totale)} for s in monthly_stats]
        else:
            yearly_stats = db.session.query(
                Fattura.anno.label('anno'),
                func.count(Fattura.id).label('conteggio'),
                func.sum(Fattura.totale).label('totale')
            ).group_by(Fattura.anno).order_by(Fattura.anno).all()
            monthly_data = [{'mese': s.anno, 'conteggio': s.conteggio, 'totale': float(s.totale)} for s in yearly_stats]

        client_stats = db.session.query(
            Cliente.nome,
            Cliente.cognome,
            func.count(Fattura.id).label('conteggio'),
            func.sum(Fattura.totale).label('totale')
        ).join(Fattura, Cliente.id == Fattura.cliente_id).filter(year_filter).group_by(Cliente.id).order_by(func.count(Fattura.id).desc()).all()

        client_data = [{'cliente': f'{s.nome} {s.cognome}', 'conteggio': s.conteggio, 'totale': float(s.totale)} for s in client_stats]

        return jsonify({
            'totale_fatture': total_invoices,
            'totale_annuo': total_amount,
            'clienti_con_fatture': unique_clients,
            'per_mese': monthly_data,
            'per_cliente': client_data,
            'anno_selezionato': selected_year
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@invoices_bp.route('/costs/stats', methods=['GET'])
def get_costs_stats():
    """Endpoint per ottenere le statistiche dei costi (con supporto per parametro year)."""
    try:
        year_param = request.args.get('year')
        
        if year_param:
            selected_year = int(year_param)
            # FIX: Filtra per anno di competenza (anno_riferimento) invece che data pagamento
            year_filter = Costo.anno_riferimento == selected_year
            total_costs_amount = db.session.query(func.sum(Costo.totale)).filter(year_filter).scalar() or 0.0

            monthly_stats = db.session.query(
                extract('month', Costo.data_pagamento).label('mese'),
                func.count(Costo.id).label('conteggio'),
                func.sum(Costo.totale).label('totale')
            ).filter(year_filter).group_by('mese').order_by('mese').all()
            monthly_data = [{'mese': int(s.mese), 'conteggio': s.conteggio, 'totale': float(s.totale)} for s in monthly_stats]

            
        else:
            year_filter = True
            selected_year = None
            total_costs_amount = db.session.query(func.sum(Costo.totale)).scalar() or 0.0

            # FIX: Raggruppa per anno di competenza (anno_riferimento)
            yearly_stats = db.session.query(
                Costo.anno_riferimento.label('anno'),
                func.count(Costo.id).label('conteggio'),
                func.sum(Costo.totale).label('totale')
            ).group_by('anno').order_by('anno').all()
            monthly_data = [{'mese': s.anno, 'conteggio': s.conteggio, 'totale': float(s.totale)} for s in yearly_stats]

        total_costs_count = db.session.query(Costo).filter(year_filter).count()

        category_stats = db.session.query(
            Costo.descrizione,
            func.count(Costo.id).label('conteggio'),
            func.sum(Costo.totale).label('totale')
        ).filter(year_filter).group_by(Costo.descrizione).order_by(func.count(Costo.id).desc()).all()

        category_data = [{'descrizione': s.descrizione, 'conteggio': s.conteggio, 'totale': float(s.totale)} for s in category_stats]

        return jsonify({
            'totale_costi': total_costs_count,
            'totale_annuo': total_costs_amount,
            'per_mese': monthly_data,
            'per_descrizione': category_data,
            'anno_selezionato': selected_year
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500