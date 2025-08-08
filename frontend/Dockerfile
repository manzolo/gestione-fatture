FROM python:3.12-slim

WORKDIR /app

# Copia i requisiti e installa le dipendenze
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice dell'applicazione
COPY main.py ./main.py
COPY templates ./templates
COPY static ./static

# Espone la porta su cui gira l'applicazione (Uvicorn per FastAPI)
EXPOSE 80

# Comando per avviare l'applicazione Uvicorn
# --host 0.0.0.0 rende l'applicazione accessibile da tutte le interfacce di rete
# --port 80 ascolta sulla porta 80 all'interno del container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]