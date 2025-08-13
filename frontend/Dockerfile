FROM python:3.12-slim

WORKDIR /app

# Copia i requisiti e installa le dipendenze
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copia l'intera applicazione frontend nella cartella app
COPY ./app /app/app

EXPOSE 80

# Avvia l'applicazione Flask con Waitress
CMD ["waitress-serve", "--listen=0.0.0.0:80", "app.main:app"]