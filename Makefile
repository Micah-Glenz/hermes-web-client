.PHONY: up down restart build logs test shell-backend shell-web shell-gateway ps clean

SHELL := /bin/bash
VENV := venv/bin

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

build:
	docker compose build

rebuild:
	docker compose build --no-cache

logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

logs-web:
	docker compose logs -f web

logs-gateway:
	docker compose logs -f gateway

ps:
	docker compose ps

shell-backend:
	docker compose exec backend python manage.py shell

shell-web:
	docker compose exec web sh

shell-gateway:
	docker compose exec gateway sh

manage:
	docker compose exec backend python manage.py $(cmd)

migrate:
	docker compose exec backend python manage.py migrate

makemigrations:
	docker compose exec backend python manage.py makemigrations

clean:
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf web/dist

test-backend:
	cd backend && $(VENV)/python manage.py test

test-backend-pytest:
	cd backend && $(VENV)/pytest

test-web:
	cd web && npx vitest run

test-web-watch:
	cd web && npx vitest

test:
	make test-backend && make test-web

lint-web:
	cd web && npx eslint src --ext .vue,.js

lint-backend:
	cd backend && $(VENV)/ruff check

lint:
	make lint-web; make lint-backend

format-web:
	cd web && npx prettier --write src

format-backend:
	cd backend && $(VENV)/ruff format
