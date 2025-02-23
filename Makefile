-include .env
export


build:
	@docker-compose build

test:
	@pytest

format:
	@ruff format .

db.run:
	@docker compose up -d db

db.migrate:
	@yoyo apply -d $(GRPC_MOCK_DATABASE_URL)

db.clean:
	@docker compose down -t 1

dev.run:
	@python -m grpc_mock

local.run: db.run db.migrate
	@docker compose up -d api

local.stop:
	@docker compose down

run:
	@hypercorn grpc_mock.server:app -b $(GRPC_MOCK_HOST):$(GRPC_MOCK_PORT)
