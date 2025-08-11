FROM python:3.12-slim

WORKDIR /app

# Copia i requisiti e installa le dipendenze
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Crea la cartella del pacchetto e copia i file al suo interno
WORKDIR /app/invoice_frontend
COPY main.py ./
COPY cliente_routes.py ./
COPY fattura_routes.py ./
COPY costi_routes.py ./
COPY templates ./templates
COPY static ./static
COPY __init__.py ./

# Torna alla directory principale per impostare il comando CMD
WORKDIR /app

# Avvia l'applicazione Flask con Waitress
# Il comando ora funziona perché 'invoice_frontend' è un pacchetto riconosciuto
CMD ["waitress-serve", "--listen=0.0.0.0:80", "invoice_frontend.main:app"]
