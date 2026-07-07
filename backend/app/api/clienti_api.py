from flask import Blueprint, request, jsonify, send_file, current_app
from app.models import db, Cliente
from app.utils import decode_codice_fiscale
from codicefiscale import isvalid
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime, timedelta
from app.timezone import now_local
from docxtpl import DocxTemplate
import requests
import os
import re
import tempfile
import zipfile

clients_bp = Blueprint('clients_bp', __name__)

def extract_constraint_error(error_message):
    """
    Estrae informazioni specifiche dagli errori di constraint del database
    """
    # Pattern per errori di chiave duplicata PostgreSQL
    duplicate_key_pattern = r'duplicate key value violates unique constraint "([^"]+)"'
    detail_pattern = r'DETAIL:\s*Key \(([^)]+)\)=\(([^)]+)\) already exists'
    
    match_constraint = re.search(duplicate_key_pattern, str(error_message))
    match_detail = re.search(detail_pattern, str(error_message))
    
    if match_constraint and match_detail:
        constraint_name = match_constraint.group(1)
        field_name = match_detail.group(1)
        field_value = match_detail.group(2)
        
        # Messaggi specifici per diversi constraint
        if 'codice_fiscale' in constraint_name:
            return f"Codice Fiscale '{field_value}' già presente nel sistema. Utilizza un codice fiscale diverso."
        elif 'email' in constraint_name:
            return f"Email '{field_value}' già utilizzata da un altro cliente."
        else:
            return f"Il valore inserito per il campo '{field_name}' è già presente nel sistema."
    
    return "Errore: dati duplicati nel sistema."

def handle_database_error(error):
    """
    Gestisce gli errori del database e restituisce messaggi user-friendly
    """
    if isinstance(error, IntegrityError):
        if 'UniqueViolation' in str(error.orig):
            return extract_constraint_error(str(error.orig)), 409
        elif 'NotNullViolation' in str(error.orig):
            # Estrae il nome del campo null
            null_field_pattern = r'null value in column "([^"]+)" violates not-null constraint'
            match = re.search(null_field_pattern, str(error.orig))
            if match:
                field_name = match.group(1)
                return f"Il campo '{field_name}' è obbligatorio.", 400
            return "Campi obbligatori mancanti.", 400
        elif 'ForeignKeyViolation' in str(error.orig):
            return "Riferimento non valido. Controlla i dati inseriti.", 400
        else:
            return "Errore di integrità dei dati.", 400
    
    return "Errore del database.", 500

def parse_data_nascita(raw):
    """Ritorna (date|None, errore|None) dal campo opzionale data_nascita (YYYY-MM-DD)."""
    raw = (raw or '').strip()
    if not raw:
        return None, None
    try:
        return datetime.strptime(raw, '%Y-%m-%d').date(), None
    except ValueError:
        return None, "La data di nascita deve essere in formato YYYY-MM-DD."


@clients_bp.route('/clients', methods=['GET', 'POST'])
def clients_api():
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # Validazione dati di input
            if not data:
                return jsonify({"message": "Nessun dato fornito."}), 400
            
            # Campi obbligatori
            required_fields = ['nome', 'cognome', 'codice_fiscale']
            missing_fields = [field for field in required_fields if not data.get(field, '').strip()]
            
            if missing_fields:
                return jsonify({
                    "message": f"Campi obbligatori mancanti: {', '.join(missing_fields)}."
                }), 400
            
            # Validazione codice fiscale
            codice_fiscale = data['codice_fiscale'].strip().upper()
            if not isvalid(codice_fiscale):
                return jsonify({
                    "message": "Il Codice Fiscale inserito non è valido. Controlla il formato."
                }), 400
            
            # Controllo preventivo duplicati codice fiscale
            existing_client = Cliente.query.filter_by(codice_fiscale=codice_fiscale).first()
            if existing_client:
                return jsonify({
                    "message": f"Un cliente con Codice Fiscale '{codice_fiscale}' è già presente nel sistema."
                }), 409
            
            # Validazione lunghezza campi
            if len(data['nome'].strip()) > 100:
                return jsonify({"message": "Il nome non può superare i 100 caratteri."}), 400
            
            if len(data['cognome'].strip()) > 100:
                return jsonify({"message": "Il cognome non può superare i 100 caratteri."}), 400
            
            # Validazione CAP se presente
            cap = data.get('cap', '').strip()
            if cap and not re.match(r'^\d{5}$', cap):
                return jsonify({"message": "Il CAP deve essere composto da 5 cifre."}), 400
            
            # Data di nascita opzionale
            data_nascita, errore_data = parse_data_nascita(data.get('data_nascita'))
            if errore_data:
                return jsonify({"message": errore_data}), 400

            # Creazione nuovo cliente
            # flag_opposizione: checkbox manda "on"/"true"/true, assente = False
            raw_flag = data.get('flag_opposizione', False)
            flag_opposizione = raw_flag in (True, 'true', 'on', '1', 1)

            new_client = Cliente(
                nome=data['nome'].strip(),
                cognome=data['cognome'].strip(),
                codice_fiscale=codice_fiscale,
                luogo_nascita=data.get('luogo_nascita', '').strip() or None,
                data_nascita=data_nascita,
                indirizzo=data.get('indirizzo', '').strip() or None,
                citta=data.get('citta', '').strip() or None,
                cap=cap or None,
                flag_opposizione=flag_opposizione
            )
            
            db.session.add(new_client)
            db.session.commit()
            
            return jsonify({
                "message": f"Cliente {new_client.nome} {new_client.cognome} aggiunto con successo!",
                "id": new_client.id
            }), 201
            
        except IntegrityError as e:
            db.session.rollback()
            error_message, status_code = handle_database_error(e)
            return jsonify({"message": error_message}), status_code
        
        except Exception as e:
            db.session.rollback()
            print(f"Errore imprevisto durante l'aggiunta del cliente: {str(e)}")
            return jsonify({
                "message": "Si è verificato un errore imprevisto. Riprova più tardi."
            }), 500
    
    else:  # GET
        try:
            clients = Cliente.query.all()
            clients_list = [{
                'id': c.id,
                'nome': c.nome,
                'cognome': c.cognome,
                'codice_fiscale': c.codice_fiscale,
                'luogo_nascita': c.luogo_nascita,
                'data_nascita': c.data_nascita.isoformat() if c.data_nascita else None,
                'indirizzo': c.indirizzo,
                'citta': c.citta,
                'cap': c.cap,
                'flag_opposizione': c.flag_opposizione or False
            } for c in clients]
            return jsonify(clients_list)
        except Exception as e:
            print(f"Errore durante il recupero dei clienti: {str(e)}")
            return jsonify({"message": "Errore durante il recupero dei clienti."}), 500

@clients_bp.route('/clients/<int:client_id>', methods=['GET', 'PUT', 'DELETE'])
def client_api_detail(client_id):
    try:
        client = Cliente.query.get(client_id)
        if not client:
            return jsonify({"message": "Cliente non trovato."}), 404
        
        if request.method == 'GET':
            return jsonify({
                'id': client.id,
                'nome': client.nome,
                'cognome': client.cognome,
                'codice_fiscale': client.codice_fiscale,
                'luogo_nascita': client.luogo_nascita,
                'data_nascita': client.data_nascita.isoformat() if client.data_nascita else None,
                'indirizzo': client.indirizzo,
                'citta': client.citta,
                'cap': client.cap,
                'flag_opposizione': client.flag_opposizione or False
            })
        
        elif request.method == 'PUT':
            try:
                data = request.get_json()
                
                if not data:
                    return jsonify({"message": "Nessun dato fornito per l'aggiornamento."}), 400
                
                # Validazione campi obbligatori se forniti
                if 'nome' in data and not data['nome'].strip():
                    return jsonify({"message": "Il nome non può essere vuoto."}), 400
                
                if 'cognome' in data and not data['cognome'].strip():
                    return jsonify({"message": "Il cognome non può essere vuoto."}), 400
                
                # Validazione codice fiscale se fornito
                if 'codice_fiscale' in data:
                    codice_fiscale = data['codice_fiscale'].strip().upper()
                    if not isvalid(codice_fiscale):
                        return jsonify({
                            "message": "Il Codice Fiscale inserito non è valido. Controlla il formato."
                        }), 400
                    
                    # Controllo duplicati solo se il codice fiscale è diverso da quello attuale
                    if codice_fiscale != client.codice_fiscale:
                        existing_client = Cliente.query.filter_by(codice_fiscale=codice_fiscale).first()
                        if existing_client:
                            return jsonify({
                                "message": f"Un altro cliente con Codice Fiscale '{codice_fiscale}' è già presente nel sistema."
                            }), 409
                
                # Validazione CAP se presente
                if 'cap' in data:
                    cap = data['cap'].strip()
                    if cap and not re.match(r'^\d{5}$', cap):
                        return jsonify({"message": "Il CAP deve essere composto da 5 cifre."}), 400
                
                # Aggiornamento campi
                if 'nome' in data:
                    client.nome = data['nome'].strip()
                if 'cognome' in data:
                    client.cognome = data['cognome'].strip()
                if 'codice_fiscale' in data:
                    client.codice_fiscale = data['codice_fiscale'].strip().upper()
                if 'luogo_nascita' in data:
                    client.luogo_nascita = data['luogo_nascita'].strip() or None
                if 'data_nascita' in data:
                    valore, errore_data = parse_data_nascita(data['data_nascita'])
                    if errore_data:
                        return jsonify({"message": errore_data}), 400
                    client.data_nascita = valore
                if 'indirizzo' in data:
                    client.indirizzo = data['indirizzo'].strip() or None
                if 'citta' in data:
                    client.citta = data['citta'].strip() or None
                if 'cap' in data:
                    client.cap = data['cap'].strip() or None
                if 'flag_opposizione' in data:
                    raw_flag = data['flag_opposizione']
                    client.flag_opposizione = raw_flag in (True, 'true', 'on', '1', 1)

                db.session.commit()
                
                return jsonify({
                    "message": f"Cliente {client.nome} {client.cognome} aggiornato con successo!"
                }), 200
                
            except IntegrityError as e:
                db.session.rollback()
                error_message, status_code = handle_database_error(e)
                return jsonify({"message": error_message}), status_code
            
            except Exception as e:
                db.session.rollback()
                print(f"Errore durante l'aggiornamento del cliente {client_id}: {str(e)}")
                return jsonify({
                    "message": "Si è verificato un errore durante l'aggiornamento. Riprova più tardi."
                }), 500
        
        elif request.method == 'DELETE':
            try:
                # Controllo se il cliente ha fatture associate
                if hasattr(client, 'fatture') and client.fatture:
                    fatture_count = len(client.fatture)
                    return jsonify({
                        'message': f'Impossibile eliminare il cliente: ha {fatture_count} fattur{"a" if fatture_count == 1 else "e"} associat{"a" if fatture_count == 1 else "e"}.'
                    }), 400
                
                client_name = f"{client.nome} {client.cognome}"
                db.session.delete(client)
                db.session.commit()
                
                return jsonify({
                    "message": f"Cliente {client_name} eliminato con successo!"
                }), 200
                
            except Exception as e:
                db.session.rollback()
                print(f"Errore durante l'eliminazione del cliente {client_id}: {str(e)}")
                return jsonify({
                    "message": "Si è verificato un errore durante l'eliminazione. Riprova più tardi."
                }), 500
    
    except Exception as e:
        print(f"Errore generale nell'API cliente {client_id}: {str(e)}")
        return jsonify({"message": "Si è verificato un errore imprevisto."}), 500


PUNTINI = '…' * 8  # linea di puntini per i campi da compilare a mano


def _build_residenza(client):
    """Compone la residenza (es. 'Firenze (50100), Via Roma 123') saltando i campi vuoti."""
    luogo = client.citta or ''
    if client.cap:
        luogo = f"{luogo} ({client.cap})" if luogo else f"CAP {client.cap}"
    parti = [p for p in (luogo, client.indirizzo) if p]
    return ', '.join(parti) if parti else PUNTINI


@clients_bp.route('/clients/<int:client_id>/giustificativo', methods=['GET'])
def download_giustificativo(client_id):
    """
    Genera l'attestazione di presenza (giustificativo) per il cliente,
    precompilata con data e ora correnti, e la restituisce come ZIP
    contenente DOCX e PDF (stesso flusso delle fatture via Gotenberg).

    Query params opzionali: data (YYYY-MM-DD), ora_inizio (HH:MM), ora_fine (HH:MM).
    """
    try:
        client = Cliente.query.get(client_id)
        if not client:
            return jsonify({"message": "Cliente non trovato."}), 404

        app_root = current_app.root_path
        custom_template_path = os.path.join(app_root, 'templates', 'custom', 'giustificativo_template.docx')
        builtin_template_path = os.path.join(app_root, 'templates', 'giustificativo_template.docx')
        template_path = custom_template_path if os.path.exists(custom_template_path) else builtin_template_path
        if not os.path.exists(template_path):
            return jsonify({"error": "Template file not found"}), 404

        adesso = now_local()

        # Data della prestazione: parametro opzionale, default oggi
        data_param = request.args.get('data')
        if data_param:
            try:
                data_prestazione = datetime.strptime(data_param, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"message": "Il parametro 'data' deve essere in formato YYYY-MM-DD."}), 400
        else:
            data_prestazione = adesso.date()

        # Orari: parametri opzionali; di default la seduta si è appena conclusa
        # (dalle = un'ora fa, alle = ora corrente)
        def parse_ora(nome_param, default_value):
            valore = request.args.get(nome_param)
            if not valore:
                return default_value, None
            try:
                return datetime.strptime(valore, '%H:%M').strftime('%H:%M'), None
            except ValueError:
                return None, jsonify({"message": f"Il parametro '{nome_param}' deve essere in formato HH:MM."})

        ora_inizio, err = parse_ora('ora_inizio', (adesso - timedelta(hours=1)).strftime('%H:%M'))
        if err:
            return err, 400
        ora_fine, err = parse_ora('ora_fine', adesso.strftime('%H:%M'))
        if err:
            return err, 400

        # Sesso ricavato dal codice fiscale; data di nascita dal campo
        # anagrafico se presente, altrimenti decodificata dal CF
        dati_cf = decode_codice_fiscale(client.codice_fiscale)
        sesso = dati_cf['sesso'] if dati_cf else None
        if client.data_nascita:
            data_nascita = client.data_nascita.strftime('%d/%m/%Y')
        elif dati_cf:
            data_nascita = dati_cf['data_nascita'].strftime('%d/%m/%Y')
        else:
            data_nascita = PUNTINI

        genere = {
            'M': {'articolo_titolo': 'Il Sig.', 'nato_nata': 'nato', 'presentato_presentata': 'presentato', 'interessato_interessata': 'interessato'},
            'F': {'articolo_titolo': 'La Sig.ra', 'nato_nata': 'nata', 'presentato_presentata': 'presentata', 'interessato_interessata': 'interessata'},
        }.get(sesso, {'articolo_titolo': 'Il/La Sig./Sig.ra', 'nato_nata': 'nato/a', 'presentato_presentata': 'presentato/a', 'interessato_interessata': 'interessato/a'})

        context = {
            'cliente_nome': client.nome,
            'cliente_cognome': client.cognome,
            'cliente_codice_fiscale': client.codice_fiscale,
            'cliente_data_nascita': data_nascita,
            'cliente_luogo_nascita': client.luogo_nascita or PUNTINI,
            'cliente_residenza': _build_residenza(client),
            'data_prestazione': data_prestazione.strftime('%d/%m/%Y'),
            'ora_inizio': ora_inizio,
            'ora_fine': ora_fine,
            **genere,
            # Dati intestatario (professionista) da env vars, come per la fattura
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

        # Riga "luogo, data": città dell'intestatario senza CAP iniziale, se disponibile
        luogo_rilascio = re.sub(r'^\d{5}\s*', '', os.getenv('INVOICE_INTESTATARIO_CAP_CITTA', '')).strip()
        data_rilascio = data_prestazione.strftime('%d/%m/%Y')
        context['luogo_data_rilascio'] = f"{luogo_rilascio}, {data_rilascio}" if luogo_rilascio else data_rilascio

        nome_base = re.sub(r'[^A-Za-z0-9_-]+', '_', f"giustificativo_{client.cognome}_{client.nome}_{data_prestazione.strftime('%Y%m%d')}")

        with tempfile.TemporaryDirectory() as tmpdir:
            docx_path = os.path.join(tmpdir, f"{nome_base}.docx")
            doc = DocxTemplate(template_path)
            doc.render(context)
            doc.save(docx_path)

            gotenberg_url = os.getenv('GOTENBERG_URL', 'http://localhost:3000')
            gotenberg_libreoffice_endpoint = f'{gotenberg_url}/forms/libreoffice/convert'

            try:
                with open(docx_path, 'rb') as docx_file:
                    response = requests.post(gotenberg_libreoffice_endpoint, files={'files': docx_file}, timeout=60)
                response.raise_for_status()
                pdf_path = os.path.join(tmpdir, f"{nome_base}.pdf")
                with open(pdf_path, 'wb') as pdf_file:
                    pdf_file.write(response.content)
            except requests.exceptions.RequestException as e:
                print(f"Errore nella comunicazione con Gotenberg: {e}")
                return jsonify({"error": "Errore nella conversione a PDF (problema con il servizio Gotenberg)"}), 500

            zip_path = os.path.join(tmpdir, f"{nome_base}.zip")
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                zipf.write(docx_path, os.path.basename(docx_path))
                zipf.write(pdf_path, os.path.basename(pdf_path))

            return send_file(zip_path, as_attachment=True, download_name=f"{nome_base}.zip")

    except Exception as e:
        print(f"Errore durante la generazione del giustificativo per il cliente {client_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500