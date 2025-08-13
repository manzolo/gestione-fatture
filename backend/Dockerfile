FROM python:3.12-slim

WORKDIR /app

# Installa netcat, postgresql-client, build-essential, LibreOffice headless e Java
RUN apt-get update && \
    apt-get install -y curl netcat-traditional postgresql-client build-essential libreoffice libreoffice-java-common default-jre && \
    rm -rf /var/lib/apt/lists/*

# Copia requirements e installa le dipendenze Python
COPY ./backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copia lo script entrypoint
COPY ./backend/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copia il codice backend nella cartella app
COPY ./backend/app /app/app

# Copia alembic
COPY ./backend/alembic.ini /app/
COPY ./backend/alembic /app/alembic

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]