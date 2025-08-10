from flask import Flask, request, jsonify, send_file, Response
from .models import db
from datetime import datetime
import os
from .clienti_api import clients_bp
from .fatture_api import invoices_bp

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

# Registra i Blueprint
app.register_blueprint(clients_bp, url_prefix='/api')
app.register_blueprint(invoices_bp, url_prefix='/api')

# Endpoint di health check
@app.route('/health')
def health_check():
    try:
        # Aggiungi qui un controllo per il database
        with app.app_context():
            db.session.execute(db.text('SELECT 1'))
        return jsonify({"status": "healthy"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500
