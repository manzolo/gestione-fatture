FROM python:3.12-slim

WORKDIR /app

# Installa netcat (per wait-for-it.sh) e postgresql-client (per pg_isready)
RUN apt-get update && \
    apt-get install -y curl netcat-traditional postgresql-client build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copia solo il file requirements.txt della tua app backend
# Questo assume che il requirements.txt sia all'interno della cartella backend/
COPY ./backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copia lo script entrypoint e rendilo eseguibile
COPY ./backend/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copia l'intera directory dell'applicazione backend
# Questo include main.py, models.py, config.py e il cruciale __init__.py
COPY ./backend /app/backend

# Copia alembic.ini e la directory delle migrazioni alembic
# Assumiamo che si trovino nella root del tuo progetto locale
COPY ./backend/alembic.ini /app/
COPY ./backend/alembic /app/alembic

# Espone la porta su cui gira FastAPI
EXPOSE 8000

# Imposta l'entrypoint per eseguire le migrazioni e poi avviare l'app
ENTRYPOINT ["/app/entrypoint.sh"]