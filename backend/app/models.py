from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base

db = SQLAlchemy()

# Base è necessaria per Alembic
Base = db.Model 

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cognome = db.Column(db.String(100), nullable=False)
    codice_fiscale = db.Column(db.String(16), unique=True, nullable=False)
    indirizzo = db.Column(db.String(200))
    citta = db.Column(db.String(255))
    cap = db.Column(db.String(5))

class Fattura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    anno = db.Column(db.Integer, nullable=False)
    progressivo = db.Column(db.Integer, nullable=False)
    # Aggiunti nuovi campi
    data_fattura = db.Column(db.Date, nullable=False, default=datetime.now)
    data_pagamento = db.Column(db.Date)
    metodo_pagamento = db.Column(db.String(50))
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    importo_prestazione = db.Column(db.Float, nullable=False)
    bollo = db.Column(db.Boolean, default=False)
    descrizione = db.Column(db.String(255), nullable=False)
    totale = db.Column(db.Float, nullable=False)
    numero_sedute = db.Column(db.Float, nullable=False)
    inviata_sns = db.Column(db.Boolean, default=False)

    cliente = db.relationship('Cliente', backref=db.backref('fatture', lazy=True))

# Nuovo modello per gestire il progressivo annuale delle fatture
class FatturaProgressivo(db.Model):
    __tablename__ = 'fattura_progressivo'
    anno = db.Column(db.Integer, primary_key=True)
    last_progressivo = db.Column(db.Integer, default=0)

class Costo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descrizione = db.Column(db.String(255), nullable=False)
    anno_riferimento = db.Column(db.Integer, nullable=False)
    data_pagamento = db.Column(db.Date, nullable=False, default=datetime.now)
    totale = db.Column(db.Float, nullable=False)
    pagato = db.Column(db.Boolean, default=False)