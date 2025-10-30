# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Invoice management system for psychological consultation services. The application manages clients, invoices, and costs with automatic Italian invoice generation (with stamp duty calculation) and PDF export via Gotenberg.

**Technology Stack:**
- Backend: Flask + SQLAlchemy (Python 3.12)
- Frontend: Flask with Jinja2 templates + vanilla JavaScript
- Database: PostgreSQL 13
- PDF Generation: Gotenberg (for converting DOCX to PDF)
- Migrations: Alembic
- Containerization: Docker Compose

**Architecture:** Dockerized microservices with backend API (port 8000), frontend proxy (port 8080), PostgreSQL database, PgAdmin, and Gotenberg service for PDF conversion.

## Development Commands

### Starting the Application
```bash
make start              # Start all containers
make stop               # Stop and remove containers
make restart            # Restart with logs
make rebuild-start      # Rebuild images and start
make dev                # Development mode (rebuild + start + logs)
```

### Testing
```bash
make test-all          # Run all tests (backend + frontend)
make test-backend      # Run backend API tests only
make test-frontend     # Run frontend proxy tests only
make test-quick        # Quick tests without DB reset
```

Test scripts are located in `tests/` directory:
- `run_backend_tests.sh` - Tests backend REST API endpoints
- `run_frontend_tests.sh` - Tests frontend proxy routes

### Database Operations
```bash
make backupdb          # Create PostgreSQL backup
make restoredb         # Restore from backup.sql
make list-backups      # List available backups
make db-shell          # Open PostgreSQL shell
```

### Logs & Diagnostics
```bash
make logs              # View all container logs
make logs-backend      # Backend logs only
make logs-frontend     # Frontend logs only
make logs-db           # Database logs only
make status            # Container status
make health            # Check service health
```

### Docker Registry
```bash
make docker-push       # Publish images to Docker Hub (manzolo/invoice_backend, manzolo/invoice_frontend)
make docker-pull       # Pull images from Docker Hub
```

### Shell Access
```bash
make shell-backend     # Shell into backend container
make shell-frontend    # Shell into frontend container
```

## Application Architecture

### Backend (`/backend`)
REST API server using Flask and SQLAlchemy:
- `app/main.py` - Flask app initialization and blueprint registration
- `app/models.py` - SQLAlchemy models: Cliente, Fattura, FatturaProgressivo, Costo
- `app/schemas.py` - Pydantic schemas for validation
- `app/api/` - API blueprints:
  - `clienti_api.py` - Client CRUD operations
  - `fatture_api.py` - Invoice management including PDF generation via Gotenberg
  - `costi_api.py` - Cost tracking
- `app/utils.py` - Business logic for invoice calculations (stamp duty, unit costs)
- `app/templates/invoice_template.docx` - DOCX template for invoice generation using docxtpl
- `entrypoint.sh` - Wait for PostgreSQL, run Alembic migrations, start Gunicorn

**Port:** 8000 (exposed as BACKEND_PORT)

### Frontend (`/frontend`)
Flask application serving HTML pages with Jinja2 templates and vanilla JS:
- `app/main.py` - Flask app with route blueprints
- `app/routes/` - Route handlers that proxy to backend API:
  - `fattura_routes.py` - Invoice dashboard and operations
  - `cliente_routes.py` - Client management
  - `costi_routes.py` - Cost management
- `app/templates/` - Jinja2 HTML templates
- `app/static/js/` - Vanilla JavaScript (jQuery, Chart.js, Select2)

**Port:** 80 (exposed externally as FRONTEND_EXTERNAL_PORT:8080)

### Database Migrations
Alembic is used for schema migrations:
- Configuration: `backend/alembic.ini`
- Migration scripts: `backend/alembic/versions/`
- Run migrations: Automatically executed on backend startup via `entrypoint.sh`

To create a new migration:
```bash
make shell-backend
alembic revision -m "description"
alembic upgrade head
```

## Key Business Logic

### Invoice Calculation (`backend/app/utils.py`)
```python
PRESTAZIONE_BASE = 58.82           # Base consultation fee
CONTRIBUTO_FISSO_PER_SEDUTA = 1.18 # Fixed contribution per session
BOLLO_COSTO = 2.00                 # Stamp duty cost
BOLLO_SOGLIA = 77.47               # Threshold for stamp duty
```

Invoice totals are calculated with support for fractional sessions (e.g., 1.5, 2.5):
- Subtotal = PRESTAZIONE_BASE × numero_sedute
- Contribution = CONTRIBUTO_FISSO_PER_SEDUTA × numero_sedute
- Stamp duty applies if total > 77.47€
- Progressive invoice numbering per year managed via `FatturaProgressivo` model

### PDF Generation Workflow
1. Backend fills DOCX template (`invoice_template.docx`) using docxtpl
2. DOCX is sent to Gotenberg service via HTTP POST
3. Gotenberg converts DOCX to PDF
4. PDF is stored in `/app/backend/invoices` volume
5. Backend returns PDF to client

Gotenberg URL: `http://invoice_gotenberg:3000` (configured via GOTENBERG_URL env var)

## Database Schema

**Cliente** (clients):
- id, nome, cognome, codice_fiscale (unique), indirizzo, citta, cap

**Fattura** (invoices):
- id, anno, progressivo, data_fattura, data_pagamento, metodo_pagamento
- cliente_id (FK), importo_prestazione, bollo, descrizione, totale
- numero_sedute (float - supports fractional sessions)
- inviata_sns (boolean flag)

**FatturaProgressivo** (yearly invoice counter):
- anno (PK), last_progressivo

**Costo** (costs):
- id, descrizione, anno_riferimento, data_pagamento, totale, pagato

## Environment Variables

Critical environment variables in `.env`:
- `DATABASE_URL` - PostgreSQL connection for raw queries
- `DATABASE_SQLALCHEMY_URL` - PostgreSQL connection for SQLAlchemy
- `BACKEND_PORT` - Backend service port (default: 8000)
- `FRONTEND_EXTERNAL_PORT` - Frontend external port (default: 8080)
- `GOTENBERG_URL` - Gotenberg service URL for PDF conversion
- `SECRET_KEY` - Flask session secret

## Testing Strategy

Tests use bash scripts with curl to validate:
1. Health check endpoints
2. CRUD operations for clients, invoices, costs
3. PDF generation workflow
4. Data validation and error handling

Before running tests, the database is restored from `backups/backup.sql` to ensure consistent state.

## Important Notes

- Invoice numbers (`progressivo`) are auto-incremented per year via `FatturaProgressivo` model
- The backend waits for PostgreSQL readiness before starting (via `entrypoint.sh`)
- Frontend acts as a presentation layer and proxies all data operations to backend API
- All dates follow ISO format (YYYY-MM-DD) in API, displayed as DD/MM/YYYY in Italian format on frontend
- Invoice PDFs are stored in `invoices_data/` volume mounted to `/app/backend/invoices`
- Alembic migrations run automatically on backend container startup
