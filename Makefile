# Configurazione
COMPOSE_FILE := docker-compose.yaml
DB_SERVICE := invoice_postgres_db
BACKUP_DIR := ./backups

# Docker Registry Configuration
DOCKER_USER := manzolo
BACKEND_IMAGE := $(DOCKER_USER)/invoice_backend
FRONTEND_IMAGE := $(DOCKER_USER)/invoice_frontend
DOCKER_TAG := latest

# Importa variabili d'ambiente
include .env
export $(shell grep -v '^\s*#' .env | cut -d= -f1)

# Crea la directory dei backup se non esiste
$(shell mkdir -p $(BACKUP_DIR))

# Colori per l'output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
CYAN := \033[0;36m
NC := \033[0m # No Color

# Default target: mostra l'help
.DEFAULT_GOAL := help

.PHONY: help
help: ## 📖 Mostra questo messaggio di aiuto
	@echo "$(BLUE)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║         📊 Gestionale Fatture - Comandi Disponibili       ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "}; /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)make %-18s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)💡 Esempi di utilizzo:$(NC)"
	@echo "  make start             - Avvia i container"
	@echo "  make test-all          - Esegue tutti i test"
	@echo "  make docker-push       - Publica le immagini su Docker Hub"
	@echo ""

# ============================================================================
# COMANDI DOCKER COMPOSE
# ============================================================================

.PHONY: start
start: ## 🚀 Avvia tutti i container in background
	@echo "$(GREEN)🚀 Avvio dei container...$(NC)"
	@docker compose -f $(COMPOSE_FILE) up -d
	@echo "$(GREEN)✅ Container avviati con successo!$(NC)"
	@echo "$(BLUE)📱 Frontend: http://localhost:$(FRONTEND_EXTERNAL_PORT)$(NC)"
	@echo "$(BLUE)🔧 Backend:  http://localhost:$(BACKEND_PORT)$(NC)"
	@echo "$(BLUE)🗄️  PgAdmin:  http://localhost:$(PGADMIN_HOST_PORT)$(NC)"

.PHONY: stop
stop: ## 🛑 Ferma e rimuove tutti i container
	@echo "$(YELLOW)🛑 Arresto dei container...$(NC)"
	@docker compose -f $(COMPOSE_FILE) down
	@docker compose -f $(COMPOSE_FILE) rm -f
	@echo "$(GREEN)✅ Container fermati e rimossi!$(NC)"

.PHONY: restart
restart: ## 🔄 Riavvia tutti i container e mostra i log
	@echo "$(YELLOW)🔄 Riavvio dei container...$(NC)"
	@docker compose -f $(COMPOSE_FILE) down
	@docker compose -f $(COMPOSE_FILE) rm -f
	@docker compose -f $(COMPOSE_FILE) up -d
	@echo "$(GREEN)✅ Container riavviati!$(NC)"
	@echo "$(BLUE)📋 Visualizzazione log (Ctrl+C per uscire)...$(NC)"
	@docker compose -f $(COMPOSE_FILE) logs -f

.PHONY: rebuild
rebuild: ## 🔨 Ricostruisce le immagini Docker
	@echo "$(YELLOW)🔨 Ricostruzione delle immagini...$(NC)"
	@docker compose -f $(COMPOSE_FILE) build
	@echo "$(GREEN)✅ Immagini ricostruite con successo!$(NC)"

.PHONY: rebuild-start
rebuild-start: ## 🔨🚀 Ricostruisce e riavvia tutti i container
	@echo "$(YELLOW)🔨 Ricostruzione e riavvio...$(NC)"
	@docker compose -f $(COMPOSE_FILE) down
	@docker compose -f $(COMPOSE_FILE) build
	@docker compose -f $(COMPOSE_FILE) up -d
	@echo "$(GREEN)✅ Container ricostruiti e avviati!$(NC)"

# ============================================================================
# COMANDI DOCKER REGISTRY
# ============================================================================

.PHONY: docker-login
docker-login: ## 🔐 Effettua il login a Docker Hub
	@echo "$(BLUE)🔐 Login a Docker Hub...$(NC)"
	@docker login

.PHONY: docker-tag
docker-tag: ## 🏷️  Tagga le immagini per Docker Hub
	@echo "$(BLUE)🏷️  Tagging delle immagini...$(NC)"
	@docker tag $(BACKEND_IMAGE):latest $(BACKEND_IMAGE):$(DOCKER_TAG)
	@docker tag $(FRONTEND_IMAGE):latest $(FRONTEND_IMAGE):$(DOCKER_TAG)
	@echo "$(GREEN)✅ Immagini taggate!$(NC)"

.PHONY: docker-push
docker-push: docker-tag ## 📤 Publica le immagini su Docker Hub
	@echo "$(YELLOW)📤 Push delle immagini su Docker Hub...$(NC)"
	@echo "$(CYAN)Pushing $(BACKEND_IMAGE):$(DOCKER_TAG)...$(NC)"
	@docker push $(BACKEND_IMAGE):$(DOCKER_TAG)
	@echo "$(CYAN)Pushing $(FRONTEND_IMAGE):$(DOCKER_TAG)...$(NC)"
	@docker push $(FRONTEND_IMAGE):$(DOCKER_TAG)
	@echo "$(GREEN)✅ Immagini pubblicate con successo!$(NC)"

.PHONY: docker-pull
docker-pull: ## 📥 Scarica le immagini da Docker Hub
	@echo "$(BLUE)📥 Download immagini da Docker Hub...$(NC)"
	@docker pull $(BACKEND_IMAGE):$(DOCKER_TAG)
	@docker pull $(FRONTEND_IMAGE):$(DOCKER_TAG)
	@echo "$(GREEN)✅ Immagini scaricate!$(NC)"

.PHONY: docker-build-push
docker-build-push: rebuild docker-push ## 🔨📤 Ricostruisce e pubblica le immagini
	@echo "$(GREEN)✅ Build e push completati!$(NC)"

# ============================================================================
# COMANDI LOG
# ============================================================================

.PHONY: logs
logs: ## 📋 Visualizza i log di tutti i container in tempo reale
	@echo "$(BLUE)📋 Log in tempo reale (Ctrl+C per uscire)...$(NC)"
	@docker compose -f $(COMPOSE_FILE) logs -f

.PHONY: logs-backend
logs-backend: ## 📋 Visualizza solo i log del backend
	@echo "$(BLUE)📋 Log del backend (Ctrl+C per uscire)...$(NC)"
	@docker compose -f $(COMPOSE_FILE) logs -f invoice_backend

.PHONY: logs-frontend
logs-frontend: ## 📋 Visualizza solo i log del frontend
	@echo "$(BLUE)📋 Log del frontend (Ctrl+C per uscire)...$(NC)"
	@docker compose -f $(COMPOSE_FILE) logs -f invoice_frontend

.PHONY: logs-db
logs-db: ## 📋 Visualizza solo i log del database
	@echo "$(BLUE)📋 Log del database (Ctrl+C per uscire)...$(NC)"
	@docker compose -f $(COMPOSE_FILE) logs -f $(DB_SERVICE)

.PHONY: status
status: ## 📊 Mostra lo stato di tutti i container
	@echo "$(BLUE)📊 Stato dei container:$(NC)"
	@docker compose -f $(COMPOSE_FILE) ps

# ============================================================================
# COMANDI DATABASE
# ============================================================================

.PHONY: backupdb
backupdb: ## 💾 Crea un backup del database PostgreSQL
	@echo "$(YELLOW)💾 Creazione backup del database...$(NC)"
	@docker compose -f $(COMPOSE_FILE) exec -T $(DB_SERVICE) \
		pg_dump -U $(POSTGRES_USER) $(POSTGRES_DB) > $(BACKUP_DIR)/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✅ Backup creato in $(BACKUP_DIR)$(NC)"

.PHONY: restoredb
restoredb: ## ♻️  Ripristina il database dal backup (backup.sql)
	@if [ ! -f "$(BACKUP_DIR)/backup.sql" ]; then \
		echo "$(RED)❌ Errore: $(BACKUP_DIR)/backup.sql non trovato.$(NC)"; \
		echo "$(YELLOW)💡 Usa 'make list-backups' per vedere i backup disponibili$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)♻️  Ripristino database da $(BACKUP_DIR)/backup.sql...$(NC)"
	@echo "$(RED)⚠️  ATTENZIONE: Questo cancellerà tutti i dati attuali!$(NC)"
	@printf "Sei sicuro? (y/N) "; \
	read -r REPLY; \
	case "$$REPLY" in \
		[Yy]*) \
			docker compose -f $(COMPOSE_FILE) exec -T $(DB_SERVICE) \
				psql -U $(POSTGRES_USER) $(POSTGRES_DB) -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"; \
			docker compose -f $(COMPOSE_FILE) exec -T $(DB_SERVICE) \
				psql -U $(POSTGRES_USER) $(POSTGRES_DB) < $(BACKUP_DIR)/backup.sql; \
			echo "$(GREEN)✅ Database ripristinato con successo!$(NC)"; \
			;; \
		*) \
			echo "$(YELLOW)❌ Ripristino annullato.$(NC)"; \
			;; \
	esac

.PHONY: list-backups
list-backups: ## 📂 Lista tutti i backup disponibili
	@echo "$(BLUE)📂 Backup disponibili in $(BACKUP_DIR):$(NC)"
	@if [ -d "$(BACKUP_DIR)" ] && [ "$$(ls -A $(BACKUP_DIR)/*.sql 2>/dev/null)" ]; then \
		ls -lht $(BACKUP_DIR)/*.sql | head -10; \
	else \
		echo "$(YELLOW)⚠️  Nessun backup trovato$(NC)"; \
	fi

.PHONY: db-shell
db-shell: ## 🗄️  Apre una shell PostgreSQL nel container del database
	@echo "$(BLUE)🗄️  Apertura shell PostgreSQL...$(NC)"
	@docker compose -f $(COMPOSE_FILE) exec $(DB_SERVICE) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

# ============================================================================
# COMANDI SHELL
# ============================================================================

.PHONY: shell-backend
shell-backend: ## 🐚 Apre una shell nel container del backend
	@echo "$(BLUE)🐚 Apertura shell backend...$(NC)"
	@docker compose -f $(COMPOSE_FILE) exec invoice_backend /bin/sh

.PHONY: shell-frontend
shell-frontend: ## 🐚 Apre una shell nel container del frontend
	@echo "$(BLUE)🐚 Apertura shell frontend...$(NC)"
	@docker compose -f $(COMPOSE_FILE) exec invoice_frontend /bin/sh

# ============================================================================
# COMANDI TEST
# ============================================================================

.PHONY: test-setup
test-setup: ## 🔧 Prepara l'ambiente per i test (ripristina DB)
	@echo "$(BLUE)🔧 Preparazione ambiente test...$(NC)"
	@if [ -f "$(BACKUP_DIR)/backup.sql" ]; then \
		docker compose -f $(COMPOSE_FILE) exec -T $(DB_SERVICE) \
			psql -U $(POSTGRES_USER) $(POSTGRES_DB) -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" 2>/dev/null || true; \
		docker compose -f $(COMPOSE_FILE) exec -T $(DB_SERVICE) \
			psql -U $(POSTGRES_USER) $(POSTGRES_DB) < $(BACKUP_DIR)/backup.sql 2>/dev/null || true; \
		echo "$(GREEN)✅ Database di test ripristinato$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  Nessun backup trovato, database vuoto$(NC)"; \
	fi
	@sleep 2

.PHONY: test-backend
test-backend: test-setup ## 🧪 Esegue i test del backend
	@echo "$(CYAN)╔════════════════════════════════════════╗$(NC)"
	@echo "$(CYAN)║     🧪 TEST BACKEND API                ║$(NC)"
	@echo "$(CYAN)╚════════════════════════════════════════╝$(NC)"
	@chmod +x ./tests/run_backend_tests.sh
	@./tests/run_backend_tests.sh

.PHONY: test-frontend
test-frontend: test-setup ## 🧪 Esegue i test del frontend
	@echo "$(CYAN)╔════════════════════════════════════════╗$(NC)"
	@echo "$(CYAN)║     🧪 TEST FRONTEND PROXY             ║$(NC)"
	@echo "$(CYAN)╚════════════════════════════════════════╝$(NC)"
	@chmod +x ./tests/run_frontend_tests.sh
	@./tests/run_frontend_tests.sh

.PHONY: test-sts
test-sts: ## 🧪 Esegue i test di integrazione STS
	@echo "$(CYAN)╔════════════════════════════════════════╗$(NC)"
	@echo "$(CYAN)║     🧪 TEST STS (Tessera Sanitaria)    ║$(NC)"
	@echo "$(CYAN)╚════════════════════════════════════════╝$(NC)"
	@chmod +x ./tests/run_sts_tests.sh
	@./tests/run_sts_tests.sh

.PHONY: test-all
test-all: ## 🧪 Esegue tutti i test (backend + frontend + sts)
	@echo "$(CYAN)╔════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(CYAN)║     🧪 ESECUZIONE COMPLETA TEST SUITE                 ║$(NC)"
	@echo "$(CYAN)╚════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@$(MAKE) test-backend
	@echo ""
	@$(MAKE) test-frontend
	@echo ""
	@$(MAKE) test-sts
	@echo ""
	@echo "$(GREEN)╔════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(GREEN)║     ✅ TUTTI I TEST COMPLETATI                         ║$(NC)"
	@echo "$(GREEN)╚════════════════════════════════════════════════════════╝$(NC)"

.PHONY: test-quick
test-quick: ## ⚡ Test rapidi senza setup del database
	@echo "$(YELLOW)⚡ Test rapidi (senza reset DB)...$(NC)"
	@chmod +x ./tests/run_backend_tests.sh ./run_frontend_tests.sh
	@./tests/run_backend_tests.sh && ./run_frontend_tests.sh

# ============================================================================
# COMANDI PULIZIA
# ============================================================================

.PHONY: clean
clean: ## 🧹 Rimuove container, volumi e immagini
	@echo "$(RED)⚠️  ATTENZIONE: Questo comando cancellerà tutti i dati!$(NC)"
	@printf "Sei sicuro di voler procedere? (y/N) "; \
	read -r REPLY; \
	case "$$REPLY" in \
		[Yy]*) \
			echo "$(YELLOW)🧹 Pulizia in corso...$(NC)"; \
			docker compose -f $(COMPOSE_FILE) down -v --rmi all; \
			echo "$(GREEN)✅ Pulizia completata!$(NC)"; \
			;; \
		*) \
			echo "$(YELLOW)❌ Pulizia annullata.$(NC)"; \
			;; \
	esac

.PHONY: prune
prune: ## 🗑️  Rimuove risorse Docker inutilizzate
	@echo "$(YELLOW)🗑️  Pulizia risorse Docker inutilizzate...$(NC)"
	@docker system prune -af --volumes
	@echo "$(GREEN)✅ Pulizia completata!$(NC)"

# ============================================================================
# COMANDI DIAGNOSTICA
# ============================================================================

.PHONY: check-env
check-env: ## ✅ Verifica le variabili d'ambiente
	@echo "$(BLUE)✅ Verifica configurazione...$(NC)"
	@echo "Database: $(POSTGRES_DB)"
	@echo "User: $(POSTGRES_USER)"
	@echo "Backend Port: $(BACKEND_PORT)"
	@echo "Frontend Port: $(FRONTEND_EXTERNAL_PORT)"
	@echo "PgAdmin Port: $(PGADMIN_HOST_PORT)"
	@echo "Docker Images:"
	@echo "  Backend:  $(BACKEND_IMAGE):$(DOCKER_TAG)"
	@echo "  Frontend: $(FRONTEND_IMAGE):$(DOCKER_TAG)"
	@echo "$(GREEN)✅ Configurazione OK!$(NC)"

.PHONY: health
health: ## 🏥 Verifica lo stato di salute dei servizi
	@echo "$(BLUE)🏥 Controllo stato servizi...$(NC)"
	@echo ""
	@echo "$(YELLOW)Backend:$(NC)"
	@curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost:$(BACKEND_PORT)/health || echo "$(RED)❌ Backend non raggiungibile$(NC)"
	@echo ""
	@echo "$(YELLOW)Frontend:$(NC)"
	@curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost:$(FRONTEND_EXTERNAL_PORT) || echo "$(RED)❌ Frontend non raggiungibile$(NC)"
	@echo ""
	@echo "$(YELLOW)Database:$(NC)"
	@docker compose -f $(COMPOSE_FILE) exec $(DB_SERVICE) pg_isready -U $(POSTGRES_USER) || echo "$(RED)❌ Database non pronto$(NC)"

# ============================================================================
# COMANDI VARI
# ============================================================================

.PHONY: update
update: ## 🔄 Aggiorna il repository e riavvia i container
	@echo "$(BLUE)🔄 Aggiornamento in corso...$(NC)"
	@git pull
	@docker compose -f $(COMPOSE_FILE) down
	@docker compose -f $(COMPOSE_FILE) build
	@docker compose -f $(COMPOSE_FILE) up -d
	@echo "$(GREEN)✅ Aggiornamento completato!$(NC)"

.PHONY: dev
dev: ## 🔧 Modalità sviluppo (rebuild + start + logs)
	@echo "$(CYAN)🔧 Avvio modalità sviluppo...$(NC)"
	@$(MAKE) rebuild-start
	@$(MAKE) logs