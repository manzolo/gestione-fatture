import asyncio
import logging
import os
from fastapi import FastAPI
from sqlalchemy.orm import Session

# Importa i moduli refactorizzati
from .database import engine, get_db
from .models import Base, Client
from .routers import healtcheck_router

# Configure the logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Backend API (Microservice Manager)",
    version="1.0.0",
    contact={
        "name": "Andrea Manzi",
        "email": "manzolo@libero.it",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_url="/openapi.json",
    docs_url="/swagger",
    redoc_url="/redoc"
)

# Includi i router
app.include_router(healtcheck_router.router)

# --- Application Startup Event ---
@app.on_event("startup")
async def startup_event():
    # Crea le tabelle del database se non esistono (utile per lo sviluppo senza Alembic)
    # Se usi Alembic per le migrazioni, puoi commentare questa riga.
    # Base.metadata.create_all(bind=engine)
    
    # Popola la tabella operation_types con dati iniziali se è vuota
    db: Session = next(get_db())
    try:
        if db.query(Client).count() == 0:
            logger.info("No Clients...")
        else:
            logger.info("Clients already populated.")
    finally:
        db.close()
