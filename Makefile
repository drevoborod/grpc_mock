-include .env
export


test:
	@pytest

format:
	@ruff format .

postgres-up:
	@docker compose -f docker-compose_postgres.yml up -d db

postgres-migrate:
	@yoyo apply -d $(GRPC_MOCK_DATABASE_URL)

postgres-down:
	@docker compose -f docker-compose_postgres.yml down -t 1

sqlite-down:
	@docker compose -f docker-compose_sqlite.yml down

dev.run:
	@python -m grpc_mock

run:
	@hypercorn grpc_mock.server:app -b $(GRPC_MOCK_HOST):$(GRPC_MOCK_PORT)

run-postgres: postgres-up
	@sleep 3
	-@$(MAKE) postgres-migrate
	-@docker compose -f docker-compose_postgres.yml up --build api
	-@$(MAKE) postgres-down

run-sqlite:
	-@docker compose -f docker-compose_sqlite.yml up --build
	-@$(MAKE) sqlite-down

