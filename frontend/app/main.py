from flask import Flask, render_template
import os
from datetime import datetime

# Importa i Blueprint dai nuovi file nella cartella routes
from .routes.cliente_routes import cliente_bp
from .routes.fattura_routes import fattura_bp
from .routes.costi_routes import costi_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "una-chiave-segreta-molto-complessa")

# Versione applicazione: valorizzata dal tag di release via INVOICE_VERSION
# (impostata nel .env del server dal flusso /bump); "dev" in locale.
APP_VERSION = os.getenv("INVOICE_VERSION", "dev")


@app.context_processor
def inject_app_version():
    """Rende {{ app_version }} disponibile in tutti i template."""
    return {"app_version": APP_VERSION}

# Variabile d'ambiente per l'URL del backend
BACKEND_URL = os.getenv("BACKEND_URL", "http://invoice_backend:5000")

# Funzione di filtro personalizzata per Jinja
def format_date_italian(value):
    if value is None:
        return None
    try:
        date_obj = datetime.strptime(value, '%Y-%m-%d')
        return date_obj.strftime('%d/%m/%Y')
    except (ValueError, TypeError):
        return value

# Aggiungi il filtro personalizzato all'ambiente Jinja
app.jinja_env.filters['to_italian_date'] = format_date_italian

# Registra i Blueprint
# Le rotte definite nei Blueprint verranno aggiunte all'applicazione principale
app.register_blueprint(cliente_bp)
app.register_blueprint(fattura_bp)
app.register_blueprint(costi_bp)