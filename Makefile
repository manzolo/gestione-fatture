COMPOSE_FILE := docker-compose.yaml
DB_SERVICE := invoice_postgres_db
BACKUP_DIR := ./backups

include .env
export $(shell grep -v '^\s*#' .env | cut -d= -f1)

# Crea la directory dei backup se non esiste
$(shell mkdir -p $(BACKUP_DIR))

stop:
	docker compose -f $(COMPOSE_FILE) down
	docker compose -f $(COMPOSE_FILE) rm -f

restart:
	docker compose -f $(COMPOSE_FILE) down
	docker compose -f $(COMPOSE_FILE) rm -f
	docker compose -f $(COMPOSE_FILE) up -d
	docker compose -f $(COMPOSE_FILE) logs -f

start:
	docker compose -f $(COMPOSE_FILE) up -d

rebuild:
	docker compose -f $(COMPOSE_FILE) build

logs:
	docker compose -f $(COMPOSE_FILE) logs -f

backupdb:
	@echo "Creating PostgreSQL backup..."
	@docker compose -f $(COMPOSE_FILE) exec -T $(DB_SERVICE) \
		pg_dump -U $(POSTGRES_USER) $(POSTGRES_DB) > $(BACKUP_DIR)/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Backup created in $(BACKUP_DIR)"

restoredb:
	@if [ ! -f "$(BACKUP_DIR)/backup.sql" ]; then \
		echo "Errore: $(BACKUP_DIR)/backup.sql non trovato."; \
		exit 1; \
	fi
	@echo "Restoring PostgreSQL database from $(BACKUP_DIR)/backup.sql..."
	@docker compose -f $(COMPOSE_FILE) exec -T $(DB_SERVICE) \
		psql -U $(POSTGRES_USER) $(POSTGRES_DB) -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	@docker compose -f $(COMPOSE_FILE) exec -T $(DB_SERVICE) \
		psql -U $(POSTGRES_USER) $(POSTGRES_DB) < $(BACKUP_DIR)/backup.sql
	@echo "Database restored successfully"

list-backups:
	@echo "Available backups:"
	@ls -lh $(BACKUP_DIR)/*.sql

# Comando per entrare nel container del database
db-shell:
	docker compose -f $(COMPOSE_FILE) exec $(DB_SERVICE) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)