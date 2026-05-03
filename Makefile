.PHONY: help up down logs ps clean backend frontend backend-shell db-shell migrate revision test fmt lint

help:
	@echo "Spieon — common commands"
	@echo ""
	@echo "  make up             Bring up postgres + langfuse + backend"
	@echo "  make down           Stop all services"
	@echo "  make logs           Tail logs from all services"
	@echo "  make ps             Show service status"
	@echo "  make clean          Stop services and remove volumes (DESTROYS DATA)"
	@echo ""
	@echo "  make backend        Run backend dev server outside docker (uv run uvicorn)"
	@echo "  make frontend       Run frontend dev server (next dev)"
	@echo ""
	@echo "  make backend-shell  Shell inside backend container"
	@echo "  make db-shell       psql inside postgres container"
	@echo ""
	@echo "  make migrate        Apply alembic migrations"
	@echo "  make revision m=...  Generate a new alembic revision"
	@echo ""
	@echo "  make test           Run pytest"
	@echo "  make fmt            Run ruff format"
	@echo "  make lint           Run ruff check"

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

ps:
	docker compose ps

clean:
	docker compose down -v

backend:
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && rm -rf .next && pnpm dev

backend-shell:
	docker compose exec backend bash

db-shell:
	docker compose exec postgres psql -U $${POSTGRES_USER:-spieon} -d $${POSTGRES_DB:-spieon}

migrate:
	cd backend && uv run alembic upgrade head

revision:
	@if [ -z "$(m)" ]; then echo "Usage: make revision m='describe change'"; exit 1; fi
	cd backend && uv run alembic revision --autogenerate -m "$(m)"

test:
	cd backend && uv run pytest -q

fmt:
	cd backend && uv run ruff format .

lint:
	cd backend && uv run ruff check .
